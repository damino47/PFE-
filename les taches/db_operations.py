# db_operations.py
# Fonctions pour gérer les véhicules, tickets, paiements, tarifs et alertes
from config import get_db_connection
from datetime import datetime, timedelta

def ajouter_vehicule(plaque, type_vehicule):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO vehicules (plaque, type) VALUES (%s, %s)", (plaque, type_vehicule))
    connection.commit()
    cursor.close()
    connection.close()
    print("Véhicule ajouté.")

def enregistrer_ticket(plaque):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM vehicules WHERE plaque = %s", (plaque,))
    vehicule = cursor.fetchone()
    if vehicule:
        cursor.execute("INSERT INTO tickets (vehicule_id) VALUES (%s)", (vehicule[0],))
        connection.commit()
        print("Ticket enregistré.")
    else:
        print("Véhicule non trouvé.")
    cursor.close()
    connection.close()

def calculer_tarif(plaque):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT tickets.id, tickets.date_entree FROM tickets
    JOIN vehicules ON tickets.vehicule_id = vehicules.id
    WHERE vehicules.plaque = %s AND tickets.date_sortie IS NULL
    """, (plaque,))
    ticket = cursor.fetchone()
    if ticket:
        date_entree = ticket[1]
        maintenant = datetime.now()
        duree = (maintenant - date_entree).total_seconds() / 60
        if duree > 10:
            tarif = (duree - 10) * 2  # 2 dinars par minute après 10 minutes
        else:
            tarif = 0
        print(f"Tarif à payer : {tarif:.2f} dinars")
    else:
        print("Ticket non trouvé.")
    cursor.close()
    connection.close()

def enregistrer_paiement(plaque):
    connection = get_db_connection()
    cursor = connection.cursor()
    calculer_tarif(plaque)
    montant = float(input("Montant payé : "))
    mode = input("Mode de paiement (Carte Bancaire / Cash) : ")
    cursor.execute("""
    SELECT tickets.id FROM tickets
    JOIN vehicules ON tickets.vehicule_id = vehicules.id
    WHERE vehicules.plaque = %s AND tickets.date_sortie IS NULL
    """, (plaque,))
    ticket = cursor.fetchone()
    if ticket:
        cursor.execute("INSERT INTO paiements (ticket_id, montant, mode_paiement) VALUES (%s, %s, %s)",
                       (ticket[0], montant, mode))
        cursor.execute("UPDATE tickets SET date_sortie = NOW() WHERE id = %s", (ticket[0],))
        connection.commit()
        print("Paiement enregistré.")
    else:
        print("Ticket non trouvé.")
    cursor.close()
    connection.close()


def verifier_alertes():
    connection = get_db_connection()
    cursor = connection.cursor()

    print("🔍 Vérification des alertes en cours...")

    # Détection des véhicules stationnés plus de 60 minutes sans paiement
    cursor.execute("""
    SELECT vehicules.plaque, TIMESTAMPDIFF(MINUTE, tickets.entree, NOW()) AS duree
    FROM tickets
    JOIN vehicules ON tickets.vehicule_id = vehicules.id
    WHERE tickets.paye = 0 AND TIMESTAMPDIFF(MINUTE, tickets.entree, NOW()) > 60
    """)
    
    alertes = cursor.fetchall()

    if alertes:
        for plaque, duree in alertes:
            print(f"⚠️ Alerte : Le véhicule {plaque} est stationné depuis {duree} minutes sans paiement.")
    else:
        print("✅ Aucune alerte détectée.")

    cursor.close()
    connection.close()
    
