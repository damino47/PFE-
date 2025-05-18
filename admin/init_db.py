import mysql.connector
from werkzeug.security import generate_password_hash
import sys
import os

# Ajouter le répertoire parent au chemin de recherche Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from admin.config import DATABASE_CONFIG

def init_db():
    # Lire le contenu du fichier SQL
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(current_dir, 'database_setup.sql')
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_commands = f.read()

    # Connexion à MySQL
    conn = mysql.connector.connect(
        host=DATABASE_CONFIG['host'],
        user=DATABASE_CONFIG['user'],
        password=DATABASE_CONFIG['password']
    )
    cursor = conn.cursor()

    # Créer la base de données si elle n'existe pas
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_CONFIG['database']}")
    cursor.execute(f"USE {DATABASE_CONFIG['database']}")

    # Exécuter les commandes SQL
    for command in sql_commands.split(';'):
        if command.strip():
            cursor.execute(command.strip() + ';')

    # Créer toutes les tables nécessaires
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            numero INT PRIMARY KEY,
            occupied BOOLEAN DEFAULT FALSE,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            immatriculation VARCHAR(20) NOT NULL,
            place_numero INT,
            heure_entree TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            heure_sortie TIMESTAMP NULL,
            duree INT DEFAULT 0,
            montant DECIMAL(10,2) DEFAULT 0,
            status VARCHAR(50) DEFAULT 'en_cours',
            FOREIGN KEY (place_numero) REFERENCES places(numero)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paiements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            montant_paye DECIMAL(10,2) NOT NULL,
            montant_change DECIMAL(10,2) DEFAULT 0,
            status_paiement VARCHAR(50) DEFAULT 'en_attente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_status (
            id INT AUTO_INCREMENT PRIMARY KEY,
            equipment_name VARCHAR(100) NOT NULL,
            status VARCHAR(50) DEFAULT 'ok',
            last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP NULL
        )
    """)

    # Insérer les places de parking par défaut
    cursor.execute("INSERT IGNORE INTO places (numero) VALUES (1), (2), (3), (4), (5), (6)")

    # Insérer les équipements par défaut
    cursor.execute("""
        INSERT IGNORE INTO equipment_status (equipment_name) VALUES 
        ('Caméra Entrée'),
        ('Caméra Sortie'),
        ('Barrière Entrée'),
        ('Barrière Sortie'),
        ('Unité de Paiement')
    """)

    # Créer l'utilisateur admin
    admin_password = generate_password_hash('admin123')
    try:
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, ('admin', admin_password, 'admin'))
        print("Utilisateur admin créé avec succès!")
    except mysql.connector.IntegrityError:
        print("L'utilisateur admin existe déjà.")
        cursor.execute("""
            UPDATE users 
            SET password = %s
            WHERE username = 'admin'
        """, (admin_password,))
        print("Mot de passe admin mis à jour!")

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        init_db()
        print("Base de données initialisée avec succès!")
        print("Vous pouvez maintenant vous connecter avec:")
        print("Username: admin")
        print("Password: admin123")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
