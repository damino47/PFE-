-- Création de la table users
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table places
CREATE TABLE IF NOT EXISTS places (
    numero INT PRIMARY KEY,
    status ENUM('libre', 'occupee') DEFAULT 'libre'
);

-- Création de la table sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    immatriculation VARCHAR(20) NOT NULL,
    place_numero INT,
    heure_entree DATETIME DEFAULT CURRENT_TIMESTAMP,
    heure_sortie DATETIME,
    duree INT,
    montant DECIMAL(10,2),
    FOREIGN KEY (place_numero) REFERENCES places(numero)
);

-- Création de la table paiements
CREATE TABLE IF NOT EXISTS paiements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT,
    montant_paye DECIMAL(10,2) NOT NULL,
    montant_change DECIMAL(10,2) DEFAULT 0,
    status_paiement ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Création de la table notifications
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    type ENUM('info', 'warning', 'error') DEFAULT 'info',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table equipment_status
CREATE TABLE IF NOT EXISTS equipment_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_id INT NOT NULL,
    status ENUM('online', 'offline', 'error') DEFAULT 'offline',
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table detections
CREATE TABLE IF NOT EXISTS detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_path VARCHAR(255),
    plaque VARCHAR(20),
    confiance DECIMAL(5,2),
    date_detection TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table recettes
CREATE TABLE IF NOT EXISTS recettes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT,
    user_id INT,
    montant DECIMAL(10,2) NOT NULL,
    date_recette TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Insertion des places de parking
INSERT IGNORE INTO places (numero) VALUES (1), (2), (3), (4), (5), (6);

-- Création d'un utilisateur admin par défaut (mot de passe: admin123)
INSERT IGNORE INTO users (username, password, role) 
VALUES ('admin', 'pbkdf2:sha256:600000$7NEVhkFhxXClFYr7$c89775b7cfd5920cfb8e48e86d2a91e879cd4fd925fd0e60b2c31c51266d91b6', 'admin'); 