-- Création de la base de données si elle n'existe pas
CREATE DATABASE IF NOT EXISTS parking_db;
USE parking_db;

-- Table pour l'historique des stationnements
CREATE TABLE IF NOT EXISTS historique_stationnement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plaque VARCHAR(20) NOT NULL,
    place VARCHAR(10) NOT NULL,
    temps_entree DATETIME NOT NULL,
    temps_sortie DATETIME NOT NULL,
    duree_minutes FLOAT NOT NULL,
    montant DECIMAL(10, 2) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    status_paiement VARCHAR(20) DEFAULT 'en_attente',
    INDEX (plaque),
    INDEX (temps_entree)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table pour les véhicules en stationnement
CREATE TABLE IF NOT EXISTS vehicules_en_stationnement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plaque VARCHAR(20) NOT NULL,
    place VARCHAR(10) NOT NULL,
    temps_entree DATETIME DEFAULT CURRENT_TIMESTAMP,
    temps_sortie DATETIME NULL,
    status VARCHAR(20) DEFAULT 'en_stationnement',
    INDEX (plaque),
    UNIQUE KEY (place)  -- Pour s'assurer qu'une place ne peut pas être occupée par plusieurs véhicules
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Table pour les paiements
CREATE TABLE IF NOT EXISTS paiements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    historique_id INT,
    montant_paye DECIMAL(10, 2) NOT NULL,
    montant_change DECIMAL(10, 2) NOT NULL,
    date_paiement DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (historique_id) REFERENCES historique_stationnement(id) ON DELETE SET NULL,
    INDEX (date_paiement)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;