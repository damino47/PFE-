from datetime import datetime
import os
import sqlite3
import time
import threading
import keyboard
from dashboard_paiement import traiter_paiement_especes

# Obtenir le chemin absolu du répertoire du script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def init_db():
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    # Lire et exécuter le script SQL d'initialisation
    sql_path = os.path.join(SCRIPT_DIR, 'admin', 'init_db.sql')
    try:
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)
        
        conn.commit()
        print("Base de données initialisée avec succès")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
        print("Création des tables directement...")
        
        # Créer les tables directement si le fichier SQL n'est pas trouvé
        cursor.executescript("""
        -- Table pour l'historique des stationnements
        CREATE TABLE IF NOT EXISTS historique_stationnement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaque TEXT NOT NULL,
            place TEXT NOT NULL,
            temps_entree TIMESTAMP NOT NULL,
            temps_sortie TIMESTAMP NOT NULL,
            duree_minutes REAL NOT NULL,
            montant REAL NOT NULL,
            direction TEXT NOT NULL,
            status_paiement TEXT DEFAULT 'en_attente'
        );

        -- Table pour les véhicules en stationnement
        CREATE TABLE IF NOT EXISTS vehicules_en_stationnement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plaque TEXT NOT NULL,
            place TEXT NOT NULL,
            temps_entree TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            temps_sortie TIMESTAMP,
            status TEXT DEFAULT 'en_stationnement'
        );

        -- Table pour les paiements
        CREATE TABLE IF NOT EXISTS paiements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            historique_id INTEGER,
            montant_paye REAL NOT NULL,
            montant_change REAL NOT NULL,
            date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (historique_id) REFERENCES historique_stationnement(id)
        );
        """)
        
        conn.commit()
        print("Tables créées avec succès")
    
    finally:
        conn.close()

def calculer_montant(duree_minutes):
    # Gratuit si ≤ 1 minute
    if duree_minutes <= 1:
        return 0
    
    # Au-delà d'une minute, 2 DT par minute
    minutes_payantes = int(duree_minutes - 1)  # On soustrait la première minute gratuite
    return minutes_payantes * 2

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
    return montant  # Retourner le montant pour utilisation ultérieure

def enregistrer_sortie(vehicule_id, plaque, place, temps_entree):
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    temps_sortie = datetime.now()
    duree_minutes = (temps_sortie - temps_entree).total_seconds() / 60
    montant = calculer_montant(duree_minutes)
    direction = "A" if duree_minutes <= 1 else "B"
    
    # Enregistrer dans l'historique
    cursor.execute('''
    INSERT INTO historique_stationnement 
    (plaque, place, temps_entree, temps_sortie, duree_minutes, montant, direction, status_paiement)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (plaque, place, temps_entree, temps_sortie, duree_minutes, montant, direction, 'en_attente'))
    
    # Mettre à jour le statut dans vehicules_en_stationnement
    cursor.execute('''
    UPDATE vehicules_en_stationnement
    SET temps_sortie = ?, status = 'en_attente_paiement'
    WHERE id = ?
    ''', (temps_sortie, vehicule_id))
    
    conn.commit()
    conn.close()
    
    # Générer le dashboard de sortie
    generer_dashboard_sortie(plaque, temps_entree, temps_sortie, place, duree_minutes)
    
    return duree_minutes, montant

def traiter_sortie():
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    
    # Rechercher le dernier véhicule en stationnement
    cursor.execute('''
    SELECT id, plaque, place, temps_entree 
    FROM vehicules_en_stationnement 
    WHERE status = 'en_stationnement'
    ORDER BY temps_entree DESC
    LIMIT 1
    ''')
    
    vehicule = cursor.fetchone()
    conn.close()
    
    if vehicule:
        vehicule_id, plaque, place, temps_entree = vehicule
        print(f"\nTraitement de la sortie pour le véhicule :")
        print(f"ID : {vehicule_id}")
        print(f"Plaque : {plaque}")
        print(f"Place : {place}")
        print(f"Heure d'entrée : {temps_entree}")
        
        temps_entree = datetime.strptime(temps_entree, '%Y-%m-%d %H:%M:%S.%f')
        
        # Enregistrer la sortie
        duree_minutes, montant = enregistrer_sortie(
            vehicule_id, plaque, place, temps_entree
        )
        
        print(f"\nSortie enregistrée :")
        print(f"Heure de sortie : {temps_sortie}")
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

def surveiller_clavier():
    print("\nAppuyez sur 'S' pour simuler une sortie de véhicule...")
    while True:
        try:
            if keyboard.is_pressed('s'):
                print("\nDétection de sortie...")
                traiter_sortie()
                time.sleep(1)  # Éviter les détections multiples
        except Exception as e:
            print(f"Erreur lors de la détection: {str(e)}")
            time.sleep(1)

def surveiller_sorties():
    print("=== Système de surveillance des sorties ===")
    print("Instructions:")
    print("1. Attendez qu'un véhicule soit enregistré à l'entrée")
    print("2. Appuyez sur 'S' pour simuler sa sortie")
    print("3. La dashboard de sortie s'affichera automatiquement")
    print("\nEn attente...")
    
    # Initialiser la base de données
    init_db()
    
    # Démarrer la surveillance du clavier dans un thread séparé
    thread_clavier = threading.Thread(target=surveiller_clavier)
    thread_clavier.daemon = True
    thread_clavier.start()
    
    # Maintenir le programme en cours d'exécution
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt du système de surveillance...")

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