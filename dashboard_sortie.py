from admin.config import DATABASE_CONFIG, COLUMNS, VEHICLE_STATUS, DATE_FORMAT
from datetime import datetime
import mysql.connector
import os
import time
import threading
import keyboard
from dashboard_paiement import traiter_paiement_especes

# Obtenir le chemin absolu du répertoire du script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def init_db():
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Mot de passe par défaut de XAMPP est vide
            database='parking_db',
            port=3306  # Port par défaut de MySQL dans XAMPP
        )
        
        if conn.is_connected():
            cursor = conn.cursor()
            print("Connexion réussie à la base de données MySQL")
            
            # Lire et exécuter le script SQL d'initialisation
            sql_path = os.path.join(SCRIPT_DIR, 'admin', 'init_db.sql')
            try:
                with open(sql_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                    for statement in sql_script.split(';'):
                        if statement.strip():
                            cursor.execute(statement)
                
                conn.commit()
                print("Base de données initialisée avec succès")
            except Exception as e:
                print(f"Erreur lors de l'exécution du script SQL : {str(e)}")
            finally:
                cursor.close()
    except mysql.connector.Error as e:
        print(f"Erreur de connexion à MySQL : {str(e)}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            conn.close()
            print("Connexion à la base de données MySQL fermée")



def generer_dashboard_sortie(plaque, temps_entree, temps_sortie, place, duree_minutes):
    montant = calculer_montant(duree_minutes)
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Sortie - Aéroport Tunis-Carthage</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                margin: 0;
                padding: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                max-width: 1200px;
                padding: 1rem;
            }}
            .display-4 {{
                font-size: 2.5rem;
                font-weight: 700;
                color: #fff;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                margin: 0;
                line-height: 1.2;
            }}
            .card {{
                border: none;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                background: rgba(255, 255, 255, 0.9);
                margin-bottom: 0.5rem;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
            }}
            .info-item {{
                padding: 0.5rem;
            }}
            .info-label {{
                font-size: 1.2rem;
                color: #1e3c72;
                font-weight: bold;
            }}
            .info-value {{
                font-size: 1.6rem;
                color: #000;
            }}
            .payment-button {{
                display: block;
                width: 100%;
                padding: 1rem;
                font-size: 1.5rem;
                font-weight: bold;
                color: white;
                background: #28a745;
                border: none;
                border-radius: 10px;
                margin-top: 2rem;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .payment-button:hover {{
                background: #218838;
                transform: translateY(-2px);
            }}
        </style>
        <script>
            function procederAuPaiement() {{
                // Créer un formulaire pour appeler Python
                var form = document.createElement('form');
                form.method = 'POST';
                form.action = '/paiement';
                
                // Ajouter les données nécessaires
                var data = {{
                    plaque: '{plaque}',
                    temps_entree: '{temps_entree.isoformat()}',
                    temps_sortie: '{temps_sortie.isoformat()}',
                    place: '{place}',
                    duree_minutes: {duree_minutes},
                    montant: {montant}
                }};
                
                // Ajouter les données au formulaire
                for (var key in data) {{
                    var input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = key;
                    input.value = data[key];
                    form.appendChild(input);
                }}
                
                // Ajouter le formulaire à la page et le soumettre
                document.body.appendChild(form);
                form.submit();
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="text-center mb-3">
                <img src="OACA.jpg" alt="Logo" class="airport-logo">
                <h1 class="display-4">Sortie du Parking</h1>
            </div>
            <div class="card shadow">
                <div class="card-body">
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Véhicule :</div>
                            <div class="info-value">{plaque}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Place :</div>
                            <div class="info-value">{place}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Entrée :</div>
                            <div class="info-value">{temps_entree.strftime('%H:%M')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Sortie :</div>
                            <div class="info-value">{temps_sortie.strftime('%H:%M')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Durée :</div>
                            <div class="info-value">{duree_minutes:.1f} minutes</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Montant :</div>
                            <div class="info-value">{montant:.2f} DT</div>
                        </div>
                    </div>
                    
                    <button class="payment-button" onclick="procederAuPaiement()">
                        Valider le paiement
                    </button>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("dashboard_sortie.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    os.startfile("dashboard_sortie.html")
    # Attendre 10 secondes avant d'afficher l'interface de paiement
    time.sleep(10)
    
    # Appeler l'interface de paiement
    generer_interface_paiement(plaque, temps_entree, temps_sortie, place, duree_minutes, montant)

def enregistrer_sortie(vehicule_id, plaque, place, temps_entree):
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Mot de passe par défaut de XAMPP est vide
            database='parking_db',
            port=3306  # Port par défaut de MySQL dans XAMPP
        )
        cursor = conn.cursor()

        # Calculer le temps de sortie
        temps_sortie = datetime.now()

        # Calculer la durée de stationnement en minutes
        duree_minutes = (temps_sortie - temps_entree).total_seconds() / 60

        # Calculer le montant à payer
        if duree_minutes <= 1:
            montant = 0  # Gratuit pour 1 minute ou moins
            direction = "A"  # Voie de sortie gratuite
        else:
            minutes_payantes = int(duree_minutes - 1)  # Soustraire la première minute gratuite
            montant = minutes_payantes * 2  # 2 DT par minute
            direction = "B"  # Voie de sortie payante

        # Enregistrer dans l'historique
        cursor.execute('''
        INSERT INTO historique_stationnement 
        (plaque, place, temps_entree, temps_sortie, duree_minutes, montant, direction, status_paiement)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (plaque, place, temps_entree, temps_sortie, duree_minutes, montant, direction, 'en_attente'))

        # Mettre à jour le statut dans vehicules_en_stationnement
        cursor.execute('''
        UPDATE vehicules_en_stationnement
        SET temps_sortie = %s, status = 'en_attente_paiement'
        WHERE id = %s
        ''', (temps_sortie, vehicule_id))

        # Valider les modifications
        conn.commit()

        # Générer le tableau de bord de sortie
        generer_dashboard_sortie(plaque, temps_entree, temps_sortie, place, duree_minutes)

        # Afficher les informations de sortie
        print(f"Sortie enregistrée pour le véhicule {plaque} :")
        print(f" - Place : {place}")
        print(f" - Temps d'entrée : {temps_entree}")
        print(f" - Temps de sortie : {temps_sortie}")
        print(f" - Durée : {duree_minutes:.1f} minutes")
        print(f" - Montant à payer : {montant:.2f} DT")
        print(f" - Voie de sortie : {direction}")

        return duree_minutes, montant

    except mysql.connector.Error as e:
        print(f"Erreur lors de l'enregistrement de la sortie : {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()
    

 

def traiter_sortie():
    try:
        # Connexion à la base de données MySQL
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Mot de passe par défaut de XAMPP est vide
            database='parking_db',
            port=3306  # Port par défaut de MySQL dans XAMPP
        )
        cursor = conn.cursor(dictionary=True)  # Utiliser `dictionary=True` pour obtenir des résultats sous forme de dictionnaire

        # Rechercher le dernier véhicule en stationnement
        cursor.execute('''
        SELECT id, plaque, place, temps_entree 
        FROM vehicules_en_stationnement 
        WHERE status = 'en_stationnement'
        ORDER BY temps_entree DESC
        LIMIT 1
        ''')

        vehicule = cursor.fetchone()

        if vehicule:
            vehicule_id = vehicule['id']
            plaque = vehicule['plaque']
            place = vehicule['place']
            temps_entree = vehicule['temps_entree']

            print(f"\nTraitement de la sortie pour le véhicule :")
            print(f"ID : {vehicule_id}")
            print(f"Plaque : {plaque}")
            print(f"Place : {place}")
            print(f"Heure d'entrée : {temps_entree}")

            # Convertir `temps_entree` en objet datetime
            temps_entree = datetime.strptime(temps_entree, '%Y-%m-%d %H:%M:%S')

            # Enregistrer la sortie
            duree_minutes, montant = enregistrer_sortie(
                vehicule_id, plaque, place, temps_entree
            )

            print(f"\nSortie enregistrée :")
            print(f"Heure de sortie : {datetime.now()}")
            print(f"Durée : {duree_minutes:.1f} minutes")
            print(f"Montant : {montant:.2f} DT")

            # Si le stationnement est payant (> 1 minute)
            if duree_minutes > 1:
                print(f"\nTraitement du paiement :")
                print(f"Plaque : {plaque}")
                print(f"Durée : {duree_minutes:.1f} minutes")
                print(f"Montant dû : {montant:.2f} DT")

                # Traiter le paiement en espèces
                if traiter_paiement_especes(plaque, duree_minutes, montant):
                    print("✅ Paiement effectué avec succès")
                else:
                    print("❌ Échec du paiement")

            print(f"\nSortie terminée pour le véhicule {plaque}")
        else:
            print("\nAucun véhicule en stationnement trouvé")

    except mysql.connector.Error as e:
        print(f"Erreur lors de la connexion ou de l'exécution SQL : {str(e)}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

def surveiller_sorties_directement():
    print("\nSurveillance des sorties activée...")
    try:
        print("\nDétection de sortie...")
        traiter_sortie()
    except Exception as e:
        print(f"Erreur lors de la détection : {str(e)}")

def surveiller_sorties():
    print("=== Système de surveillance des sorties ===")
    print("Traitement direct d'une sortie...")
    # Initialiser la base de données
    init_db()
    
    # Traiter une seule sortie
    try:
        traiter_sortie()  # Appeler directement la fonction pour traiter une sortie
    except Exception as e:
        print(f"Erreur lors du traitement de la sortie : {str(e)}")



def generer_interface_paiement(plaque, temps_entree, temps_sortie, place, duree_minutes, montant):
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Paiement - Aéroport Tunis-Carthage</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                margin: 0;
                padding: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                max-width: 1200px;
                padding: 1rem;
            }}
            .display-4 {{
                font-size: 2.5rem;
                font-weight: 700;
                color: #fff;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                margin: 0;
                line-height: 1.2;
            }}
            .card {{
                border: none;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                background: rgba(255, 255, 255, 0.9);
                margin-bottom: 0.5rem;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
                margin-bottom: 2rem;
            }}
            .info-item {{
                padding: 0.5rem;
            }}
            .info-label {{
                font-size: 1.2rem;
                color: #1e3c72;
                font-weight: bold;
            }}
            .info-value {{
                font-size: 1.6rem;
                color: #000;
            }}
            .money-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                margin: 2rem 0;
            }}
            .money-button {{
                padding: 1.5rem;
                font-size: 1.5rem;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                background: #f8f9fa;
                transition: all 0.3s;
                cursor: pointer;
            }}
            .money-button:hover {{
                background: #e9ecef;
                transform: translateY(-2px);
            }}
            .total-amount {{
                font-size: 2rem;
                font-weight: bold;
                text-align: center;
                margin: 2rem 0;
                color: #1e3c72;
            }}
            .inserted-amount {{
                font-size: 1.8rem;
                text-align: center;
                margin: 1rem 0;
                padding: 1rem;
                background: #e9ecef;
                border-radius: 10px;
            }}
            .action-buttons {{
                display: flex;
                justify-content: center;
                gap: 1rem;
                margin-top: 2rem;
            }}
            .action-button {{
                padding: 1rem 2rem;
                font-size: 1.2rem;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .confirm-button {{
                background: #28a745;
                color: white;
            }}
            .cancel-button {{
                background: #dc3545;
                color: white;
            }}
        </style>
        <script>
            let insertedAmount = 0;
            
            function addMoney(amount) {{
                insertedAmount += amount;
                document.getElementById('insertedAmount').textContent = insertedAmount.toFixed(2);
                
                // Activer le bouton de confirmation si le montant est suffisant
                const confirmButton = document.getElementById('confirmButton');
                if (insertedAmount >= {montant}) {{
                    confirmButton.disabled = false;
                }}
            }}
            
            function resetAmount() {{
                insertedAmount = 0;
                document.getElementById('insertedAmount').textContent = '0.00';
                document.getElementById('confirmButton').disabled = true;
            }}
            
            function confirmPayment() {{
                // Envoyer les données au serveur et passer à l'interface de reçu
                window.location.href = `dashboard_paiement.html?plaque={plaque}&montant={montant}&montant_insere=${insertedAmount}`;
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="text-center mb-3">
                <img src="OACA.jpg" alt="Logo" class="airport-logo">
                <h1 class="display-4">Paiement du Stationnement</h1>
            </div>
            <div class="card shadow">
                <div class="card-body">
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Véhicule :</div>
                            <div class="info-value">{plaque}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Durée :</div>
                            <div class="info-value">{duree_minutes:.1f} minutes</div>
                        </div>
                    </div>
                    
                    <div class="total-amount">
                        Montant à payer : {montant:.2f} DT
                    </div>
                    
                    <div class="inserted-amount">
                        Montant inséré : <span id="insertedAmount">0.00</span> DT
                    </div>
                    
                    <div class="money-grid">
                        <button class="money-button" onclick="addMoney(1)">1 DT</button>
                        <button class="money-button" onclick="addMoney(2)">2 DT</button>
                        <button class="money-button" onclick="addMoney(5)">5 DT</button>
                        <button class="money-button" onclick="addMoney(10)">10 DT</button>
                        <button class="money-button" onclick="addMoney(20)">20 DT</button>
                        <button class="money-button" onclick="addMoney(50)">50 DT</button>
                    </div>
                    
                    <div class="action-buttons">
                        <button class="action-button cancel-button" onclick="resetAmount()">Annuler</button>
                        <button class="action-button confirm-button" id="confirmButton" onclick="confirmPayment()" disabled>
                            Confirmer le paiement
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("interface_paiement.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    os.startfile("interface_paiement.html")

if __name__ == "__main__":
    surveiller_sorties() 