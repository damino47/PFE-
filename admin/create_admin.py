import mysql.connector
from werkzeug.security import generate_password_hash
from config import DATABASE_CONFIG

def init_db():
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

    # Créer la table users si elle n'existe pas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
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
        # Mettre à jour le mot de passe de l'admin existant
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
