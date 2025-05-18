import os
import cv2
import numpy as np
import easyocr
from ultralytics import YOLO
import torch
from PIL import Image, ImageEnhance
import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from typing import List, Tuple
import re

class ParkingDetector:
    def __init__(self, confidence_threshold: float = 0.25):
        """Initialise le détecteur de plaques d'immatriculation.
        Args:
            confidence_threshold (float): Seuil de confiance pour la détection (0-1)
        """
        try:
            # Rechercher le modèle YOLOv8 dans différents emplacements
            possible_model_paths = [
                os.path.join(os.path.dirname(__file__), "weights", "weights", "best.pt"),
                os.path.join(os.path.dirname(__file__), "YOLOv8", "runs", "detect", "train10", "weights", "best.pt"),
                os.path.join(os.path.dirname(__file__), "YOLOv8", "YOLOv8", "model", "best.pt")
            ]
            
            # Trouver le modèle le plus récent
            latest_model = None
            latest_time = 0
            
            print("\n🔍 Recherche du modèle YOLOv8...")
            for path in possible_model_paths:
                if os.path.exists(path):
                    mod_time = os.path.getmtime(path)
                    print(f"  📁 Trouvé: {path}")
                    print(f"     └─ Dernière modification: {datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')}")
                    if mod_time > latest_time:
                        latest_time = mod_time
                        latest_model = path
            
            if latest_model is None:
                print("\n❌ ERREUR: Aucun modèle YOLOv8 trouvé!")
                print("ℹ️ Pour utiliser votre modèle entraîné sur Google Colab:")
                print("   1. Créez un dossier 'weights' dans le répertoire principal")
                print("   2. Copiez votre fichier 'best.pt' dans weights/weights/")
                print("   3. Assurez-vous d'avoir tous les fichiers de configuration")
                raise FileNotFoundError("Modèle YOLOv8 introuvable. Veuillez suivre les instructions ci-dessus.")
            
            self.model_path = latest_model
            print(f"\n✅ Utilisation du modèle le plus récent: {self.model_path}")
            
            # Configurer le device (GPU/CPU)
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"💻 Device: {self.device.upper()}")
            
            # Charger le modèle YOLOv8
            print("⌛ Chargement du modèle YOLOv8...")
            try:
                self.model = YOLO(self.model_path)
                # Tester le modèle avec une petite image
                test_img = np.zeros((100, 100, 3), dtype=np.uint8)
                self.model(test_img)
                print("✅ Modèle YOLOv8 chargé et testé avec succès!")
            except Exception as model_error:
                print(f"\n❌ ERREUR lors du chargement du modèle YOLOv8: {str(model_error)}")
                print("ℹ️ Vérifiez que:")
                print("   1. Le fichier best.pt est un modèle YOLOv8 valide")
                print("   2. Le modèle a été entraîné pour la détection d'objets")
                print("   3. Tous les fichiers nécessaires ont été copiés depuis Google Colab")
                raise
            
            # Initialiser EasyOCR
            print("\n⌛ Initialisation d'EasyOCR...")
            try:
                self.reader = easyocr.Reader(
                    ['ar', 'en'],
                    gpu=torch.cuda.is_available(),
                    model_storage_directory=os.path.join(os.path.dirname(__file__), 'models'),
                    download_enabled=True,
                    recog_network='standard'
                )
                print("✅ EasyOCR initialisé avec succès!")
            except Exception as ocr_error:
                print(f"\n❌ ERREUR lors de l'initialisation d'EasyOCR: {str(ocr_error)}")
                print("ℹ️ Vérifiez que:")
                print("   1. Vous avez une connexion internet stable")
                print("   2. Vous avez assez d'espace disque")
                print("   3. Les modèles EasyOCR ne sont pas corrompus")
                raise
            
            # Paramètres de détection
            self.confidence_threshold = confidence_threshold
            self.min_plate_ratio = 1.8  # Rapport largeur/hauteur minimal pour une plaque
            self.max_plate_ratio = 5.0  # Rapport largeur/hauteur maximal
            self.min_width = 800       # Largeur minimale de l'image
            self.max_width = 1920      # Largeur maximale de l'image
            
            # Expression régulière pour valider le format des plaques tunisiennes
            self.tunisian_plate_pattern = r'^\d{3,4}\d{3,4}$'
            
            print("\n✅ Initialisation terminée avec succès!")
            print(f"ℹ️ Configuration:")
            print(f"   🎯 Seuil de confiance: {self.confidence_threshold}")
            print(f"   📏 Ratio min/max plaque: {self.min_plate_ratio}/{self.max_plate_ratio}")
            print(f"   📷 Dimensions image: {self.min_width}-{self.max_width}px")
            
        except Exception as e:
            print(f"\n❗ ERREUR CRITIQUE: {str(e)}")
            raise
            
        def clean_text(self, text: str) -> str:
            """Nettoie le texte détecté.
            
            Args:
                text (str): Texte à nettoyer
                
            Returns:
                str: Texte nettoyé
            """
            # Supprimer tous les caractères non numériques
            cleaned = ''.join(c for c in text if c.isdigit())
            return cleaned
            
        def process_tunisian_plate(self, text: str) -> tuple[bool, str]:
            """Traite spécifiquement les plaques tunisiennes
            
            Args:
                text (str): Texte à traiter
                
            Returns:
                tuple[bool, str]: (True, numéro) si plaque valide, (False, "") sinon
            """
            # Nettoyer le texte pour ne garder que les chiffres
            cleaned_text = self.clean_text(text)
            
            # Vérifier si nous avons assez de chiffres
            if len(cleaned_text) < 7 or len(cleaned_text) > 8:
                return False, ""
                
            # Séparer en deux parties: 3 premiers chiffres et 4 derniers
            if len(cleaned_text) == 7:
                first_part = cleaned_text[:3]
                second_part = cleaned_text[3:]
            else:  # len == 8
                first_part = cleaned_text[:4]
                second_part = cleaned_text[4:]
            
            # Former le numéro de plaque au format tunisien
            formatted_plate = f"{first_part} تونس {second_part}"
            
            return True, formatted_plate

    def enhance_plate_region(self, img: np.ndarray) -> np.ndarray:
        try:
            # Convertir en niveaux de gris
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Améliorer le contraste global
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            lab = cv2.merge((l,a,b))
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Réduire le bruit avec un filtre bilatéral
            denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
            
            # Convertir en niveaux de gris après l'amélioration
            gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)
            
            # Améliorer les bords avec un filtre de Sobel
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edges = cv2.magnitude(sobelx, sobely)
            edges = cv2.normalize(edges, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            
            # Binarisation adaptative
            binary = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                15,
                5
            )
            
            # Combiner les résultats
            result = cv2.addWeighted(binary, 0.7, edges, 0.3, 0)
            
            # Nettoyer avec des opérations morphologiques
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            morph = cv2.morphologyEx(result, cv2.MORPH_CLOSE, kernel)
            
            return cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR)
            
        except Exception as e:
            print(f'Erreur lors de l\'amélioration de l\'image: {str(e)}')
            return img  # Retourner l'image originale en cas d'erreur
            print(f'Erreur lors de l\'amélioration de l\'image: {str(e)}')
            return img

    def resize_image(self, image: np.ndarray) -> np.ndarray:
        """Redimensionne l'image selon les dimensions minimales et maximales.
        
        Args:
            image (np.ndarray): Image à redimensionner
            
        Returns:
            np.ndarray: Image redimensionnée
        """
        try:
            height, width = image.shape[:2]
            
            if width < self.min_width:
                scale = self.min_width / width
                image = cv2.resize(image, None, fx=scale, fy=scale)
            elif width > self.max_width:
                scale = self.max_width / width
                image = cv2.resize(image, None, fx=scale, fy=scale)
                
            return image
            
        except Exception as e:
            print(f"Erreur lors du redimensionnement: {str(e)}")
            return image

    def remove_shadows(self, img: np.ndarray) -> np.ndarray:
        """Supprime les ombres de l'image"""
        rgb_planes = cv2.split(img)
        result_planes = []
        
        for plane in rgb_planes:
            dilated = cv2.dilate(plane, np.ones((7,7), np.uint8))
            bg_img = cv2.medianBlur(dilated, 21)
            diff_img = 255 - cv2.absdiff(plane, bg_img)
            result_planes.append(diff_img)
            
        return cv2.merge(result_planes)

    def correct_skew(self, img: np.ndarray) -> np.ndarray:
        """Corrige l'inclinaison de l'image"""
        try:
            # Convertir en niveaux de gris si nécessaire
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Détecter les contours
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
            
            if lines is not None:
                # Trouver l'angle dominant
                angles = []
                for rho, theta in lines[0]:
                    angle = theta * 180 / np.pi
                    if angle < 45:
                        angles.append(angle)
                    elif angle > 135:
                        angles.append(angle - 180)
                
                if angles:
                    median_angle = np.median(angles)
                    if abs(median_angle) > 0.5:  # Corriger seulement si l'angle est significatif
                        # Rotation de l'image
                        (h, w) = img.shape[:2]
                        center = (w // 2, h // 2)
                        M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                        return rotated
            
            return img
        except Exception as e:
            print(f'Erreur lors de la correction de l\'inclinaison: {str(e)}')
            return img
            
    def preprocess_plate(self, plate_region: np.ndarray) -> List[np.ndarray]:
        """Prétraite la région de la plaque avec différentes méthodes.
        
        Args:
            plate_region (np.ndarray): Région de l'image contenant la plaque
            
        Returns:
            List[np.ndarray]: Liste des versions prétraitées de l'image
        """
        try:
            # Version originale
            processed_regions = [plate_region]
            
            # Version sans ombres
            no_shadows = self.remove_shadows(plate_region)
            processed_regions.append(no_shadows)
            
            # Version améliorée
            enhanced = self.enhance_plate_region(plate_region)
            if enhanced is not None:
                processed_regions.append(enhanced)
            
            # Version redressée
            deskewed = self.correct_skew(enhanced if enhanced is not None else plate_region)
            if deskewed is not None:
                processed_regions.append(deskewed)
            
            # Version en niveaux de gris
            gray = cv2.cvtColor(plate_region, cv2.COLOR_BGR2GRAY)
            processed_regions.append(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
            
            # Version binarisée
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_regions.append(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR))
            
            return processed_regions
            
        except Exception as e:
            print(f"Erreur lors du prétraitement: {str(e)}")
            return [plate_region]  # Retourner l'image originale en cas d'erreur

    def process_tunisian_plate(self, text: str) -> Tuple[bool, str]:
        """Traite spécifiquement les plaques tunisiennes
        
        Args:
            text (str): Texte à traiter
            
        Returns:
            Tuple[bool, str]: (True, numéro) si plaque valide, (False, "") sinon
        """
        try:
            print(f"         └─ Analyse du texte: {text}")
            
            # Extraire tous les chiffres
            all_numbers = re.findall(r'\d+', text)
            if not all_numbers:
                print("         └─ ❌ Aucun chiffre trouvé")
                return False, ""
                
            # Vérifier la présence de texte arabe et sa position
            parts = text.split()
            arabic_pos = -1
            arabic_variations = ['تونس', 'تونن', 'تون']
            
            # Chercher les variations du mot "Tunisie" en arabe
            for i, part in enumerate(parts):
                for variation in arabic_variations:
                    if any(c in part for c in variation):
                        arabic_pos = i
                        break
                if arabic_pos != -1:
                    break
            
            if arabic_pos == -1:
                print("         └─ ❌ Position du texte arabe non trouvée")
                return False, ""
                return False, ""
            
            # Récupérer les nombres avec leur position et confiance
            number_candidates = []
            
            for i, part in enumerate(parts):
                numbers = re.findall(r'\d+', part)
                for num in numbers:
                    if 3 <= len(num) <= 4:  # Filtrer les nombres valides
                        position = 'before' if i < arabic_pos else 'after' if i > arabic_pos else 'middle'
                        if position != 'middle':
                            number_candidates.append({
                                'number': num,
                                'position': position,
                                'confidence': 1.0 if len(num) == 4 else 0.9  # Favoriser les nombres à 4 chiffres
                            })
            
            if not number_candidates:
                print("         └─ ❌ Aucun nombre valide trouvé")
                return False, ""
            
            # Séparer les nombres avant et après
            before_numbers = [c for c in number_candidates if c['position'] == 'before']
            after_numbers = [c for c in number_candidates if c['position'] == 'after']
            
            # Si nous n'avons pas de nombre avant mais deux nombres après,
            # considérer le premier comme étant avant
            if not before_numbers and len(after_numbers) >= 2:
                # Trier par position dans le texte
                after_numbers.sort(key=lambda x: parts.index(x['number']))
                before_numbers = [after_numbers.pop(0)]
            
            # Si nous n'avons toujours pas la bonne configuration
            if len(before_numbers) != 1 or len(after_numbers) != 1:
                print("         └─ ❌ Format invalide: il faut exactement un nombre avant et après تونس")
                return False, ""
            
            # Prendre les meilleurs candidats
            first_part = before_numbers[0]['number']
            second_part = after_numbers[0]['number']
            
            # Formater la plaque
            formatted_plate = f"{first_part} تونس {second_part}"
            print(f"         └─ ✅ Segmentation: {formatted_plate}")
            return True, formatted_plate
            
        except Exception as e:
            print(f"Erreur lors du traitement de la plaque tunisienne: {str(e)}")
            return False, ""

    def format_plate_number(self, first_part: str, second_part: str) -> str:
        """Formate le numéro de plaque avec le texte arabe au milieu.
        
        Args:
            first_part (str): Première partie du numéro (3 chiffres)
            second_part (str): Deuxième partie du numéro (4 chiffres)
            
        Returns:
            str: Numéro de plaque formaté
        """
        try:
            # Vérifier que les parties ont la bonne longueur
            if len(first_part) != 3 or len(second_part) != 4:
                print(f"         └─ ❌ Format invalide: {first_part} تونس {second_part}")
                return ""
            
            # Ne pas changer l'ordre des numéros, garder l'ordre original
            # La première partie doit être 3 chiffres, la deuxième 4 chiffres
            # Utiliser arabic_reshaper pour gérer correctement le texte arabe
            reshaped_text = arabic_reshaper.reshape('تونس')
            bidi_text = get_display(reshaped_text)
            return f"{first_part} {bidi_text} {second_part}"
        except Exception as e:
            print(f"Erreur lors du formatage de la plaque: {str(e)}")
            return f"{first_part} تونس {second_part}"
            
    def clean_text(self, text: str) -> str:
        """Nettoie le texte détecté.
        
        Args:
            text (str): Texte à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        try:
            # Supprimer les espaces et caractères spéciaux
            text = re.sub(r'[^0-9تونس]', '', text)
            
            # Convertir les chiffres arabes en chiffres latins si nécessaire
            arabic_to_latin = {
                '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
                '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
            }
            for ar, lat in arabic_to_latin.items():
                text = text.replace(ar, lat)
                
            return text
            
        except Exception as e:
            print(f"Erreur lors du nettoyage du texte: {str(e)}")
            return text  # Retourner le texte original en cas d'erreur

    def detect_and_read_plate(self, image_path: str):
        """Détecte et lit une plaque d'immatriculation dans l'image.

        Args:
            image_path (str): Chemin vers l'image à analyser

        Returns:
            str: Numéro de plaque détecté ou None si aucune plaque n'est trouvée
        """
        try:
            print(f"\n🔍 Analyse de l'image: {image_path}")
            
            # Lire l'image
            print("\n⌛ Lecture de l'image...")
            img = cv2.imread(image_path)
            if img is None:
                print(f"\n❌ Impossible de lire l'image: {image_path}")
                print("ℹ️ Vérifiez que:")
                print("   1. Le chemin de l'image est correct")
                print("   2. L'image existe et est accessible")
                print("   3. L'image est dans un format supporté (JPG, PNG)")
                return None
                
            h, w = img.shape[:2]
            print(f"✅ Image chargée avec succès ({w}x{h} pixels)")
            
            # Redimensionner l'image si nécessaire
            img = self.resize_image(img)
            
            # Améliorer la qualité de l'image
            img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)  # Réduction du bruit
            
            # Détecter les plaques avec YOLOv8
            print("\n🔍 Détection des plaques avec YOLOv8...")
            try:
                results = self.model(img, conf=0.3)[0]  # Réduire le seuil de confiance
                
                if len(results.boxes) == 0:
                    print("❌ Aucune plaque détectée par YOLOv8")
                    return None
                    
                print(f"✅ {len(results.boxes)} plaque(s) détectée(s)")
                
            except Exception as model_error:
                print(f"❌ Erreur lors de la détection YOLOv8: {str(model_error)}")
                print("ℹ️ Vérifiez que:")
                print("   1. Le modèle est correctement chargé et compatible")
                print("   2. Vous avez les bonnes dépendances installées")
                return None
                
            best_text = None
            highest_conf = 0
            
            # Variables pour stocker les meilleurs résultats partiels
            best_first_part = None
            best_second_part = None
            best_first_conf = 0
            best_second_conf = 0
            
            # Traiter chaque détection
            print("\n🔍 Analyse des plaques détectées...")
            for i, result in enumerate(results.boxes.data):
                x1, y1, x2, y2, conf, _ = result
                print(f"\n📌 Plaque #{i+1}:")
                print(f"   └─ Confiance: {conf:.2f}")
                
                if conf < self.confidence_threshold:
                    print(f"   └─ ❌ Confiance trop faible (< {self.confidence_threshold})")
                    continue
                    
                print("   └─ ✅ Confiance suffisante")
                
                # Extraire la région de la plaque avec une marge
                print("   └─ Extraction de la région...")
                margin = 5
                y1, y2 = max(0, int(y1)-margin), min(img.shape[0], int(y2)+margin)
                x1, x2 = max(0, int(x1)-margin), min(img.shape[1], int(x2)+margin)
                plate_region = img[y1:y2, x1:x2]
                h, w = plate_region.shape[:2]
                print(f"   └─ Dimensions: {w}x{h} pixels")
                
                # Vérifier les dimensions
                if w < 100 or h < 30:  # Ignorer les régions trop petites
                    print(f"   └─ ❌ Région trop petite ({w}x{h} < 100x30)")
                    continue
                    
                print("   └─ ✅ Dimensions suffisantes")
                    
                ratio = w / h
                print(f"   └─ Ratio largeur/hauteur: {ratio:.2f}")
                
                if not (self.min_plate_ratio <= ratio <= self.max_plate_ratio):
                    print(f"   └─ ❌ Ratio invalide (doit être entre {self.min_plate_ratio} et {self.max_plate_ratio})")
                    continue
                    
                print("   └─ ✅ Ratio valide")
                
                # Prétraiter la région de la plaque
                print("   └─ Prétraitement de l'image...")
                processed_regions = self.preprocess_plate(plate_region)
                print(f"   └─ {len(processed_regions)} versions prétraitées générées")
                
                # Essayer l'OCR sur chaque version prétraitée
                print("   └─ Tentative de lecture OCR...")
                for i, processed_plate in enumerate(processed_regions):
                    print(f"      └─ Version #{i+1}:")
                    try:
                        # Configuration optimisée pour les plaques tunisiennes
                        ocr_results = self.reader.readtext(
                            processed_plate,
                            allowlist='0123456789تونس ',
                            detail=1,
                            text_threshold=0.5,
                            link_threshold=0.4,
                            low_text=0.4
                        )
                        
                        if not ocr_results:
                            print("         └─ ❌ Aucun texte détecté")
                            continue
                            
                        print(f"         └─ ✅ {len(ocr_results)} texte(s) détecté(s)")
                        
                        # Traiter chaque résultat OCR
                        for text_result in ocr_results:
                            try:
                                text = text_result[1]
                                conf = text_result[2]
                                print(f"         └─ Texte détecté: {text} (confiance: {conf:.2f})")
                                
                                # Nettoyer le texte
                                cleaned_text = self.clean_text(text)
                                print(f"         └─ Texte nettoyé: {cleaned_text}")
                                print(f"         └─ Analyse du texte: {cleaned_text}")
                                
                                # Vérifier la présence du texte arabe 'تونس'
                                has_tun = 'تونس' in text
                                if has_tun:
                                    print("         └─ ✅ Texte arabe 'TUN' trouvé")
                                else:
                                    print("         └─ ❌ Texte arabe 'TUN' non trouvé")
                                
                                # Analyser les chiffres dans le texte
                                numbers = ''.join(c for c in text if c.isdigit())
                                
                                # Si le texte contient تونس ou تون, traiter comme un format complet
                                if has_tun:
                                    # Normaliser le texte arabe
                                    text = text.replace('تون', 'تونس')
                                    
                                    # Extraire les nombres avant et après تونس
                                    parts = text.split('تونس')
                                    if len(parts) == 2:
                                        # Extraire les chiffres de chaque partie
                                        first_digits = ''.join(c for c in parts[0] if c.isdigit())
                                        second_digits = ''.join(c for c in parts[1] if c.isdigit())
                                        
                                        # Vérifier et formater la première partie (3 chiffres)
                                        if len(first_digits) == 3:
                                            first_part = first_digits
                                        else:
                                            continue
                                            
                                        # Vérifier et formater la deuxième partie (4 chiffres)
                                        if len(second_digits) == 4:
                                            second_part = second_digits
                                        else:
                                            continue
                                        
                                        # Vérifier si les deux parties sont valides
                                        if first_part and second_part:
                                            if len(first_part) == 3 and len(second_part) == 4:
                                                # Formater la plaque avec le texte arabe
                                                formatted_plate = f"{first_part} تونس {second_part}"
                                                print(f"         └─ ✅ Format avec TUN détecté: {formatted_plate}")
                                                if conf > highest_conf:
                                                    best_text = formatted_plate
                                                    highest_conf = conf
                                                    print(f"         └─ ✅ Nouveau meilleur résultat complet: {best_text} (confiance: {conf:.2f})")
                                # Si pas de texte arabe mais assez de chiffres pour une plaque
                                elif len(numbers) >= 7:
                                    # Extraire les chiffres
                                    digits = ''.join(c for c in text if c.isdigit())
                                    if len(digits) >= 7:
                                        # Chercher un pattern valide (3+4 chiffres)
                                        match = re.search(r'(\d{3})(\d{4})', digits)
                                        if match:
                                            first_part = match.group(1)
                                            second_part = match.group(2)
                                        
                                        # Vérifier que les parties sont valides
                                        if len(first_part) == 3 and len(second_part) == 4:
                                            formatted_plate = f"{first_part} تونس {second_part}"
                                            print(f"         └─ ✅ Format sans TUN détecté: {formatted_plate}")
                                            if conf > highest_conf:
                                                best_text = formatted_plate
                                                highest_conf = conf
                                                print(f"         └─ ✅ Nouveau meilleur résultat: {best_text} (confiance: {conf:.2f})")
                                
                                # Sinon, essayer de détecter les parties individuelles
                                elif len(numbers) >= 3:
                                    # Vérifier si c'est une première partie (exactement 3 chiffres)
                                    if len(numbers) == 3:
                                        if conf > best_first_conf:
                                            best_first_part = numbers
                                            best_first_conf = conf
                                            print(f"         └─ ✅ Première partie trouvée: {numbers} (confiance: {conf:.2f})")
                                    
                                    # Vérifier si c'est une deuxième partie (exactement 4 chiffres)
                                    elif len(numbers) == 4:
                                        if conf > best_second_conf:
                                            best_second_part = numbers
                                            best_second_conf = conf
                                            print(f"         └─ ✅ Deuxième partie trouvée: {numbers} (confiance: {conf:.2f})")
                            except Exception as detail_error:
                                print(f"         └─ ❌ Erreur lors du traitement: {str(detail_error)}")
                                continue
                    except Exception as ocr_error:
                        print(f"         └─ ❌ Erreur OCR: {str(ocr_error)}")
                        continue
                
                # Après avoir traité toutes les versions prétraitées, essayer de combiner les parties
                if best_first_part and best_second_part:
                    # Formater la plaque de manière consistante avec le texte arabe dans le bon sens
                    formatted_plate = self.format_plate_number(best_first_part, best_second_part)
                    combined_conf = (best_first_conf + best_second_conf) / 2
                    if combined_conf > highest_conf:
                        best_text = formatted_plate
                        highest_conf = combined_conf
                        print(f"\n✅ Plaque complète reconstruite: {best_text}")
                        print(f"   └─ Première partie: {best_first_part} (confiance: {best_first_conf:.2f})")
                        print(f"   └─ Deuxième partie: {best_second_part} (confiance: {best_second_conf:.2f})")
                        print(f"   └─ Confiance moyenne: {combined_conf:.2f}")
                
                # Si nous avons un résultat, l'enregistrer
                if best_text:
                    try:
                        output_dir = os.path.join(os.path.dirname(image_path), "detected")
                        os.makedirs(output_dir, exist_ok=True)
                        output_path = os.path.join(output_dir, f"detected_{os.path.basename(image_path)}")
                        
                        # Dessiner les détections sur l'image
                        for result in results.boxes.data:
                            x1, y1, x2, y2, conf, _ = result
                            if conf > self.confidence_threshold:
                                cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                                
                        cv2.imwrite(output_path, img)
                        print(f"\n✅ Plaque détectée: {best_text} (confiance: {highest_conf:.2f})")
                        print(f"   └─ Image sauvegardée: {output_path}")
                    except Exception as e:
                        print(f"   └─ ❌ Erreur lors de la sauvegarde de l'image: {str(e)}")
                else:
                    print("\n❌ Aucune plaque valide détectée")
                    
                return best_text
            
            print("❌ Aucune plaque valide détectée")
            return None

        except Exception as e:
            print(f"❌ Erreur dans detect_and_read_plate: {str(e)}")
            return None

def test_model():
    """Test le modèle YOLOv8 et affiche des informations détaillées."""
    print("\n🔍 Test du système de détection de plaques...")
    
    try:
        # Initialiser le détecteur
        detector = ParkingDetector()
        print("\n✅ Initialisation réussie!")
        
        # Afficher les informations sur le modèle
        print("\nℹ️ Informations sur le modèle:")
        print(f"   📁 Chemin du modèle: {detector.model_path}")
        print(f"   💻 Device: {detector.device}")
        print(f"   🎯 Seuil de confiance: {detector.confidence_threshold}")
        
        # Vérifier si une image de test existe
        test_image = os.path.join(os.path.dirname(__file__), "test_image.jpg")
        
        if os.path.exists(test_image):
            print("\n📷 Test avec l'image: test_image.jpg")
            plate_number = detector.detect_and_read_plate(test_image)
            
            if plate_number:
                print("\n✅ Test réussi!")
                print(f"   📍 Plaque détectée: {plate_number}")
            else:
                print("\n⚠️ Test échoué")
                print("   ℹ️ Vérifiez que:")
                print("      1. L'image contient une plaque d'immatriculation claire")
                print("      2. La plaque est bien visible et lisible")
                print("      3. L'image est de bonne qualité")
        else:
            print("\n⚠️ Aucune image de test trouvée")
            print("💡 Pour tester le modèle:")
            print("   1. Ajoutez une image nommée 'test_image.jpg' dans le dossier du projet")
            print("   2. L'image doit contenir une plaque d'immatriculation claire")
            
    except Exception as e:
        print(f"\n❌ ERREUR lors du test: {str(e)}")

        
        # Chercher une image de test
        test_images = ["test_image.jpg", "test.jpg", "sample.jpg"]
        test_image = None
        
        for img in test_images:
            if os.path.exists(img):
                test_image = img
                break
        
        if test_image:
            print(f"\n🖼️ Test avec l'image: {test_image}")
            result = detector.detect_and_read_plate(test_image)
            if result:
                print(f"\n✅ Test réussi!")
                print(f"   📝 Plaque détectée: {result}")
            else:
                print(f"\n⚠️ Aucune plaque détectée dans l'image de test")
                print("   💡 Suggestions:")
                print("      1. Vérifiez que l'image contient une plaque claire")
                print("      2. Ajustez le seuil de confiance si nécessaire")
                print("      3. Vérifiez que le modèle a été entraîné sur des images similaires")
        else:
            print("\n⚠️ Aucune image de test trouvée")
            print("💡 Pour tester le modèle:")
            print("   1. Ajoutez une image nommée 'test_image.jpg' dans le dossier du projet")
            print("   2. L'image doit contenir une plaque d'immatriculation claire")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors du test: {str(e)}")
        print("\nℹ️ Vérifiez que:")
        print("   1. Le modèle YOLOv8 est correctement installé")
        print("   2. Le fichier best.pt est un modèle valide")
        print("   3. Vous avez les bonnes dépendances installées")
        raise

def main():
    """Fonction principale"""
    test_model()

if __name__ == '__main__':
    main()
