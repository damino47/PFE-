import mysql.connector
from mysql.connector import Error

def check_database():
    try:
        # Configuration de connexion (à adapter selon votre configuration XAMPP)
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Mot de passe par défaut de XAMPP est vide
            database='parking_db'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Vérifier les tables existantes
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print("\nTables dans la base de données parking_db:")
            for table in tables:
                print(f"- {table[0]}")
                
                # Afficher la structure de chaque table
                cursor.execute(f"DESCRIBE {table[0]}")
                print(f"\nStructure de la table {table[0]}:\n")
                for column in cursor.fetchall():
                    print(f"Colonne: {column[0]}, Type: {column[1]}, Null: {column[2]}, Key: {column[3]}")
                print("\n" + "="*50 + "\n")
    
    except Error as e:
        print(f"Erreur de connexion à la base de données: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    check_database()
