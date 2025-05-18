import cv2
from ultralytics import YOLO
import easyocr
import re
import mysql.connector
from datetime import datetime
import os
import platform
import subprocess
import numpy as np

# === UTILITY: Open dashboard cross-platform ===
def ouvrir_dashboard(filepath):
    try:
        full_path = os.path.abspath(filepath)
        if platform.system() == "Windows":
            os.startfile(full_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", full_path])
        else:  # Linux
            subprocess.run(["xdg-open", full_path])
        print(f">>> Dashboard ouvert : {filepath}")
    except Exception as e:
        print(f">>> Erreur lors de l'ouverture du dashboard : {e}")

# === HTML DASHBOARD GENERATORS ===
def generer_dashboard_entree(plate, place, date_entree):
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Entrée</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                zoom: 0.65;
                -moz-transform: scale(0.65);
                transform-origin: top center;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}
            .container {{
                max-width: 600px;
                padding: 10px;
                margin: 0 auto;
            }}
            .display-5 {{
                font-size: 1.8rem;
                margin-bottom: 0.3rem;
            }}
            h2 {{
                font-size: 1.2rem;
                margin-bottom: 0.5rem;
            }}
            .card {{
                margin-top: 10px;
                border-radius: 8px;
            }}
            .card-body {{
                padding: 0.8rem;
            }}
            .card-title {{
                font-size: 1rem;
                margin-bottom: 0.5rem;
            }}
            .card-text {{
                font-size: 0.9rem;
                margin-bottom: 0.3rem;
                line-height: 1.2;
            }}
            .py-3 {{
                padding-top: 0.5rem !important;
                padding-bottom: 0.5rem !important;
            }}
            .mb-3 {{
                margin-bottom: 0.5rem !important;
            }}
        </style>
    </head>
    <body class="bg-light">
        <div class="container py-3">
            <div class="text-center mb-2">
                <h1 class="display-5">🛬 Aéroport Tunis-Carthage</h1>
                <h2 class="text-success">Bienvenue !</h2>
            </div>
            <div class="card shadow">
                <div class="card-body">
                    <h4 class="card-title">🆕 Véhicule enregistré</h4>
                    <p class="card-text"><strong>Matricule :</strong> {plate}</p>
                    <p class="card-text"><strong>Place assignée :</strong> {place}</p>
                    <p class="card-text"><strong>Date d'entrée :</strong> {date_entree}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    with open("dashboard_entree.html", "w", encoding="utf-8") as f:
        f.write(html)
    ouvrir_dashboard("dashboard_entree.html")

def generer_dashboard_sortie(plate, duree, montant):
    voie = "A" if montant == 0 else "B"
    statut = "Gratuit" if montant == 0 else f"{montant} DT"
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Sortie</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                zoom: 0.65;
                -moz-transform: scale(0.65);
                transform-origin: top center;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}
            .container {{
                max-width: 600px;
                padding: 10px;
                margin: 0 auto;
            }}
            .display-5 {{
                font-size: 1.8rem;
                margin-bottom: 0.3rem;
            }}
            h2 {{
                font-size: 1.2rem;
                margin-bottom: 0.5rem;
            }}
            .card {{
                margin-top: 10px;
                border-radius: 8px;
            }}
            .card-body {{
                padding: 0.8rem;
            }}
            .card-title {{
                font-size: 1rem;
                margin-bottom: 0.5rem;
            }}
            .card-text {{
                font-size: 0.9rem;
                margin-bottom: 0.3rem;
                line-height: 1.2;
            }}
            .py-3 {{
                padding-top: 0.5rem !important;
                padding-bottom: 0.5rem !important;
            }}
            .mb-3 {{
                margin-bottom: 0.5rem !important;
            }}
        </style>
    </head>
    <body class="bg-light">
        <div class="container py-3">
            <div class="text-center mb-2">
                <h1 class="display-5">🚗 Sortie du Parking</h1>
            </div>
            <div class="card shadow">
                <div class="card-body">
                    <h4 class="card-title">🗞 Détails de la sortie</h4>
                    <p class="card-text"><strong>Matricule :</strong> {plate}</p>
                    <p class="card-text"><strong>Durée de stationnement :</strong> {duree} minutes</p>
                    <p class="card-text"><strong>Montant :</strong> {statut}</p>
                    <p class="card-text"><strong>Voie de sortie :</strong> Voie {voie}</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    with open("dashboard_sortie.html", "w", encoding="utf-8") as f:
        f.write(html)
    ouvrir_dashboard("dashboard_sortie.html")


