import os

# Configuration de la base de données XAMPP
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Mot de passe par défaut de XAMPP est vide
    'database': 'parking_db',
    'port': 3306  # Port par défaut de MySQL dans XAMPP
}

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YOLO_MODEL_PATH = os.path.join(BASE_DIR, 'weights', 'yolov8n.pt')

# Configuration de l'application
SECRET_KEY = 'votre_clé_secrète_ici'
SESSION_TYPE = 'filesystem'

# Configuration du parking
TOTAL_PLACES = 6
PRIX_PAR_HEURE = 2  # en Dinars Tunisiens

# Configuration des notifications
NOTIFICATION_TIMEOUT = 300  # 5 minutes en secondes
EQUIPMENT_CHECK_INTERVAL = 60  # 1 minute en secondes

# Configuration des billets acceptés
BILLETS_ACCEPTES = [1, 2, 5, 10, 20, 50]  # en Dinars Tunisiens

# Configuration des équipements
EQUIPMENT = {
    'camera_entree': {'id': 1, 'name': 'Caméra Entrée'},
    'camera_sortie': {'id': 2, 'name': 'Caméra Sortie'},
    'barriere_entree': {'id': 3, 'name': 'Barrière Entrée'},
    'barriere_sortie': {'id': 4, 'name': 'Barrière Sortie'},
    'unite_paiement': {'id': 5, 'name': 'Unité de Paiement'}
}
