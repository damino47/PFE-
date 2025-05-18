import mysql.connector
from mysql.connector import Error

try:
    # Configuration de connexion
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # Mot de passe par défaut de XAMPP est vide
        database='parking_db'
    )
    
    if connection.is_connected():
        print("Connexion réussie à la base de données!")
        
        # Vérifier les tables
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\nTables trouvées:")
        for table in tables:
            print(f"- {table[0]}")
        
        cursor.close()
        
except Error as e:
    print(f"Erreur de connexion: {e}")
    
    # Essayer de se connecter sans spécifier la base de données
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        print("\nConnexion au serveur MySQL réussie, mais impossible d'accéder à la base 'parking_db'")
        print("Veuillez vérifier que la base de données 'parking_db' existe dans votre serveur MySQL.")
    except Error as e:
        print("\nImpossible de se connecter au serveur MySQL.")
        print("Veuillez vérifier que le serveur MySQL est en cours d'exécution.")
        print(f"Détail de l'erreur: {e}")
    
finally:
    if 'connection' in locals() and connection.is_connected():
        connection.close()
        print("\nConnexion MySQL fermée.")
