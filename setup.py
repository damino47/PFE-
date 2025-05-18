import os
import subprocess
import time

def install_mysql():
    print("\n1. Installer MySQL/XAMPP")
    print("- Téléchargez XAMPP depuis https://www.apachefriends.org/download.html")
    print("- Installez XAMPP en suivant les instructions")
    print("- Lancez le panneau de contrôle XAMPP")
    print("- Démarrez les services MySQL et Apache")

def create_database():
    print("\n2. Créer la base de données")
    print("- Ouvrez phpMyAdmin (http://localhost/phpmyadmin)")
    print("- Créez une nouvelle base de données nommée 'parking_db'")
    print("- Importez le fichier init_db.sql")

def install_python_packages():
    print("\n3. Installer les packages Python nécessaires")
    print("- Ouvrez un terminal dans le dossier du projet")
    print("- Exécutez ces commandes :")
    print("pip install flask flask-login mysql-connector-python ultralytics easyocr pillow")

def check_weights():
    weights_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'weights')
    model_path = os.path.join(weights_dir, 'yolov8n.pt')
    
    if not os.path.exists(weights_dir):
        print(f"\n4. Le dossier weights n'existe pas. Créez-le : {weights_dir}")
    
    if not os.path.exists(model_path):
        print(f"\n5. Le modèle YOLO n'est pas présent. Téléchargez-le depuis :")
        print("https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt")
        print(f"Et placez-le dans : {model_path}")

def main():
    print("Instructions pour résoudre les conflits :\n")
    install_mysql()
    create_database()
    install_python_packages()
    check_weights()
    
    print("\nUne fois ces étapes terminées, vous pourrez démarrer l'application avec :")
    print("python admin/app.py")

if __name__ == '__main__':
    main()
