from datetime import datetime
import os
import cv2
from ultralytics import YOLO
import easyocr
import numpy as np
import re
import time
from PIL import Image
import mysql.connector
import sys
from admin.init_db import init_db
import time  


# Obtenir le chemin absolu du répertoire du script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from admin.config import DATABASE_CONFIG

# Compatibility fix for PIL ANTIALIAS deprecation
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# Définir le chemin du dossier images
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'admin', 'images')
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# Initialisation de la base de données
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        if conn.is_connected():
            return conn
        else:
            print("Erreur : Impossible de se connecter à la base de données")
            return None
    except mysql.connector.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")
        return None

def call_init_db():
    conn = get_db_connection()
    if not conn:
        print("Erreur : Connexion à la base de données échouée")
        return

    cursor = conn.cursor()
    try:
        init_db()  # Appeler la fonction pour initialiser la base de données
        conn.commit()
        print("Base de données initialisée avec succès à partir du fichier init_db.sql!")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

class PlateDetector:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        self.reader = easyocr.Reader(['ar', 'en'])
        
    def preprocess_image(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        kernel = np.ones((3,3), np.uint8)
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        return morph, enhanced

    def find_plate_regions(self, binary_img, original_img):
        contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions = []
        img_h, img_w = original_img.shape[:2]
        
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(h)
            area = w * h
            area_ratio = area / (img_w * img_h)
            
            if (2.0 <= aspect_ratio <= 5.0 and 
                0.01 <= area_ratio <= 0.15 and
                w > 60 and h > 20):
                regions.append((x, y, w, h))
        
        return regions

    def clean_text(self, text):
        print(f"Texte brut avant nettoyage : '{text}'")
        text = re.sub(r'[^\d\s\u062a\u0648\u0646\u0633]', '', text)
        text = text.replace('تونن', 'تونس')
        text = ' '.join(text.split())
        print(f"Texte après nettoyage : '{text}'")
        return text.strip()

    def validate_plate(self, text):
        if not text or len(text) < 5:  # Vérifier si le texte est trop court pour être une plaque valide
            print(f"Validation échouée : Texte trop court ({text})")
            return False

        # Remplacer tout mot en arabe par 'تونس'
        arabic_word_pattern = re.compile(r'[\u0600-\u06FF]+')  # Correspond à tout mot en arabe
        text = arabic_word_pattern.sub('تونس', text)

        # Vérifier si le texte contient 'تونس'
        if 'تونس' not in text:
            print(f"Validation échouée : 'تونس' non trouvé dans ({text})")
            return False

        # Diviser le texte en deux parties autour de 'تونس'
        parts = text.split('تونس')
        if len(parts) != 2:
            print(f"Validation échouée : Texte mal formé autour de 'تونس' ({text})")
            return False

        # Extraire les chiffres avant et après 'تونس'
        print(f"Partie avant 'تونس' brute : {parts[0]}")
        before_numbers = ''.join(filter(str.isdigit, parts[0]))
        print(f"Chiffres extraits avant 'تونس' : {before_numbers}")

        print(f"Partie après 'تونس' brute : {parts[1]}")
        after_numbers = ''.join(filter(str.isdigit, parts[1]))
        print(f"Chiffres extraits après 'تونس' : {after_numbers}")


        # Vérifier les longueurs des parties numériques
        if not (1 <= len(before_numbers) <= 4):  # La première partie doit contenir entre 1 et 3 chiffres
            print(f"Validation échouée : Partie avant 'تونس' invalide ({before_numbers})")
            return False
        if not (1 <= len(after_numbers) <= 3):  # La deuxième partie doit contenir entre 1 et 4 chiffres
            print(f"Validation échouée : Partie après 'تونس' invalide ({after_numbers})")
            return False

        return True

    def detect_plate(self, image_path):
        print(f"\n=== Détection de plaque démarrée ===")
        print(f"Analyse de l'image : {image_path}")
        
        # Utiliser le chemin complet pour l'image
        full_image_path = os.path.join(IMAGES_DIR, os.path.basename(image_path))
        print(f"Chemin complet de l'image : {full_image_path}")
        
        # Vérifier si le fichier existe
        if not os.path.exists(full_image_path):
            print(f"ERREUR: Le fichier {full_image_path} n'existe pas!")
            return None
            
        image = cv2.imread(full_image_path)
        if image is None:
            print(f"ERREUR: Impossible de charger l'image: {full_image_path}")
            return None
            
        print(f"Taille de l'image chargée: {image.shape}")
        
        try:
            binary, enhanced = self.preprocess_image(image)
            print("Prétraitement de l'image terminé")
            
            regions = self.find_plate_regions(binary, image)
            print(f"Nombre de régions détectées: {len(regions)}")
            
            best_text = None
            highest_conf = 0
            best_box = None
            
            for i, (x, y, w, h) in enumerate(regions):
                print(f"\nTraitement de la région {i+1} à la position (x={x}, y={y}, w={w}, h={h})")
                
                margin = 5
                x1 = max(0, x - margin)
                y1 = max(0, y - margin)
                x2 = min(image.shape[1], x + w + margin)
                y2 = min(image.shape[0], y + h + margin)
                
                roi = enhanced[y1:y2, x1:x2]
                
                if roi.size == 0:
                    print(f"  ROI vide pour la région {i+1}, passage à la suivante...")
                    continue
                
                # Sauvegarder la ROI pour le débogage
                roi_filename = f'roi_{i}.jpg'
                cv2.imwrite(roi_filename, roi)
                print(f"  ROI sauvegardée dans {roi_filename}")
                
                # Utiliser EasyOCR pour lire le texte
                print("  Lecture du texte avec EasyOCR...")
                results = self.reader.readtext(roi, detail=1, paragraph=False)
                print(f"  Résultats EasyOCR bruts: {results}")
                
                for (bbox, text, conf) in results:
                    print(f"Texte brut détecté : '{text}', Confiance : {conf:.2f}")
                    cleaned_text = self.clean_text(text)
                    print(f"  Texte détecté: '{text}' (nettoyé: '{cleaned_text}'), confiance: {conf:.2f}")
                    
                    if conf > highest_conf and self.validate_plate(cleaned_text):
                        best_text = cleaned_text
                        highest_conf = conf
                        best_box = (x1, y1, x2, y2)
                        print(f"  Nouvelle meilleure détection: '{best_text}' avec une confiance de {highest_conf:.2f}")
            
            if best_text and best_box:
                x1, y1, x2, y2 = best_box
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(image, best_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                cv2.imwrite('detection_finale.jpg', image)
                print(f"\nDétection finale: '{best_text}' avec une confiance de {highest_conf:.2f}")
                print("Image de détection sauvegardée dans 'detection_finale.jpg'")
            else:
                print("Aucune plaque valide détectée dans l'image")
            
            print("=== Détection de plaque terminée ===\n")
            return best_text
            
        except Exception as e:
            print(f"ERREUR lors de la détection de plaque: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


class ParkingManager:
    def load_places_from_db(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM places")  # Ajout de `cursor.`
            places = cursor.fetchall()
            return places
        except Exception as e:
            print(f"Erreur lors du chargement des places : {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals() and conn.is_connected():
                conn.close()
    def __init__(self):
        self.places = self.load_places_from_db()
    
    def update_place_status(self, numero, occupied):
        """
        Met à jour le statut d'une place de parking dans la base de données.
        :param numero: Numéro de la place (int)
        :param occupied: 1 si occupée, 0 si libre (int)
        """
        try:
            #Retirer le préfixe "P" si présent
            if isinstance(numero, str) and numero.startswith("P"):
                numero = int(numero[1:])


            print(f"Mise à jour du statut de la place {numero} à {'occupé' if occupied else 'libre'}...")
            conn = get_db_connection()
            if not conn:
                print("Erreur : Connexion à la base de données échouée")
                return False

            cursor = conn.cursor()
            query = """
                UPDATE places
                SET occupied = %s, last_update = NOW()
                WHERE numero = %s
            """
            cursor.execute(query, (occupied, numero))
            conn.commit()
            print(f"Statut de la place {numero} mis à jour avec succès.")
            return True
        except Exception as e:
            print(f"Erreur lors de la mise à jour du statut de la place : {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

def generer_dashboard_sortie(plaque, place, temps_entree, temps_sortie, duree_minutes, montant):
    try:
        print("Début de la génération du dashboard de sortie...")
        html_path = os.path.join(SCRIPT_DIR, 'dashboard_sortie.html')
        if not os.path.exists(html_path):
            print(f"Erreur : Le fichier {html_path} n'existe pas.")
            return

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        html_content = html_content.replace('{plaque}', str(plaque))
        html_content = html_content.replace('{place}', str(place))
        html_content = html_content.replace('{temps_entree}', temps_entree.strftime('%d/%m/%Y %H:%M:%S'))
        html_content = html_content.replace('{temps_sortie}', temps_sortie.strftime('%d/%m/%Y %H:%M:%S'))
        html_content = html_content.replace('{duree_minutes}', f"{duree_minutes:.1f}")
        html_content = html_content.replace('{montant}', f"{montant:.2f}")

        temp_html_path = os.path.join(SCRIPT_DIR, 'dashboard_sortie_temp.html')
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        os.startfile(temp_html_path)
        print(f"Dashboard de sortie affiché avec succès depuis {temp_html_path}")
    except Exception as e:
        print(f"Erreur lors de l'affichage du dashboard de sortie : {e}")

     

def enregistrer_sortie(vehicule_id, plaque, place, temps_entree):
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()

        # Calculer le temps de sortie
        temps_sortie = datetime.now()

        # Calculer la durée de stationnement en minutes
        duree_minutes = (temps_sortie - temps_entree).total_seconds() / 60

        # Calculer le montant à payer
        if duree_minutes <= 1:
            montant = 0  # Gratuit pour 1 minute ou moins
            direction = "A"  # Voie de sortie gratuite
        else:
            minutes_payantes = int(duree_minutes - 1)  # Soustraire la première minute gratuite
            montant = minutes_payantes * 2  # 2 DT par minute
            direction = "B"  # Voie de sortie payante

        # Enregistrer dans l'historique
        cursor.execute('''
        INSERT INTO historique_stationnement 
        (plaque, place, temps_entree, temps_sortie, duree_minutes, montant, direction, status_paiement)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (plaque, place, temps_entree, temps_sortie, duree_minutes, montant, direction, 'en_attente'))
        print(f"Enregistrement dans l'historique réussi pour le véhicule {plaque}.")

        # Mettre à jour le statut dans vehicules_en_stationnement
        cursor.execute('''
        UPDATE vehicules_en_stationnement
        SET temps_sortie = %s, status = 'en_attente_paiement'
        WHERE id = %s
        ''', (temps_sortie, vehicule_id))
        print(f"Table vehicules_en_stationnement mise à jour pour le véhicule ID {vehicule_id}.")

        # Valider les modifications
        conn.commit()

        return duree_minutes, montant

    except mysql.connector.Error as e:
        print(f"Erreur lors de l'enregistrement de la sortie : {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()
    


def surveiller_sorties():
    print("=== Système de surveillance des sorties ===")
    print("Traitement direct d'une sortie...")
    try:
        # Appeler la fonction pour traiter une sortie
        traiter_sortie()
    except Exception as e:
        print(f"Erreur lors du traitement de la sortie : {str(e)}")

def traiter_sortie():
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Rechercher le dernier véhicule en stationnement
        cursor.execute('''
        SELECT id, plaque, place, temps_entree 
        FROM vehicules_en_stationnement 
        WHERE status = 'en_stationnement'
        ORDER BY temps_entree DESC
        LIMIT 1
        ''')

        vehicule = cursor.fetchone()

        if vehicule:
            vehicule_id = vehicule['id']
            plaque = vehicule['plaque']
            place = vehicule['place']
            temps_entree = vehicule['temps_entree']

            print(f"\nTraitement de la sortie pour le véhicule : {plaque}")
            print(f"Place : {place}, Heure d'entrée : {temps_entree}")

            # Vérifiez si `temps_entree` est déjà un objet datetime
            if isinstance(temps_entree, str):
                temps_entree = datetime.strptime(temps_entree, '%Y-%m-%d %H:%M:%S')

            # Enregistrer la sortie
            duree_minutes, montant = enregistrer_sortie(
                vehicule_id, plaque, place, temps_entree
            )

            # Libérer la place
            parking_manager = ParkingManager()
            libre = parking_manager.update_place_status(place, 0)
            print("libre,", libre)
            if libre:
                print(f"La place {place} a été libérée avec succès.")
            else:
                print(f"Échec de la libération de la place {place}.")

            # Générer le tableau de bord de sortie
            temps_sortie = datetime.now()
            generer_dashboard_sortie(plaque, place, temps_entree, temps_sortie, duree_minutes, montant)


            print(f"\nSortie enregistrée :")
            print(f"Durée : {duree_minutes:.1f} minutes, Montant : {montant:.2f} DT")
        else:
            print("\nAucun véhicule en stationnement trouvé.")

    except mysql.connector.Error as e:
        print(f"Erreur lors de la connexion ou de l'exécution SQL : {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    call_init_db()  # Initialiser la base de données
    surveiller_sorties()
