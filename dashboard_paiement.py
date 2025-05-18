from flask import Flask, render_template_string, jsonify, request, send_file
from datetime import datetime
import mysql.connector
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
import os
from PIL import Image
import traceback
import shutil
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import json

app = Flask(__name__)

# Définir les chemins absolus
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
RECEIPTS_DIR = os.path.join(STATIC_DIR, 'receipts')
MONNAIE_DIR = os.path.join(BASE_DIR, 'monnaie')
LOGO_PATH = os.path.join(BASE_DIR, 'OACA.jpg')

# Créer le dossier receipts s'il n'existe pas
os.makedirs(RECEIPTS_DIR, exist_ok=True)

# Configuration MySQL
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'parking_db'
}

def get_vehicle(vehicle_id):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT 
                id,
                plaque, 
                place, 
                temps_entree, 
                temps_sortie,
                duree,
                montant,
                status,
                payment_status
            FROM vehicules_en_stationnement
            WHERE id = %s
        ''', (vehicle_id,))
        
        result = cursor.fetchone()
        
        if result:
            # Calculer la durée si elle est nulle
            if result['temps_entree'] and result['temps_sortie']:
                temps_entree = datetime.strptime(str(result['temps_entree']), '%Y-%m-%d %H:%M:%S')
                temps_sortie = datetime.strptime(str(result['temps_sortie']), '%Y-%m-%d %H:%M:%S')
                duree_minutes = (temps_sortie - temps_entree).total_seconds() / 60
                result['duree'] = round(duree_minutes, 2)
            else:
                result['duree'] = 0
                
            # Calculer le montant en fonction de la durée
            from payment_utils import calculer_montant
            result['montant'] = calculer_montant(result['duree'])
            
            # Formater la plaque avec TUN au lieu des carrés
            if result['plaque'] and '■■■■' in result['plaque']:
                result['plaque'] = result['plaque'].replace('■■■■', 'TUN')
            
            return result
    except Exception as e:
        print(f"Erreur lors de la récupération du véhicule: {str(e)}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def get_latest_unpaid_vehicle():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT 
                id,
                plaque, 
                place, 
                temps_entree, 
                temps_sortie,
                duree,
                montant,
                status,
                payment_status
            FROM vehicules_en_stationnement
            WHERE status = 'sorti'
            ORDER BY temps_sortie DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        
        if result:
            # Calculer la durée si elle est nulle
            if result['temps_entree'] and result['temps_sortie']:
                temps_entree = datetime.strptime(str(result['temps_entree']), '%Y-%m-%d %H:%M:%S')
                temps_sortie = datetime.strptime(str(result['temps_sortie']), '%Y-%m-%d %H:%M:%S')
                duree_minutes = (temps_sortie - temps_entree).total_seconds() / 60
                result['duree'] = round(duree_minutes, 2)
            else:
                result['duree'] = 0
                
            # Calculer le montant en fonction de la durée
            from payment_utils import calculer_montant
            result['montant'] = calculer_montant(result['duree'])
            
            print(f"\nVéhicule trouvé:")
            print(f"ID: {result['id']}")
            print(f"Plaque: {result['plaque']}")
            print(f"Place: {result['place']}")
            print(f"Durée: {result['duree']:.2f} minutes")
            print(f"Montant: {result['montant']} DT")
            print(f"Statut: {result['status']}")
            print(f"Statut de paiement: {result['payment_status']}")
            
            return result
        else:
            print("Aucun véhicule en attente de paiement trouvé")
            return None
            
    except mysql.connector.Error as e:
        print(f"Erreur MySQL lors de la récupération du véhicule: {str(e)}")
        traceback.print_exc()
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def formater_plaque(plaque):
    # Si la plaque ne contient pas déjà 'TUN'
    if 'TUN' not in plaque:
        # Séparer les numéros
        parts = plaque.split()
        if len(parts) == 2:
            # Mettre le numéro de droite en premier, puis TUN, puis le numéro de gauche
            return f"{parts[1]} TUN {parts[0]}"
    return plaque
def traiter_paiement_especes(montant):
    """
    Traite un paiement en espèces
    Retourne un tuple (succès, message)
    """
    try:
        # Logique de traitement du paiement
        # Par exemple, enregistrement en base de données
        return True, "Paiement en espèces effectué avec succès"
    except Exception as e:
        return False, f"Erreur lors du traitement du paiement : {str(e)}"
def generer_recu_pdf(vehicle):
    try:
        # Créer le dossier receipts s'il n'existe pas
        receipts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'receipts')
        if not os.path.exists(receipts_dir):
            os.makedirs(receipts_dir)

        # Nom du fichier PDF
        filename = os.path.join(receipts_dir, f"recu_{vehicle['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

        # Créer le PDF
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        # Ajouter le logo OACA
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'OACA.jpg')
        if os.path.exists(logo_path):
            # Calculer la largeur du logo (25% de la largeur de la page)
            logo_width = width * 0.25
            # Calculer la position x pour centrer le logo
            x = (width - logo_width) / 2
            # Positionner le logo en haut de la page
            y = height - 150
            # Dessiner le logo
            c.drawImage(logo_path, x, y, width=logo_width, preserveAspectRatio=True)

        # Titre
        c.setFont("Helvetica-Bold", 24)
        # Positionner le titre sous le logo
        title_text = "Reçu de Paiement"
        title_width = c.stringWidth(title_text, "Helvetica-Bold", 24)
        x_title = (width - title_width) / 2
        c.drawString(x_title, height - 200, title_text)

        # Informations du véhicule
        c.setFont("Helvetica", 12)
        y = height - 250  # Commencer plus bas pour éviter le chevauchement avec le titre
        
        # Toutes les informations
        infos = [
            f"Numéro de reçu: {vehicle['id']}",
            f"Plaque d'immatriculation: {vehicle['plaque'].replace('■■■■', 'TUN') if '■■■■' in vehicle['plaque'] else vehicle['plaque']}",
            f"Place de parking: {vehicle['place']}",
            f"Heure d'entrée: {vehicle['temps_entree']}",
            f"Heure de sortie: {vehicle['temps_sortie']}",
            f"Durée de stationnement: {vehicle['duree']:.2f} minutes",
            f"Montant payé: {vehicle['montant']:.2f} DT",
            f"Date de paiement: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]

        for info in infos:
            c.drawString(50, y, info)
            y -= 20

        # Message de l'aéroport centré
        y -= 30  # Espace supplémentaire avant le message
        c.setFont("Helvetica-Bold", 14)
        footer_text = "Aéroport International de Tunis-Carthage"
        footer_width = c.stringWidth(footer_text, "Helvetica-Bold", 14)
        x_footer = (width - footer_width) / 2
        c.drawString(x_footer, y, footer_text)

        y -= 25  # Espace entre les deux lignes
        c.setFont("Helvetica-Bold", 12)
        thanks_text = "Merci de votre visite"
        thanks_width = c.stringWidth(thanks_text, "Helvetica-Bold", 12)
        x_thanks = (width - thanks_width) / 2
        c.drawString(x_thanks, y, thanks_text)

        c.save()
        return filename
    except Exception as e:
        print(f"Erreur lors de la génération du reçu: {str(e)}")
        traceback.print_exc()
        return None

def traiter_paiement(vehicle_id):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Mettre à jour le statut de paiement
        cursor.execute("""
            UPDATE vehicules_en_stationnement 
            SET payment_status = 'paid' 
            WHERE id = %s
        """, (vehicle_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return True
    except Exception as e:
        print(f"Erreur lors du traitement du paiement: {str(e)}")
        return False



@app.route('/')
def index():
    try:
        vehicle = get_latest_unpaid_vehicle()
        if not vehicle:
            vehicle = {
                'plaque': 'Aucun véhicule',
                'place': '-',
                'temps_entree': '-',
                'temps_sortie': '-',
                'duree': 0,
                'montant': 0
            }
        
        html = '''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Dashboard Paiement - Aéroport Tunis-Carthage</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <meta http-equiv="refresh" content="10">
            <style>
                body {
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    min-height: 100vh;
                    margin: 0;
                    padding: 0.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    max-width: 1200px;
                    padding: 1rem;
                }
                .display-4 {
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: #fff;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                    margin: 0;
                    line-height: 1.2;
                }
                .payment-text {
                    font-size: 1.8rem;
                    color: #fff;
                    margin: 0.5rem 0;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.4);
                }
                .card {
                    border: none;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                    background: rgba(255, 255, 255, 0.9);
                    margin-bottom: 0.5rem;
                }
                .info-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 1rem;
                }
                .info-item {
                    padding: 0.5rem;
                }
                .info-label {
                    font-size: 1.2rem;
                    color: #1e3c72;
                    font-weight: bold;
                }
                .info-value {
                    font-size: 1.6rem;
                    color: #000;
                }
                .airport-logo {
                    height: 60px;
                    margin-bottom: 0.5rem;
                }
                .btn-pay {
                    font-size: 1.5rem;
                    padding: 1rem 2rem;
                    background: linear-gradient(45deg, #1e3c72 0%, #2a5298 100%);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .btn-pay:hover, .btn-receipt:hover {
                    transform: translateY(-2px);
                }
                .btn-receipt {
                    background: linear-gradient(45deg, #2a5298 0%, #1e3c72 100%);
                    color: white;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    font-size: 1.5rem;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .payment-amount {
                    font-size: 2.5rem;
                    color: #1e3c72;
                    font-weight: bold;
                    margin-bottom: 1rem;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="text-center mb-3">
                    <img src="{{ url_for('static', filename='OACA.jpg') }}" alt="Logo" class="airport-logo">
                    <h1 class="display-4">Aéroport Tunis-Carthage</h1>
                    <h2 class="payment-text">Paiement • الدفع • Payment</h2>
                </div>
                <div class="card shadow mb-2">
                    <div class="card-body p-3">
                        <h3 class="card-title text-center">💳 Détails du paiement</h3>
                        <div class="info-grid">
                            <div class="info-item">
                                <div>
                                    <div class="info-label">N° :</div>
                                    <div class="info-value">{{ vehicle.plaque }}</div>
                                </div>
                                <div>
                                    <div class="info-label">Place :</div>
                                    <div class="info-value">{{ vehicle.place }}</div>
                                </div>
                            </div>
                            <div class="info-item">
                                <div>
                                    <div class="info-label">Durée :</div>
                                    <div class="info-value">{{ "%.1f"|format(vehicle.duree) }} min</div>
                                </div>
                                <div>
                                    <div class="info-label">Montant :</div>
                                    <div class="info-value payment-amount">{{ "%.2f"|format(vehicle.montant) }} DT</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card shadow">
                    <div class="card-body p-3 text-center">
                        <h4 class="payment-amount">{{ "%.2f"|format(vehicle.montant) }} DT</h4>
                        <button class="btn btn-pay mt-4" onclick="window.location.href='/payment'">
                            💶 Procéder au paiement
                        </button>
                    </div>
                </div>
                <footer class="footer">
                    <p>OACA 2025</p>
                </footer>
            </div>
        </body>
        </html>
        '''
        
        return render_template_string(html, vehicle=vehicle)
    except Exception as e:
        print(f"Erreur dans l'index: {str(e)}")
        traceback.print_exc()
        return "Une erreur s'est produite. Veuillez vérifier les logs du serveur.", 500

@app.route('/payment')
def payment():
    try:
        vehicle = get_latest_unpaid_vehicle()
        if not vehicle:
            return "Aucun véhicule à payer", 404
        
        html = '''
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Paiement - Aéroport Tunis-Carthage</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    min-height: 100vh;
                    margin: 0;
                    padding: 1rem;
                }
                .payment-container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.2);
                }
                .money-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 1rem;
                    margin: 2rem 0;
                }
                .money-item {
                    cursor: pointer;
                    transition: transform 0.2s;
                    text-align: center;
                }
                .money-item:hover {
                    transform: scale(1.1);
                }
                .money-image {
                    max-width: 150px;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                }
                .payment-info {
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 8px;
                    margin-bottom: 1rem;
                }
                .amount {
                    font-size: 2rem;
                    font-weight: bold;
                    color: #1e3c72;
                }
                .btn-receipt {
                    background: linear-gradient(45deg, #2a5298 0%, #1e3c72 100%);
                    color: white;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    font-size: 1.5rem;
                    cursor: pointer;
                    transition: all 0.3s;
                    display: none;
                }
                .btn-receipt:hover {
                    transform: translateY(-2px);
                }
                .btn-receipt {
                    background: linear-gradient(45deg, #2a5298 0%, #1e3c72 100%);
                    color: white;
                    border: none;
                    padding: 1rem 2rem;
                    border-radius: 8px;
                    font-size: 1.5rem;
                    cursor: pointer;
                    transition: all 0.3s;
                    opacity: 0.5;
                    margin-top: 2rem;
                    width: 100%;
                    max-width: 400px;
                    display: none;
                }
                .btn-receipt:disabled {
                    cursor: not-allowed;
                }
                .btn-receipt:not(:disabled):hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
            </style>
        </head>
        <body>
            <div class="payment-container">
                <h2 class="text-center mb-4">Paiement en espèces</h2>
                
                <div class="payment-info">
                    <div class="row">
                        <div class="col">
                            <p>Montant à payer: <span class="amount">{{ "%.2f"|format(vehicle.montant) }} DT</span></p>
                            <p>Montant inséré: <span id="inserted-amount" class="amount">0.00 DT</span></p>
                            <p>Reste à payer: <span id="remaining-amount" class="amount">{{ "%.2f"|format(vehicle.montant) }} DT</span></p>
                            <div id="monnaie-rendue" style="display: none;" class="alert alert-success mt-4">
                    Monnaie à rendre : <span class="amount">0 DT</span>
                </div>        </div>
                    </div>
                </div>

                <div class="money-grid" id="money-grid">
                    <div class="money-item" onclick="addMoney(1)">
                        <img src="{{ url_for('static', filename='monnaie/1 dinar.jpg') }}" alt="1 DT" class="money-image">
                        <p>1 DT</p>
                    </div>
                    <div class="money-item" onclick="addMoney(2)">
                        <img src="{{ url_for('static', filename='monnaie/2 dinar.jpg') }}" alt="2 DT" class="money-image">
                        <p>2 DT</p>
                    </div>
                    <div class="money-item" onclick="addMoney(5)">
                        <img src="{{ url_for('static', filename='monnaie/5 dinar.jpg') }}" alt="5 DT" class="money-image">
                        <p>5 DT</p>
                    </div>
                    <div class="money-item" onclick="addMoney(10)">
                        <img src="{{ url_for('static', filename='monnaie/10 dinar.jpg') }}" alt="10 DT" class="money-image">
                        <p>10 DT</p>
                    </div>
                    <div class="money-item" onclick="addMoney(20)">
                        <img src="{{ url_for('static', filename='monnaie/20 dinar.jpg') }}" alt="20 DT" class="money-image">
                        <p>20 DT</p>
                    </div>
                    <div class="money-item" onclick="addMoney(50)">
                        <img src="{{ url_for('static', filename='monnaie/50 dinar.jpg') }}" alt="50 DT" class="money-image">
                        <p>50 DT</p>
                    </div>
                </div>

                <div id="monnaie-rendue" style="display: none;" class="alert alert-success mt-4 text-center">
                    Monnaie à rendre : <span class="amount">0 DT</span>
                </div>

                <div class="text-center mt-4">
                    <button class="btn btn-receipt" id="btn-receipt" onclick="window.location.href='/generer_recu/{{ vehicle.id }}'" disabled>
                        📄 Générer le reçu
                    </button>
                </div>

                <div class="text-center">
                    <button id="complete-payment" class="btn btn-success btn-lg" style="display: none;" onclick="completePayment()">
                        Terminer le paiement
                    </button>
                </div>
            </div>

            <script>
                let insertedAmount = 0;
                const totalAmount = {{ vehicle.montant }};
                
                function updateAmounts() {
                    document.getElementById('inserted-amount').textContent = insertedAmount.toFixed(2) + ' DT';
                    const remaining = Math.max(0, totalAmount - insertedAmount);
                    document.getElementById('remaining-amount').textContent = remaining.toFixed(2) + ' DT';
                    
                    // Activer/désactiver le bouton de reçu
                    const btnReceipt = document.getElementById('btn-receipt');
                    if (insertedAmount >= totalAmount) {
                        btnReceipt.disabled = false;
                        btnReceipt.style.opacity = '1';
                        const monnaieRendue = insertedAmount - totalAmount;
                        document.getElementById('monnaie-rendue').style.display = 'block';
                        document.getElementById('monnaie-rendue').querySelector('.amount').textContent = monnaieRendue.toFixed(2) + ' DT';
                        
                        // Traiter le paiement
                        const data = {
                            montant_paye: insertedAmount,
                            monnaie_rendue: monnaieRendue.toFixed(2)
                        };
                        
                        fetch('/process_payment/{{ vehicle.id }}', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(data)
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                document.getElementById('btn-receipt').style.display = 'inline-block';
                            } else {
                                alert('Erreur lors du paiement: ' + data.error);
                            }
                        })
                        .catch(error => {
                            console.error('Erreur:', error);
                            alert('Erreur lors du paiement');
                        });
                    } else {
                        btnReceipt.disabled = true;
                        btnReceipt.style.opacity = '0.5';
                    }
                }
                
                function addMoney(amount) {
                    insertedAmount += amount;
                    updateAmounts();
                }
            </script>
        </body>
        </html>
        '''
        
        return render_template_string(html, vehicle=vehicle)
    except Exception as e:
        print(f"Erreur dans la page de paiement: {str(e)}")
        traceback.print_exc()
        return "Une erreur s'est produite. Veuillez vérifier les logs du serveur.", 500

@app.route('/process_payment/<int:vehicle_id>', methods=['POST'])
def process_payment(vehicle_id):
    try:
        data = request.json
        vehicle = get_vehicle(vehicle_id)
        if not vehicle:
            return jsonify({'success': False, 'error': 'Véhicule non trouvé'})
        
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        # Mettre à jour le statut de paiement
        cursor.execute('''
            UPDATE vehicules_en_stationnement
            SET payment_status = 'paid'
            WHERE id = %s
        ''', (vehicle['id'],))
        
        # Enregistrer le paiement
        cursor.execute('''
            INSERT INTO historique_paiements 
            (vehicule_id, plaque, montant, montant_paye, monnaie_rendue, date_paiement, methode_paiement)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            vehicle['id'],
            vehicle['plaque'],
            vehicle['montant'],
            float(data['montant_paye']),
            float(data['monnaie_rendue']),
            datetime.now(),
            'especes'
        ))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Erreur lors du traitement du paiement: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generer_recu/<int:vehicle_id>')
def generer_recu(vehicle_id):
    try:
        vehicle = get_vehicle(vehicle_id)
        if not vehicle:
            return 'Véhicule non trouvé', 404
            
        filename = generer_recu_pdf(vehicle)
        if filename:
            try:
                return send_file(
                    filename,
                    as_attachment=True,
                    download_name=f"recu_{vehicle_id}.pdf",
                    mimetype='application/pdf'
                )
            except Exception as e:
                print(f"Erreur lors de l'envoi du fichier: {str(e)}")
                traceback.print_exc()
                return 'Erreur lors de l\'envoi du reçu', 500
        return 'Erreur lors de la génération du reçu', 500
    except Exception as e:
        print(f"Erreur lors de la génération du reçu: {str(e)}")
        traceback.print_exc()
        return 'Erreur lors de la génération du reçu', 500


@app.route('/static/receipts/<path:filename>')
def serve_receipt(filename):
    try:
        return send_file(os.path.join(RECEIPTS_DIR, filename))
    except Exception as e:
        print(f"Erreur lors de l'envoi du reçu: {str(e)}")
        traceback.print_exc()
        abort(404)

if __name__ == '__main__':
    app.run(port=8000, debug=True) 