# === CONFIG ===
MODEL_PATH = 'yolov8n.pt'
IMAGE_PATH = 'image_originale.jpg'

# === DB CONFIG ===
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'MySQL2025',
    'database': 'parking_db',
    'port': 3306
}

# === UTILS ===
def normalize_arabic_word_to_tunisia(text: str) -> str:
    # Remplacer tous les mots arabes par تونس
    return re.sub(r'[\u0600-\u06FF]+', 'تونس', text)

def format_numbers(numbers):
    if not numbers:
        return '', ''
    # Pour la première partie (2 ou 3 chiffres)
    first_part = numbers[0]
    if len(first_part) > 3:
        first_part = first_part[-3:]  # Prendre les 3 derniers chiffres si plus de 3
    elif len(first_part) < 2:
        first_part = first_part.zfill(2)  # Ajouter des zéros si moins de 2 chiffres
    
    # Pour la deuxième partie (2, 3 ou 4 chiffres)
    second_part = numbers[1]
    if len(second_part) > 4:
        second_part = second_part[:4]  # Prendre les 4 premiers chiffres si plus de 4
    elif len(second_part) < 2:
        second_part = second_part.zfill(2)  # Ajouter des zéros si moins de 2 chiffres
    
    return first_part, second_part

def correct_plate_text(text: str) -> str:
    print(f">>> Traitement du texte de la plaque : {text}")
    try:
        # Normaliser d'abord le mot تونس
        text = normalize_arabic_word_to_tunisia(text)
        
        # Si le texte contient تونس
        if 'تونس' in text:
            # Séparer en deux parties
            parts = text.split('تونس')
            # Extraire tous les chiffres de chaque partie
            left_numbers = ''.join(re.findall(r'\d+', parts[0])) if len(parts) > 0 else ''
            right_numbers = ''.join(re.findall(r'\d+', parts[1])) if len(parts) > 1 else ''
            
            # Si la partie droite a plus de chiffres que la partie gauche, les échanger
            if len(right_numbers) > len(left_numbers):
                left_numbers, right_numbers = right_numbers, left_numbers
            
            # Formater les nombres selon le standard
            left, right = format_numbers([left_numbers, right_numbers])
            
            # Retourner le format standard
            formatted = f"{left} تونس {right}"
            print(f">>> Plaque formatée : {formatted}")
            return formatted
        else:
            # Si pas de تونس, extraire tous les chiffres
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:
                left, right = format_numbers(numbers)
                formatted = f"{left} تونس {right}"
                print(f">>> Plaque formatée : {formatted}")
                return formatted
        
        return text
    except Exception as e:
        print(f">>> Erreur lors du traitement du texte : {e}")
        return None

