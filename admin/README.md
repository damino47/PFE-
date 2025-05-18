# Application Administrative du Parking OACA

Cette application web permet la gestion administrative du parking dépose-minute à l'aéroport Tunis-Carthage.

## Fonctionnalités

- Authentification des utilisateurs (admin et utilisateurs)
- Surveillance en temps réel des places de parking
- Gestion des sessions de stationnement
- Suivi des paiements
- Notifications des pannes d'équipement
- Interface de paiement en espèces

## Prérequis

- Python 3.8+
- MySQL
- YOLOv8
- EasyOCR

## Installation

1. Cloner le projet
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Configurer la base de données MySQL :
   - Créer une base de données nommée 'parking_db'
   - Importer le fichier SQL fourni

4. Copier le fichier de configuration :
   ```bash
   cp config.example.py config.py
   ```
   Puis modifier les paramètres selon votre environnement

## Lancement de l'application

```bash
python app.py
```

L'application sera accessible à l'adresse : http://localhost:5000

## Structure des dossiers

```
admin/
├── app.py              # Application Flask principale
├── config.py           # Configuration de l'application
├── requirements.txt    # Dépendances Python
├── static/            # Fichiers statiques (CSS, images)
└── templates/         # Templates HTML
    ├── index.html    # Page d'accueil
    └── login.html    # Page de connexion
```

## Intégration avec les dashboards existants

L'application administrative partage la même base de données que les dashboards d'affichage existants :
- dashboard_entree
- dashboard_sortie
- dashboard_paiement

Les notifications et mises à jour sont synchronisées en temps réel entre tous les composants.
