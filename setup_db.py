import mysql.connector
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'parking_db'
}

def setup_database():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS recettes")
    cursor.execute("DROP TABLE IF EXISTS paiements")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    cursor.execute("DROP TABLE IF EXISTS users")

    # Create users table
    cursor.execute("""
    CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        nom VARCHAR(50) NOT NULL,
        prenom VARCHAR(50) NOT NULL,
        cin VARCHAR(8) NOT NULL UNIQUE,
        adresse TEXT NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('admin', 'user') DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create sessions table
    cursor.execute("""
    CREATE TABLE sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        immatriculation VARCHAR(20) NOT NULL,
        place_numero VARCHAR(10) NOT NULL,
        heure_entree DATETIME NOT NULL,
        heure_sortie DATETIME,
        duree INT,
        montant DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create paiements table
    cursor.execute("""
    CREATE TABLE paiements (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        montant_paye DECIMAL(10,2) NOT NULL,
        montant_change DECIMAL(10,2) DEFAULT 0.00,
        status_paiement ENUM('en_attente', 'completed', 'cancelled') DEFAULT 'en_attente',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """)

    # Create recettes table
    cursor.execute("""
    CREATE TABLE recettes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        session_id INT NOT NULL,
        user_id INT NOT NULL,
        montant DECIMAL(10,2) NOT NULL,
        date_recette TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Create admin user
    hashed_password = generate_password_hash('admin123')
    cursor.execute("""
    INSERT INTO users (username, nom, prenom, cin, adresse, password, role)
    VALUES (%s, 'Admin', 'System', '00000000', 'OACA Tunis', %s, 'admin')
    """, ('admin', hashed_password))
    admin_id = cursor.lastrowid

    # Insert test sessions
    now = datetime.now()
    test_sessions = [
        ('123 TUN 4567', 'P1', now - timedelta(hours=2), now - timedelta(hours=1), 60, 2.00),
        ('456 TUN 7890', 'P2', now - timedelta(hours=3), now - timedelta(minutes=30), 150, 5.00),
        ('789 TUN 1234', 'P3', now - timedelta(hours=1), None, None, None),
        ('321 TUN 5678', 'P4', now - timedelta(hours=4), now - timedelta(hours=2), 120, 4.00)
    ]

    for session in test_sessions:
        cursor.execute("""
        INSERT INTO sessions (immatriculation, place_numero, heure_entree, heure_sortie, duree, montant)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, session)
        session_id = cursor.lastrowid

        # Add payment and receipt for completed sessions
        if session[3] is not None:  # If heure_sortie is not None
            cursor.execute("""
            INSERT INTO paiements (session_id, montant_paye, montant_change, status_paiement)
            VALUES (%s, %s, %s, 'completed')
            """, (session_id, session[5], 0.00))

            cursor.execute("""
            INSERT INTO recettes (session_id, user_id, montant)
            VALUES (%s, %s, %s)
            """, (session_id, admin_id, session[5]))

    conn.commit()
    cursor.close()
    conn.close()

    print("Database setup completed successfully!")

if __name__ == "__main__":
    setup_database() 