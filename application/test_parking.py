import os
import time
import shutil

def test_entree_sortie():
    print("\n=== Test d'entrée ===")
    # Utiliser l'image existante
    shutil.copy("test.jpg", "temp_test.jpg")
    os.system('python main.py')
    time.sleep(3)  # Attendre 3 secondes pour voir le dashboard
    
    print("\n=== Test de sortie ===")
    # Utiliser la même image pour simuler une sortie
    os.system('python main.py')
    os.system('python main.py')

if __name__ == "__main__":
    # Modifier le fichier main.py pour utiliser test.jpg
    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remplacer la configuration de l'image
    content = content.replace(
        "IMAGE_PATH = 'sortie.jpg'  # ou 'entree.jpg'",
        "IMAGE_PATH = 'temp_test.jpg'"
    )
    
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
        
    print(">>> Début du test entrée/sortie")
    test_entree_sortie()
    print("\n>>> Test terminé")
