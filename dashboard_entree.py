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
    return mysql.connector.connect(**DATABASE_CONFIG)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Création des tables si elles n'existent pas
        # Table pour l'historique des stationnements
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS historique_stationnement (
            id INT AUTO_INCREMENT PRIMARY KEY,
            plaque VARCHAR(20) NOT NULL,
            place VARCHAR(10) NOT NULL,
            temps_entree DATETIME NOT NULL,
            temps_sortie DATETIME,
            duree_minutes FLOAT NOT NULL,
            montant DECIMAL(10, 2) NOT NULL,
            direction VARCHAR(20) NOT NULL,
            status_paiement VARCHAR(20) DEFAULT 'en_attente',
            INDEX (plaque),
            INDEX (temps_entree)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # Table pour les véhicules en stationnement
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicules_en_stationnement (
            id INT AUTO_INCREMENT PRIMARY KEY,
            plaque VARCHAR(20) NOT NULL,
            place VARCHAR(10) NOT NULL,
            temps_entree DATETIME DEFAULT CURRENT_TIMESTAMP,
            temps_sortie DATETIME NULL,
            status VARCHAR(20) DEFAULT 'en_stationnement',
            UNIQUE KEY (place)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        # Table pour les paiements
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS paiements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            historique_id INT,
            montant_paye DECIMAL(10, 2) NOT NULL,
            montant_change DECIMAL(10, 2) NOT NULL,
            date_paiement DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (historique_id) REFERENCES historique_stationnement(id) ON DELETE SET NULL,
            INDEX (date_paiement)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        conn.commit()
        print("Base de données initialisée avec succès!")
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
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
        text = re.sub(r'[^\d\s\u062a\u0648\u0646\u0633]', '', text)
        text = text.replace('تونن', 'تونس')
        text = ' '.join(text.split())
        return text.strip()

    def validate_plate(self, text):
        if not text or len(text) < 7:
            return False
            
        tunisia_variants = {
            'تونس': 'تونس',
            'تونن': 'تونس',
            'توس': 'تونس',
            'تونز': 'تونس',
            'تونص': 'تونس',
            'نونس': 'تونس'
        }
        
        for variant in tunisia_variants:
            if variant in text:
                text = text.replace(variant, tunisia_variants[variant])
                break
        else:
            return False
            
        numbers = ''.join(filter(str.isdigit, text))
        if len(numbers) != 7:
            return False
            
        parts = text.split('تونس')
        if len(parts) != 2:
            return False
            
        before_numbers = ''.join(filter(str.isdigit, parts[0]))
        after_numbers = ''.join(filter(str.isdigit, parts[1]))
        
        if len(before_numbers) != 4 or len(after_numbers) != 3:
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
    def __init__(self):
        self.places = {
            'P1': {'status': 'libre', 'description': 'Près de l\'entrée'},
            'P2': {'status': 'libre', 'description': 'Zone centrale'},
            'P3': {'status': 'libre', 'description': 'Accès facile'},
            'P4': {'status': 'occupé', 'description': 'Zone couverte'},
            'P5': {'status': 'occupé', 'description': 'Près de la sortie'},
            'P6': {'status': 'occupé', 'description': 'Zone VIP'}
        }
        
def get_available_place(self):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT place FROM vehicules_en_stationnement WHERE status = 'en_stationnement'")
        occupied = {row['place'] for row in cursor.fetchall()}

        for place, info in self.places.items():
            if place not in occupied:
                return place, info['description']

        return None  # aucune place libre
    except Exception as e:
        print(f"Erreur en vérifiant les places : {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def generer_dashboard_entree(plate, place, description, date_entree):
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Entrée - Aéroport Tunis-Carthage</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <meta http-equiv="refresh" content="5">
        <style>
            body {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                margin: 0;
                padding: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                max-width: 1200px;  /* Réduit la largeur totale */
                padding: 1rem;
            }}
            .display-4 {{
                font-size: 2.5rem;  /* Réduit la taille de la police */
                font-weight: 700;
                color: #fff;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                margin: 0;
                line-height: 1.2;
            }}
            .welcome-text {{
                font-size: 1.8rem;  /* Réduit la taille de la police */
                color: #fff;
                margin: 0.5rem 0;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.4);
            }}
            .card {{
                border: none;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                background: rgba(255, 255, 255, 0.9);
                margin-bottom: 0.5rem;
            }}
            .card-title {{
                font-size: 1.8rem;  /* Réduit la taille de la police */
                color: #1e3c72;
                font-weight: bold;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
            }}
            .info-item {{
                padding: 0.5rem;  /* Réduit le padding */
            }}
            .info-label {{
                font-size: 1.2rem;  /* Réduit la taille de la police */
                color: #1e3c72;
                font-weight: bold;
            }}
            .info-value {{
                font-size: 1.6rem;  /* Réduit la taille de la police */
                color: #000;
            }}
            .status-section {{
                margin-top: 1rem;
            }}
            .status-title {{
                font-size: 1.8rem;
                color: #1e3c72;
                text-align: center;
                font-weight: bold;
            }}
            .status-item {{
                font-size: 1.4rem;  /* Réduit la taille de la police */
                padding: 0.5rem;
                margin-bottom: 0.3rem;
                border-radius: 5px;
                font-weight: 500;
            }}
            .status-available {{
                background-color: #d4edda;
                color: #155724;
            }}
            .status-occupied {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            .airport-logo {{
                height: 60px;  /* Réduit la taille du logo */
                margin-bottom: 0.5rem;
            }}
            .footer {{
                color: white;
                font-size: 1rem;  /* Réduit la taille de la police */
                margin-top: 0.5rem;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="text-center mb-3">
                <img src="OACA.jpg" alt="Logo" class="airport-logo">
                <h1 class="display-4">Aéroport Tunis-Carthage</h1>
                <h2 class="welcome-text">Bienvenue • مرحبا • Welcome</h2>
            </div>
            <div class="card shadow mb-2">
                <div class="card-body p-3">
                    <h3 class="card-title text-center">🆕 Nouveau Véhicule</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <div>
                                <div class="info-label">N° :</div>
                                <div class="info-value">{plate}</div>
                            </div>
                            <div>
                                <div class="info-label">Place :</div>
                                <div class="info-value">{place}</div>
                            </div>
                        </div>
                        <div class="info-item">
                            <div>
                                <div class="info-label">Heure :</div>
                                <div class="info-value">{date_entree.strftime('%H:%M')}</div>
                            </div>
                            <div>
                                <div class="info-label">Date :</div>
                                <div class="info-value">{date_entree.strftime('%d/%m/%Y')}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card shadow">
                <div class="card-body p-3">
                    <div class="status-section">
                        <h4 class="status-title">État du Parking</h4>
                        <div class="status-item status-available">
                            Places Disponibles : P1, P2, P3
                        </div>
                        <div class="status-item status-occupied">
                            Places Occupées : P4, P5, P6
                        </div>
                    </div>
                </div>
            </div>
            <footer class="footer">
                <p>OACA 2025</p>
            </footer>
        </div>
    </body>
    </html>
    """
    with open("dashboard_entree.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    os.startfile("dashboard_entree.html")

def enregistrer_entree(plaque, place):
    print(f"Tentative d'enregistrement - Plaque: {plaque}, Place: {place}")
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si la place est déjà occupée
        cursor.execute('SELECT * FROM vehicules_en_stationnement WHERE place = %s', (place,))
        if cursor.fetchone():
            print(f"La place {place} est déjà occupée.")
            return False
            
        # Enregistrer l'entrée
        cursor.execute('''
            INSERT INTO vehicules_en_stationnement (plaque, place, status, temps_entree)
            VALUES (%s, %s, 'en_stationnement', NOW())
        ''', (plaque, place))
        
        conn.commit()
        print(f"Enregistrement réussi - Plaque: {plaque}, Place: {place}")
        return True
    except mysql.connector.Error as err:
        print(f"Erreur MySQL lors de l'enregistrement: {err}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"Erreur inattendue lors de l'enregistrement: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def surveiller_entree():
    detector = PlateDetector()
    parking = ParkingManager()
    
    while True:
        try:
            plaque = detector.detect_plate('voiture2.jpg')
            if plaque:
                place_info = parking.get_available_place()
                if place_info:
                    place, description = place_info
                    date_entree = datetime.now()
                    
                    # Enregistrer dans la base de données
                    enregistrer_entree(plaque, place)
                    
                    # Générer le dashboard
                    generer_dashboard_entree(plaque, place, description, date_entree)
                    
                    print(f"Véhicule {plaque} enregistré à la place {place}")
                else:
                    print("Parking complet")
            
            # Attendre 5 secondes avant la prochaine détection
            time.sleep(5)
            
        except Exception as e:
            print(f"Erreur : {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    init_db()  # Initialiser la base de données
    surveiller_entree() 