# === IMAGE PROCESSING FUNCTIONS ===
def preprocess_image(image):
    print(">>> Prétraitement de l'image...")
    try:
        # Définir des dimensions plus petites pour un meilleur affichage
        target_width = 1280  # Largeur réduite
        target_height = 720  # Hauteur réduite

        # Obtenir les dimensions actuelles
        height, width = image.shape[:2]
        
        # Calculer le ratio pour le redimensionnement
        width_ratio = target_width / width
        height_ratio = target_height / height
        
        # Utiliser le plus petit ratio pour maintenir les proportions
        ratio = min(width_ratio, height_ratio)
        
        # Calculer les nouvelles dimensions
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # Redimensionner l'image
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        print(f">>> Image redimensionnée à {new_width}x{new_height}")

        # Améliorer le contraste
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge((l,a,b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        print(">>> Prétraitement terminé avec succès")
        return enhanced
    except Exception as e:
        print(f">>> Erreur lors du prétraitement : {e}")
        return image

def find_plate_candidates(image):
    """Trouve les zones potentielles de plaques d'immatriculation"""
    print(">>> Recherche des zones de plaques potentielles...")
    
    # Convertir en niveaux de gris
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Réduction du bruit
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Détection des bords
    edges = cv2.Canny(blurred, 50, 150)
    
    # Trouver les contours
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrer les contours
    plate_candidates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        area = w * h
        
        # Filtrer par ratio et taille
        if 2.0 <= aspect_ratio <= 5.0 and area > 1000:
            roi = image[y:y+h, x:x+w]
            plate_candidates.append((roi, (x, y, w, h)))
            
            # Sauvegarder le candidat pour débogage
            cv2.imwrite(f'debug_candidate_{len(plate_candidates)}.jpg', roi)
    
    print(f">>> {len(plate_candidates)} zones candidates trouvées")
    return plate_candidates

def enhance_plate_region(plate_img):
    """Amélioration avancée de l'image de la plaque"""
    try:
        # Convertir en niveaux de gris si nécessaire
        if len(plate_img.shape) == 3:
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_img
            
        # Redimensionner si trop petit
        min_width = 300
        if gray.shape[1] < min_width:
            scale = min_width / gray.shape[1]
            gray = cv2.resize(gray, None, fx=scale, fy=scale)
        
        # Amélioration du contraste
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Binarisation adaptative
        binary = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2
        )
        
        # Opérations morphologiques
        kernel = np.ones((3,3), np.uint8)
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Sauvegarder les étapes
        cv2.imwrite('debug_plate_gray.jpg', gray)
        cv2.imwrite('debug_plate_enhanced.jpg', enhanced)
        cv2.imwrite('debug_plate_binary.jpg', binary)
        cv2.imwrite('debug_plate_morph.jpg', morph)
        
        return morph
    except Exception as e:
        print(f">>> Erreur lors de l'amélioration de la plaque : {e}")
        return plate_img

def detect_text_in_candidates(candidates, reader):
    """Détecte le texte dans chaque candidat"""
    best_plate = None
    best_confidence = 0
    
    for idx, (candidate, bbox) in enumerate(candidates):
        print(f"\n>>> Analyse du candidat {idx+1}")
        
        # Préparer l'image
        processed = enhance_plate_region(candidate)
        
        # Essayer différentes versions de l'image
        versions = [
            ("original", processed),
            ("inverted", 255 - processed),
            ("resized", cv2.resize(processed, None, fx=2, fy=2))
        ]
        
        for version_name, img in versions:
            print(f">>> Tentative sur version {version_name}")
            
            try:
                # OCR avec paramètres stricts
                results = reader.readtext(
                    img,
                    allowlist='0123456789تونس',
                    batch_size=1,
                    paragraph=False,
                    height_ths=0.5,
                    width_ths=0.5
                )
                
                # Analyser les résultats
                for result in results:
                    text = result[1]
                    conf = result[2]
                    print(f">>> Texte trouvé : '{text}' (confiance : {conf:.2f})")
                    
                    # Vérifier si c'est une plaque valide
                    if 'تونس' in text and any(c.isdigit() for c in text):
                        if conf > best_confidence:
                            best_confidence = conf
                            best_plate = (text, bbox, conf)
            
            except Exception as e:
                print(f">>> Erreur lors de la détection : {e}")
                continue
    
    return best_plate

# === MAIN FUNCTION ===
def main():
    try:
        print("\n=== DÉMARRAGE DU SYSTÈME DE DÉTECTION ===")
        
        # Charger le modèle YOLOv8
        print(">>> Chargement du modèle YOLOv8...")
        model = YOLO(MODEL_PATH)
        
        # Charger l'image
        print(f">>> Chargement de l'image : {IMAGE_PATH}")
        image = cv2.imread(IMAGE_PATH)
        if image is None:
            raise Exception("Impossible de charger l'image")
        
        # Prétraiter l'image
        processed_image = preprocess_image(image)
        cv2.imwrite('image_preprocessed.jpg', processed_image)
        
        # Détection avec YOLOv8
        print(">>> Détection des objets...")
        results = model(processed_image, conf=0.25)[0]
        
        # Initialiser EasyOCR avec des paramètres optimisés
        print(">>> Initialisation d'EasyOCR...")
        reader = easyocr.Reader(
            ['ar', 'en'],
            gpu=False,
            model_storage_directory='models',
            download_enabled=True
        )
        
        # Trouver les zones candidates
        candidates = find_plate_candidates(image)
        
        if not candidates:
            print(">>> Aucune zone de plaque potentielle trouvée")
            return
        
        # Détecter le texte dans les candidats
        best_plate = detect_text_in_candidates(candidates, reader)
        
        if best_plate:
            text, (x, y, w, h), conf = best_plate
            print(f"\n>>> Plaque détectée : {text} (confiance : {conf:.2f})")
            
            # Dessiner sur l'image
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(image, text, (x, y-10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Traiter la plaque détectée
            try:
                # Connexion à la base de données
                print(">>> Connexion à la base de données...")
                conn = mysql.connector.connect(**db_config)
                cursor = conn.cursor()
                
                # Vérifier si la plaque existe
                cursor.execute("SELECT id, date_entree, place FROM entries WHERE immatricule = %s", (text,))
                existing_entry = cursor.fetchone()
                
                if existing_entry:
                    # Logique de sortie
                    entry_id, date_entree, place = existing_entry
                    now = datetime.now()
                    duree = int((now - date_entree).total_seconds() // 60)
                    montant = max((duree - 1), 0) * 1
                    
                    cursor.execute("""
                        INSERT INTO history (immatricule, date_entree, date_sortie, duree_minutes, place)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (text, date_entree, now, duree, place))
                    
                    cursor.execute("DELETE FROM entries WHERE id = %s", (entry_id,))
                    cursor.execute("UPDATE places SET disponible = TRUE WHERE code = %s", (place,))
                    
                    conn.commit()
                    print(f">>> Sortie enregistrée pour la plaque {text}")
                    generer_dashboard_sortie(text, duree, montant)
                    
                else:
                    # Logique d'entrée
                    cursor.execute("SELECT code FROM places WHERE disponible = TRUE ORDER BY id ASC LIMIT 1")
                    available_place = cursor.fetchone()
                    
                    if available_place:
                        place = available_place[0]
                        now = datetime.now()
                        
                        cursor.execute("""
                            INSERT INTO entries (immatricule, date_entree, place)
                            VALUES (%s, %s, %s)
                        """, (text, now, place))
                        
                        cursor.execute("UPDATE places SET disponible = FALSE WHERE code = %s", (place,))
                        
                        conn.commit()
                        print(f">>> Entrée enregistrée pour la plaque {text}")
                        generer_dashboard_entree(text, place, now.strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        print(">>> Parking complet")
                
            except mysql.connector.Error as err:
                print(f">>> Erreur MySQL : {err}")
            finally:
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        else:
            print(">>> Aucune plaque valide détectée")
        
        # Sauvegarder les images finales
        cv2.imwrite('detections.jpg', image)
        print(">>> Images sauvegardées avec succès")
        
    except Exception as e:
        print(f">>> ERREUR CRITIQUE : {e}")
        raise

if __name__ == "__main__":
    main()