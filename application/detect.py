import cv2
import numpy as np
import torch
from ultralytics import YOLO
import easyocr
import re

# === CONFIGURATION ===
MODEL_PATH = 'best.pt'  # Ton modèle YOLOv8 entraîné
IMAGE_PATH = 'test.jpg'  # Une image contenant une voiture et sa plaque

# === Fonction pour remplacer tout mot arabe par 'تونس' ===
def normalize_arabic_word_to_tunisia(text: str) -> str:
    arabic_pattern = r'[\u0600-\u06FF]+'
    return re.sub(arabic_pattern, 'تونس', text)

# === Fonction pour corriger le format de la plaque ===
def correct_plate_text(text: str) -> str:
    text = normalize_arabic_word_to_tunisia(text)
    if 'تونس' in text:
        parts = text.split('تونس')
        left_digits = ''.join(re.findall(r'\d+', parts[0])) if len(parts) > 0 else ''
        right_digits = ''.join(re.findall(r'\d+', parts[1])) if len(parts) > 1 else ''

        # Corriger si inversé
        if len(right_digits) <= 3 and len(left_digits) >= 4:
            left_digits, right_digits = right_digits, left_digits

        first_part = left_digits[-3:] if len(left_digits) >= 1 else ''
        second_part = right_digits[:4] if len(right_digits) >= 1 else ''

        if first_part and second_part:
            return f"{first_part} تونس {second_part}"

    digits = re.findall(r'\d+', text)
    if len(digits) >= 2:
        first = digits[0][-3:]
        second = digits[1][:4]
        return f"{first} تونس {second}"

    return text

# === ÉTAPE 1: Charger le modèle YOLOv8 ===
model = YOLO(MODEL_PATH)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"✅ Modèle YOLO chargé sur {device}")

# === ÉTAPE 2: Charger l'image ===
image = cv2.imread(IMAGE_PATH)
if image is None:
    raise FileNotFoundError(f"❌ Image non trouvée : {IMAGE_PATH}")
print(f"📷 Image chargée: {IMAGE_PATH}")

# === ÉTAPE 3: Détection de plaque ===
results = model(image)[0]

if len(results.boxes) == 0:
    print("❌ Aucune plaque détectée")
    exit()

# On prend la première plaque détectée
x1, y1, x2, y2 = map(int, results.boxes.xyxy[0])
plate_img = image[y1:y2, x1:x2]
cv2.imwrite("plate_crop.jpg", plate_img)
print("✅ Région de plaque extraite")

# === ÉTAPE 4: Lire la plaque avec EasyOCR ===
reader = easyocr.Reader(['ar', 'en'], gpu=torch.cuda.is_available())
ocr_results = reader.readtext(plate_img, detail=0)

if not ocr_results:
    print("❌ Aucun texte détecté par OCR")
    exit()

raw_text = ''.join(ocr_results)
print(f"🧾 Texte brut OCR: {raw_text}")

# === ÉTAPE 5: Normaliser et corriger ===
normalized_text = normalize_arabic_word_to_tunisia(raw_text)
print(f"🧾 Texte normalisé: {normalized_text}")

final_plate = correct_plate_text(normalized_text)
print(f"✅ Plaque finale: {final_plate}")