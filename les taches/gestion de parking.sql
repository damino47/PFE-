-- Supprimer la base de données si elle existe
DROP DATABASE IF EXISTS gestion_parking;
CREATE DATABASE gestion_parking;
USE gestion_parking;

-- Supprimer les tables si elles existent déjà
DROP TABLE IF EXISTS alertes;
DROP TABLE IF EXISTS tarifs;
DROP TABLE IF EXISTS paiements;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS vehicules;

-- Table des véhicules
CREATE TABLE vehicules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plaque VARCHAR(20) UNIQUE NOT NULL,
    type VARCHAR(20) NOT NULL -- Ex: Voiture, Moto, etc.
);

-- Table des tickets de parking
CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicule_id INT NOT NULL,
    date_entree DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_sortie DATETIME NULL,
    FOREIGN KEY (vehicule_id) REFERENCES vehicules(id) ON DELETE CASCADE
);

-- Table des paiements
CREATE TABLE paiements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    montant DECIMAL(10,2) NOT NULL,
    mode_paiement ENUM('Carte Bancaire', 'Cash') NOT NULL,
    date_paiement DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

-- Table des tarifs dynamiques
CREATE TABLE tarifs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    periode VARCHAR(50) NOT NULL, -- Ex: Jour, Nuit, Week-end
    tarif DECIMAL(10,2) NOT NULL
);

-- Table des alertes
CREATE TABLE alertes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    type_alerte VARCHAR(50) NOT NULL, -- Ex: Stationnement prolongé, Non-paiement
    date_alerte DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);
USE gestion_parking;
SHOW TABLES;
