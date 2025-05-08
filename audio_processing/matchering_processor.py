import os
import uuid
import logging
import tempfile
import shutil
import matchering as mg
from pathlib import Path
from pydub import AudioSegment
from .processor import generate_waveform_data

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("matchering_processor")

# Répertoire des références
REFERENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
USER_REFERENCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_references")

# Créer les répertoires s'ils n'existent pas
os.makedirs(REFERENCE_DIR, exist_ok=True)
os.makedirs(USER_REFERENCE_DIR, exist_ok=True)

# Simplification pour n'utiliser que deux références pour les presets Masterify
REFERENCE_TRACKS = {
    "masterify_v1": os.path.join(REFERENCE_DIR, "masterify_v1_reference.mp3"),
    "masterify_ia": os.path.join(REFERENCE_DIR, "masterify_ia_reference.mp3")
}

def process_with_matchering(input_file, preset_type, output_directory, original_filename=None, reference_file=None, use_reference=False):
    """
    Traite un fichier audio avec Matchering
    
    Args:
        input_file (str): Chemin vers le fichier d'entrée
        preset_type (str): Type de preset (masterify_v1 ou masterify_ia)
        output_directory (str): Répertoire où sauvegarder le fichier traité
        original_filename (str, optional): Nom du fichier original
        reference_file (str, optional): Chemin vers le fichier de référence fourni par l'utilisateur
        use_reference (bool): Si True, utilise la référence fournie, sinon traitement sans référence
        
    Returns:
        dict: Information sur le fichier traité
    """
    try:
        # Créer un ID unique pour le fichier de sortie
        file_id = str(uuid.uuid4())
        
        # Déterminer les paramètres en fonction du preset
        if preset_type.lower() == "masterify_ia":
            # Paramètres plus avancés pour le preset IA
            min_loudness = -24
            target_loudness = -14
            max_loudness = -8
            max_peak = 1.0
        else:
            # Paramètres standard pour Masterify V.1
            min_loudness = -30
            target_loudness = -16
            max_loudness = -10
            max_peak = 1.0

        # Créer le dossier temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            # Chemins des fichiers temporaires
            temp_target = os.path.join(temp_dir, "target.wav")
            temp_result = os.path.join(temp_dir, "result.wav")
            
            # Convertir le fichier d'entrée en WAV si nécessaire
            if not input_file.lower().endswith('.wav'):
                audio = AudioSegment.from_file(input_file)
                audio.export(temp_target, format="wav")
            else:
                shutil.copy(input_file, temp_target)
            
            # Configuration Matchering - utilise les paramètres par défaut de Matchering
            # Les paramètres de loudness sont stockés séparément pour un traitement manuel si nécessaire
            config = mg.Config()
            
            # Deux modes de traitement: avec ou sans référence
            if use_reference and reference_file and os.path.exists(reference_file):
                # Mode avec référence fournie par l'utilisateur
                logger.info(f"Traitement de {input_file} avec référence utilisateur {reference_file}")
                
                mg.process(
                    target=temp_target,
                    reference=reference_file,
                    results=[temp_result],
                    config=config
                )
            else:
                try:
                    # Mode sans référence utilisateur - utiliser la référence du système si disponible
                    preset_reference = REFERENCE_TRACKS.get(preset_type.lower())
                    
                    if preset_reference and os.path.exists(preset_reference):
                        # Utiliser la référence intégrée
                        logger.info(f"Traitement de {input_file} avec référence système {preset_reference}")
                        mg.process(
                            target=temp_target,
                            reference=preset_reference,
                            results=[temp_result],
                            config=config
                        )
                    else:
                        # Aucune référence disponible, traitement sans référence (ajustement standard)
                        logger.info(f"Traitement de {input_file} sans référence externe")
                        # Créer un fichier de résultat avec des ajustements audio standard
                        # en utilisant pydub pour des ajustements basiques
                        audio = AudioSegment.from_file(temp_target)
                        
                        # Normaliser à -0.1 dB
                        normalized = audio.normalize(headroom=0.1)
                        
                        # Appliquer un gain pour atteindre la loudness cible approximative
                        gain_adjustment = target_loudness + 14  # Approximation simple
                        if gain_adjustment > 0:
                            processed = normalized + gain_adjustment
                        else:
                            processed = normalized - abs(gain_adjustment)
                        
                        # Exporter le résultat
                        processed.export(temp_result, format="wav")
                except Exception as inner_e:
                    logger.error(f"Erreur lors du traitement standard: {str(inner_e)}")
                    # Fallback to basic processing
                    audio = AudioSegment.from_file(temp_target)
                    audio.normalize(headroom=0.1).export(temp_result, format="wav")
            
            # Nom du fichier de sortie
            if original_filename:
                basename = os.path.splitext(original_filename)[0]
                output_filename = f"{basename}_mastered_{preset_type}.mp3"
            else:
                output_filename = f"mastered_{file_id}.mp3"
            
            output_path = os.path.join(output_directory, output_filename)
            
            # Convertir le résultat en MP3
            audio = AudioSegment.from_wav(temp_result)
            audio.export(output_path, format="mp3", bitrate="320k")
            
            # Générer les données de forme d'onde
            waveform_data = generate_waveform_data(output_path)
            
            return {
                "success": True,
                "file_id": file_id,
                "processed_filename": output_filename,
                "waveform_data": waveform_data
            }
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement avec Matchering: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def save_user_reference(reference_file, user_id):
    """
    Sauvegarde une référence fournie par l'utilisateur
    
    Args:
        reference_file (str): Chemin vers le fichier de référence
        user_id (str/int): ID de l'utilisateur pour le nommage
        
    Returns:
        str: Chemin vers le fichier de référence sauvegardé ou None si erreur
    """
    try:
        # Vérifier que le fichier existe
        if not os.path.exists(reference_file):
            return None
            
        # Créer le répertoire des références utilisateur s'il n'existe pas
        os.makedirs(USER_REFERENCE_DIR, exist_ok=True)
        
        # Créer un nom unique pour cette référence
        reference_id = str(uuid.uuid4())
        dest_filename = f"user_{user_id}_{reference_id}.mp3"
        dest_file = os.path.join(USER_REFERENCE_DIR, dest_filename)
        
        # Convertir en MP3 si nécessaire
        if reference_file.lower().endswith('.mp3'):
            shutil.copy(reference_file, dest_file)
        else:
            audio = AudioSegment.from_file(reference_file)
            audio.export(dest_file, format="mp3", bitrate="320k")
        
        return dest_file
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la référence utilisateur: {str(e)}")
        return None

def get_available_references():
    """
    Retourne la liste des références système disponibles
    
    Returns:
        dict: Dictionnaire des références disponibles
    """
    available_references = {}
    
    for preset, path in REFERENCE_TRACKS.items():
        if os.path.exists(path):
            available_references[preset] = path
    
    return available_references 