#!/usr/bin/env python
import os
import sys
import requests
import shutil
from pathlib import Path

# Configuration
REFERENCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")
os.makedirs(REFERENCES_DIR, exist_ok=True)

# Liste des URL de références pour les presets Masterify
# Note: Ces URL sont fictives et doivent être remplacées par des liens réels vers des fichiers MP3 de référence
REFERENCE_URLS = {
    "masterify_v1": "https://example.com/reference_tracks/masterify_v1_reference.mp3",
    "masterify_ia": "https://example.com/reference_tracks/masterify_ia_reference.mp3",
}

def download_file(url, destination):
    """
    Télécharge un fichier depuis une URL
    
    Args:
        url (str): URL du fichier à télécharger
        destination (str): Chemin de destination
        
    Returns:
        bool: True si le téléchargement a réussi, False sinon
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(destination, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        
        print(f"Téléchargé: {destination}")
        return True
    except Exception as e:
        print(f"Erreur de téléchargement pour {url}: {str(e)}")
        return False

def copy_local_file(source, destination):
    """
    Copie un fichier local
    
    Args:
        source (str): Chemin source
        destination (str): Chemin de destination
        
    Returns:
        bool: True si la copie a réussi, False sinon
    """
    try:
        shutil.copy2(source, destination)
        print(f"Copié: {destination}")
        return True
    except Exception as e:
        print(f"Erreur de copie pour {source}: {str(e)}")
        return False

def setup_references():
    """
    Télécharge ou copie les fichiers de référence
    
    Returns:
        int: Nombre de références configurées avec succès
    """
    success_count = 0
    
    # Traiter tous les presets
    for preset, url in REFERENCE_URLS.items():
        destination = os.path.join(REFERENCES_DIR, f"{preset}_reference.mp3")
        
        # Si le fichier existe déjà, le sauter
        if os.path.exists(destination):
            print(f"Le fichier {destination} existe déjà, ignoré.")
            success_count += 1
            continue
        
        # S'il s'agit d'un chemin local
        if os.path.exists(url):
            if copy_local_file(url, destination):
                success_count += 1
        # Sinon, essayer de télécharger
        else:
            if download_file(url, destination):
                success_count += 1
                
    return success_count

def main():
    """Point d'entrée principal"""
    print(f"Configuration des références dans: {REFERENCES_DIR}")
    
    # Demander confirmation
    if len(sys.argv) < 2 or sys.argv[1] != "--force":
        answer = input("Ce script va télécharger ou copier les fichiers de référence. Continuer? (y/n): ")
        if answer.lower() != 'y':
            print("Opération annulée.")
            return 1
    
    # Configurer les références
    success_count = setup_references()
    
    print(f"\nConfiguration terminée. {success_count}/{len(REFERENCE_URLS)} références configurées avec succès.")
    
    if success_count < len(REFERENCE_URLS):
        print("\nCertaines références n'ont pas pu être configurées.")
        print("Pour configurer manuellement les références:")
        print(f"1. Placez des fichiers MP3 dans: {REFERENCES_DIR}")
        print("2. Nommez-les sous la forme: preset_reference.mp3 (ex: masterify_v1_reference.mp3)")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 