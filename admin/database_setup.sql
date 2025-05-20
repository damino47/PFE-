-- Suppression des tables existantes dans l'ordre pour respecter les contraintes de clé étrangère
DROP TABLE IF EXISTS recettes;
DROP TABLE IF EXISTS images_detections;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS places;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS equipment_status;
DROP TABLE IF EXISTS notifications;

-- Création de la table users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de la table places
CREATE TABLE places (
    numero INT PRIMARY KEY,
    occupied BOOLEAN DEFAULT FALSE,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertion des places de parking (P1 à P6)
INSERT INTO places (numero) VALUES (1), (2), (3), (4), (5), (6);

-- Création de la table sessions
CREATE TABLE sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    immatriculation VARCHAR(20) NOT NULL,
    heure_entree TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    heure_sortie TIMESTAMP NULL,
    montant DECIMAL(10,2) DEFAULT 0,
    duree INT DEFAULT 0,
    place_numero INT,
    status VARCHAR(50) DEFAULT 'en_cours',
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (place_numero) REFERENCES places(numero)
);

-- Création de la table recettes
CREATE TABLE recettes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    user_id INT NOT NULL,
    montant DECIMAL(10,2) NOT NULL,
    date_recette TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Création de la table images_detections
CREATE TABLE images_detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    texte_extrait VARCHAR(20),
    type_detection ENUM('entree', 'sortie') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Création de la table equipment_status
CREATE TABLE equipment_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'ok',
    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertion des équipements
INSERT INTO equipment_status (equipment_name) VALUES
('Caméra Entrée'),
('Caméra Sortie'),
('Barrière Entrée'),
('Barrière Sortie'),
('Unité de Paiement');

-- Création de la table notifications
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL
);

-- Insertion d'un utilisateur admin par défaut (mot de passe: admin123)
INSERT INTO users (username, password, role) 
VALUES ('admin', 'pbkdf2:sha256:150000$KCwsw8nj$b94463d68b7fdb3454b6a05dd4d8ac9bd147eaac9277b7a39c35b238f6ef7dcd', 'admin')
ON DUPLICATE KEY UPDATE role = 'admin';

-- Insertion d'un utilisateur normal pour test (mot de passe: user123)
INSERT INTO users (username, password, role)
VALUES ('user1', 'pbkdf2:sha256:150000$KCwsw8nj$b94463d68b7fdb3454b6a05dd4d8ac9bd147eaac9277b7a39c35b238f6ef7dcd', 'user')
ON DUPLICATE KEY UPDATE role = 'user';
