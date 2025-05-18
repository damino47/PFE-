import mysql.connector
from mysql.connector import Error
import os

# Configuration de la base de données
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Mot de passe par défaut de XAMPP est vide
    'port': 3306
}

def create_database():
    try:
        # Se connecter au serveur MySQL
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        # Créer la base de données si elle n'existe pas
        cursor.execute("CREATE DATABASE IF NOT EXISTS parking_db")
        print("Base de données 'parking_db' vérifiée/créée avec succès.")
        
        # Utiliser la base de données
        cursor.execute("USE parking_db")
        
        # Lire le fichier SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'admin', 'database_setup.sql')
        with open(sql_file, 'r', encoding='utf-8') as file:
            sql_commands = file.read().split(';')
        
        # Exécuter chaque commande SQL
        for command in sql_commands:
            try:
                if command.strip() != '':
                    cursor.execute(command)
            except mysql.connector.Error as err:
                print(f"Erreur lors de l'exécution de la commande: {command}")
                print(f"Erreur: {err}")
        
        # Valider les changements
        connection.commit()
        print("Script d'initialisation de la base de données exécuté avec succès.")
        
    except Error as e:
        print(f"Erreur lors de la connexion à MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Connexion MySQL fermée.")

if __name__ == "__main__":
    create_database()
