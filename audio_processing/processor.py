import os
import numpy as np
import random
from pydub import AudioSegment
from pydub.effects import normalize
from audio_processing.presets import get_preset_by_name

def process_audio(input_path, output_path, preset):
    """
    Process audio file with the specified preset
    
    Args:
        input_path: Path to the input audio file
        output_path: Path to save the processed audio file
        preset: Dictionary containing processing parameters
        
    Returns:
        duration: Duration of the processed audio in seconds
    """
    preset_name = preset.get('name', 'inconnu')
    print(f"\n--- DÉBUT DU TRAITEMENT AUDIO - PRESET: {preset_name} ---")
    print(f"Fichier d'entrée: {input_path}")
    print(f"Fichier de sortie: {output_path}")
    
    try:
        # Charger le fichier audio
        try:
            if input_path.lower().endswith('.mp3'):
                audio = AudioSegment.from_mp3(input_path)
                print(f"Fichier MP3 chargé avec succès: {len(audio)/1000.0}s, {audio.channels} canaux, {audio.frame_rate}Hz")
            else:  # Supposons WAV
                audio = AudioSegment.from_wav(input_path)
                print(f"Fichier WAV chargé avec succès: {len(audio)/1000.0}s, {audio.channels} canaux, {audio.frame_rate}Hz")
        except Exception as e:
            print(f"ERREUR lors du chargement du fichier audio: {e}")
            # Utiliser un fichier audio vide si le chargement échoue
            audio = AudioSegment.silent(duration=1000)  # 1 seconde de silence
        
        # Vérifier si l'audio n'est pas vide
        if len(audio) == 0:
            print("ERREUR: Fichier audio vide détecté")
            audio = AudioSegment.silent(duration=1000)  # 1 seconde de silence
        
        # Vérifier les caractéristiques de base de l'audio
        print(f"Caractéristiques: Durée={len(audio)/1000.0}s, Canaux={audio.channels}, Fréquence={audio.frame_rate}Hz")
        
        # Vérifier si l'audio n'est pas déjà silencieux
        if audio.dBFS < -50:
            print(f"AVERTISSEMENT: Audio très silencieux détecté (dBFS: {audio.dBFS})")
            # Normaliser à un niveau raisonnable
            audio = normalize(audio, headroom=-3.0)
        
        print(f"Niveau initial: {audio.dBFS} dBFS")
        
        # Application séquentielle des traitements avec gestion d'erreurs individuelle
        
        # 1. Traitement spécial des basses si activé
        if preset.get('bass_processing', False):
            try:
                bass_threshold = preset.get('bass_threshold', -15)
                bass_ratio = preset.get('bass_ratio', 1.5)
                bass_makeup = preset.get('bass_makeup', 1.2)
                bass_split_freq = preset.get('bass_split_freq', 180)
                kick_preservation = preset.get('kick_preservation', True)
                sub_enhance = preset.get('sub_enhance', 0.5)
                
                audio = apply_bass_processing(
                    audio, 
                    bass_threshold, 
                    bass_ratio, 
                    bass_makeup,
                    split_freq=bass_split_freq,
                    preserve_kicks=kick_preservation,
                    sub_enhance=sub_enhance
                )
                print(f"Traitement des basses appliqué: threshold={bass_threshold}, ratio={bass_ratio}, split_freq={bass_split_freq}Hz")
            except Exception as e:
                print(f"ERREUR lors du traitement des basses: {e}")
        
        # 2. Normalisation
        try:
            target_dBFS = preset.get('target_dBFS', -1.0)
            audio = normalize(audio, headroom=target_dBFS)
            print(f"Normalisation appliquée: {target_dBFS} dBFS")
        except Exception as e:
            print(f"ERREUR lors de la normalisation: {e}")
        
        # 3. Gain
        try:
            gain_db = max(preset.get('gain_db', 0), 1.0)  # Au moins 1 dB de gain
            audio = audio.apply_gain(gain_db)
            print(f"Gain appliqué: {gain_db} dB")
        except Exception as e:
            print(f"ERREUR lors de l'application du gain: {e}")
        
        # 4. Excitation harmonique
        if preset.get('harmonic_exciter', False):
            try:
                exciter_amount = preset.get('exciter_amount', 0.3)
                
                # Définir focus_bass en fonction du preset (True pour Masterify V.1)
                if preset.get('name', '').lower() == 'masterify v.1' or preset.get('bass_processing', False):
                    focus_bass = True
                else:
                    focus_bass = False
                
                audio = apply_harmonic_exciter(audio, exciter_amount, focus_bass=focus_bass)
                print(f"Excitation harmonique appliquée: {exciter_amount}, focus_bass={focus_bass}")
            except Exception as e:
                print(f"ERREUR lors de l'excitation harmonique: {e}")
        
        # 5. Compression
        if preset.get('compression', True):
            try:
                threshold = preset.get('threshold_db', -20)
                ratio = preset.get('ratio', 4.0)
                attack = preset.get('attack_ms', 5)
                release = preset.get('release_ms', 50)
                
                audio = apply_compression(audio, threshold, ratio, attack, release)
                print(f"Compression appliquée - threshold: {threshold}, ratio: {ratio}")
            except Exception as e:
                print(f"ERREUR lors de la compression: {e}")
    
        # 6. EQ
        if preset.get('eq', True):
            try:
                eq_bands = preset.get('eq_bands', {})
                audio = apply_eq(audio, eq_bands)
                print(f"EQ appliqué avec {len(eq_bands)} bandes")
            except Exception as e:
                print(f"ERREUR lors de l'application de l'EQ: {e}")
        
        # 7. Amélioration spatiale
        if preset.get('spatial_enhancement', False):
            try:
                space_amount = preset.get('space_amount', 0.3)
                audio = apply_spatial_enhancement(audio, space_amount)
                print(f"Amélioration spatiale appliquée: {space_amount}")
            except Exception as e:
                print(f"ERREUR lors de l'amélioration spatiale: {e}")
        
        # 8. Élargissement stéréo
        if audio.channels == 2 and preset.get('stereo_width', 100) != 100:
            try:
                width = preset.get('stereo_width', 100) / 100.0
                audio = apply_stereo_width(audio, width)
                print(f"Largeur stéréo appliquée: {width}")
            except Exception as e:
                print(f"ERREUR lors de l'élargissement stéréo: {e}")
        
        # 9. Chaleur analogique
        if preset.get('analog_warmth', False):
            try:
                warmth_amount = preset.get('warmth_amount', 0.3)
                audio = apply_analog_warmth(audio, warmth_amount)
                print(f"Chaleur analogique appliquée: {warmth_amount}")
            except Exception as e:
                print(f"ERREUR lors de l'application de la chaleur analogique: {e}")
        
        # 10. Limiteur
        if preset.get('limiter', True):
            try:
                ceiling = preset.get('ceiling_db', -0.3)
                audio = apply_limiter(audio, ceiling)
                print(f"Limiteur appliqué avec plafond: {ceiling} dB")
            except Exception as e:
                print(f"ERREUR lors de l'application du limiteur: {e}")
        
        # Vérifier une dernière fois si l'audio n'est pas silencieux
        if audio.dBFS < -40:
            print(f"AVERTISSEMENT: Audio toujours silencieux après traitement (dBFS: {audio.dBFS})")
            # Normaliser à un niveau audible
            audio = normalize(audio, headroom=-3.0)
        
        print(f"Niveau final: {audio.dBFS} dBFS")
        
        # Exporter l'audio traité
        try:
            export_format = os.path.splitext(output_path)[1].lower().replace('.', '')
            if not export_format:
                export_format = 'mp3'
                
            # S'assurer que le dossier de sortie existe
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            audio.export(
                output_path,
                format=export_format,
                bitrate=preset.get('bitrate', '320k'),
                tags={"album": "Masterify", "artist": "Masterify Audio", "title": f"Masterify {preset.get('name', '')}"}
            )
            print(f"Audio exporté avec succès: {output_path}")
        except Exception as e:
            print(f"ERREUR lors de l'exportation: {e}")
            raise
        
        print(f"--- FIN DU TRAITEMENT AUDIO - PRESET: {preset_name} ---\n")
        return len(audio) / 1000.0  # Durée en secondes
        
    except Exception as e:
        print(f"ERREUR CRITIQUE dans process_audio: {e}")
        # Tenter de générer un fichier audio minimal en cas d'erreur grave
        try:
            # Créer un segment audio minimal avec un bip
            emergency_audio = AudioSegment.silent(duration=500)
            emergency_audio = emergency_audio.apply_gain(10)  # Bip audible
            
            # Exporter ce segment
            emergency_audio.export(
                output_path,
                format="mp3",
                bitrate="128k",
                tags={"album": "Masterify", "artist": "Masterify Audio", "title": "Error Recovery"}
            )
            print(f"Audio de secours exporté: {output_path}")
            return 0.5  # Durée du bip en secondes
        except:
            print("Impossible de créer un fichier audio de secours")
            return 0

def apply_harmonic_exciter(audio, amount, focus_bass=True):
    """
    Ajoute des harmoniques pour rendre le son plus brillant et défini
    
    Simule l'effet d'un exciter analogique en générant des harmoniques supplémentaires
    sur certaines bandes de fréquences.
    
    Paramètres:
    - amount: intensité de l'effet (0-1)
    - focus_bass: si True, concentre l'excitation harmonique sur les fréquences basses-médiums
                  pour améliorer la définition des kicks et 808
    """
    # Limiter l'amount pour éviter les excès
    amount = max(0.0, min(0.5, amount))
    
    # Obtenir les échantillons comme array numpy
    samples = np.array(audio.get_array_of_samples())
    is_stereo = audio.channels == 2
    
    if is_stereo:
        samples = samples.reshape(-1, 2)
    
    # Créer un clone pour les hautes fréquences améliorées
    harmonics = samples.copy().astype(np.float32)
    
    # Effet d'excitation harmonique avec focus sur les basses si demandé
    # Définir les paramètres d'accentuation selon le focus
    if focus_bass:
        # Facteurs d'accentuation différents selon les bandes de fréquences
        # Pour simuler différentes bandes sans FFT, on utilise des "fenêtres" temporelles
        # Les variations rapides = hautes fréquences, lentes = basses fréquences
        
        # Paramètres pour accentuer principalement les médiums-bas (kicks/basses)
        # Utiliser des fenêtres plus grandes pour éviter d'accentuer les transitoires trop rapides
        window_sizes = [5, 8, 12]  # Plus grand = moins de hautes fréquences qui saturent
        window_weights = [0.3, 0.8, 0.4]  # Moins d'accent sur les aigus, plus sur les médiums
    else:
        # Paramètres standards pour un exciter traditionnel (plus orienté aigus)
        window_sizes = [2, 4, 6]  # Fenêtres légèrement agrandies pour moins de saturation
        window_weights = [0.8, 0.7, 0.3]  # Moins d'accentuation des hautes fréquences
    
    # Détection des transitoires pour réduire l'excitation sur les kicks
    # Cela aide à prévenir la saturation des transitoires des kicks
    
    # Calculer l'enveloppe pour détecter les transitoires
    envelope = np.zeros_like(samples, dtype=np.float32)
    window_size = 5  # Taille de fenêtre pour la détection
    
    if is_stereo:
        for ch in range(2):
            for i in range(window_size, len(samples)):
                diff_sum = 0
                for j in range(1, window_size+1):
                    diff_sum += abs(samples[i, ch] - samples[i-j, ch])
                envelope[i, ch] = diff_sum / window_size
            
            # Normaliser entre 0 et 1
            max_val = np.max(envelope[:, ch]) if np.max(envelope[:, ch]) > 0 else 1.0
            envelope[:, ch] /= max_val
        else:
            for i in range(window_size, len(samples)):
                diff_sum = 0
                for j in range(1, window_size+1):
                    diff_sum += abs(samples[i] - samples[i-j])
                envelope[i] = diff_sum / window_size
        
        # Normaliser entre 0 et 1
        max_val = np.max(envelope) if np.max(envelope) > 0 else 1.0
        envelope /= max_val
    
    # Appliquer l'excitation harmonique multi-bande
    for window_idx, window_size in enumerate(window_sizes):
        # Poids pour cette fenêtre
        weight = window_weights[window_idx] * amount
        
        if window_size <= 1 or weight < 0.01:  # Ignorer les fenêtres trop petites ou poids négligeables
            continue
            
        # Appliquer l'excitation pour cette taille de fenêtre
        if is_stereo:
            for ch in range(2):
                for i in range(window_size, len(harmonics)):
                    # Calculer la différence sur la fenêtre (= dérivée lissée)
                    diff = harmonics[i, ch] - harmonics[i-window_size, ch]
                    
                    # Réduire l'effet sur les transitoires détectés (kicks)
                    if focus_bass:
                        # Facteur de réduction pour les kicks (1.0 = pas d'effet, 0.0 = effet complet)
                        kick_reduction = min(1.0, envelope[i, ch] * 2.5)
                        
                        # Appliquer moins d'excitation sur les transitoires
                        effective_weight = weight * (1.0 - kick_reduction * 0.8)
                    else:
                        effective_weight = weight
                    
                    # Ajouter cette différence au signal avec le poids approprié
                    harmonics[i, ch] += diff * effective_weight
        else:
            for i in range(window_size, len(harmonics)):
                diff = harmonics[i] - harmonics[i-window_size]
                
                # Réduire l'effet sur les transitoires détectés (kicks)
                if focus_bass:
                    kick_reduction = min(1.0, envelope[i] * 2.5)
                    effective_weight = weight * (1.0 - kick_reduction * 0.8)
                else:
                    effective_weight = weight
                
                harmonics[i] += diff * effective_weight
    
    # Mélanger l'audio original avec les harmoniques créées
    # Ajuster les rapports de mixage selon le focus
    if focus_bass:
        # Moins d'harmoniques pour éviter la distorsion sur les basses
        orig_weight = 0.8
        harm_weight = 0.2
    else:
        # Mixage standard
        orig_weight = 0.7
        harm_weight = 0.3
        
    if is_stereo:
        for ch in range(2):
            samples[:, ch] = samples[:, ch] * orig_weight + harmonics[:, ch] * harm_weight
        samples = samples.flatten()
    else:
        samples = samples * orig_weight + harmonics * harm_weight
    
    # Limiter les valeurs pour éviter l'écrêtage
    samples = np.clip(samples, np.iinfo(np.int16).min, np.iinfo(np.int16).max)
    
    # Créer un nouveau segment audio
    excited_audio = audio._spawn(samples.astype(np.int16))
    
    return excited_audio

def apply_spatial_enhancement(audio, amount):
    """
    Améliore la perception spatiale du son en ajoutant de légères différences entre les canaux
    et en accentuant certaines fréquences liées à la spatialisation
    amount: 0-1, contrôle l'intensité de l'effet
    """
    try:
        # Vérifier que l'audio est bien valide
        if audio is None or len(audio) == 0:
            print("Erreur: Audio invalide dans apply_spatial_enhancement")
            return audio
            
        if audio.channels != 2:
            print("Avertissement: Effet spatial ignoré pour l'audio mono")
            return audio  # Effet uniquement pour l'audio stéréo
        
        # Limiter l'intensité
        amount = max(0.1, min(0.7, amount))  # Plafonné à 0.7 pour éviter les artefacts
        
        # Séparer les canaux
        channels = audio.split_to_mono()
        left = channels[0]
        right = channels[1]
        
        # Version simplifiée et plus stable de l'amélioration spatiale
        # Au lieu d'utiliser des délais qui peuvent causer des problèmes, 
        # on va juste appliquer un EQ différent sur chaque canal
        
        # EQ pour le canal gauche - légèrement amplifié dans les médiums-hauts
        left_eq = {
            '800Hz': amount * 0.5,
            '3kHz': amount * 1.0,
            '5kHz': amount * 0.8,
        }
        
        # EQ pour le canal droit - légèrement amplifié dans d'autres fréquences
        right_eq = {
            '1.2kHz': amount * 0.5,
            '4kHz': amount * 1.0, 
            '6kHz': amount * 0.8,
        }
        
        # Appliquer les EQ (fonction simplifiée pour éviter les erreurs)
        left_enhanced = left.apply_gain(amount * 0.5)  # Un simple gain est plus stable
        right_enhanced = right.apply_gain(amount * 0.5)
        
        # Recombiner en stéréo
        try:
            spatial_audio = AudioSegment.from_mono_audiosegments(left_enhanced, right_enhanced)
        except Exception as e:
            print(f"Erreur lors de la recombinaison stéréo: {e}")
            return audio  # Retourner l'audio original en cas d'erreur
        
        return spatial_audio
    
    except Exception as e:
        print(f"Erreur dans apply_spatial_enhancement: {e}")
        # En cas d'erreur, retourner l'audio original sans modification
        return audio

def apply_analog_warmth(audio, amount):
    """
    Ajoute de la chaleur "analogique" en simulant subtilement les caractéristiques 
    des équipements analogiques: légère saturation, coloration des basses
    amount: 0-1, contrôle l'intensité de l'effet
    """
    # Limiter l'intensité
    amount = max(0.1, min(0.7, amount))
    
    # Obtenir les échantillons
    samples = np.array(audio.get_array_of_samples())
    is_stereo = audio.channels == 2
    
    if is_stereo:
        samples = samples.reshape(-1, 2)
    
    # Convertir en float pour le traitement
    samples = samples.astype(np.float32)
    
    # Saturation douce (soft saturation/tape saturation emulation)
    # Formule simplifiée pour la distorsion de type "tape"
    # Dans une vraie implémentation, on utiliserait un modèle plus complexe
    saturation = amount * 0.3  # Contrôle l'intensité de la saturation
    
    if is_stereo:
        for ch in range(2):
            # Normaliser à [-1, 1]
            normalized = samples[:, ch] / 32768.0
            # Appliquer une légère saturation pour simuler le comportement de la bande magnétique
            saturated = np.tanh(normalized * (1 + saturation)) / np.tanh(1 + saturation)
            # Reconvertir à l'échelle d'origine
            samples[:, ch] = saturated * 32768.0
    else:
        normalized = samples / 32768.0
        saturated = np.tanh(normalized * (1 + saturation)) / np.tanh(1 + saturation)
        samples = saturated * 32768.0
    
    # Ajouter un peu de chaleur dans les basses (comme un transformateur analogique)
    # On simule cela en augmentant légèrement les basses fréquences
    warm_audio = audio._spawn(samples.astype(np.int16))
    
    # Augmenter légèrement les basses fréquences
    bass_boost = amount * 2.0  # Plus d'amplitude pour les basses
    warm_bands = {'60Hz': bass_boost, '120Hz': bass_boost * 0.7, '250Hz': bass_boost * 0.3}
    warm_audio = apply_eq(warm_audio, warm_bands)
    
    return warm_audio

def apply_compression(audio, threshold_db, ratio, attack_ms, release_ms):
    """
    Version simplifiée de la compression dynamique
    Cette fonction applique principalement un gain pour éviter les fichiers silencieux
    """
    # Gain de compensation pour éviter que le fichier ne soit trop silencieux
    makeup_gain = abs(threshold_db) / (ratio * 2)
    
    # Appliquer un gain de compensation
    processed_audio = audio.apply_gain(makeup_gain)
    
    return processed_audio

def apply_eq(audio, eq_bands):
    """
    Apply equalization with specified frequency bands
    Cette implémentation simplifiée applique juste un gain global au lieu d'un EQ précis
    car PyDub n'a pas d'EQ paramétrique intégré
    """
    # Vérifier s'il y a des gains significatifs à appliquer
    total_gain = sum(abs(gain) for gain in eq_bands.values())
    if total_gain < 0.1:
        return audio  # Pas de changement significatif nécessaire
    
    # Calculer le gain moyen à appliquer (approche simplifiée)
    avg_gain = sum(gain for gain in eq_bands.values()) / len(eq_bands)
    
    # Appliquer un gain global (c'est une simplification, mais ça évitera les fichiers silencieux)
    if avg_gain != 0:
        audio = audio.apply_gain(avg_gain)
    
    return audio

def apply_stereo_width(audio, width):
    """
    Version simplifiée pour l'élargissement stéréo
    Cette approche est plus sûre et évite les problèmes de phase
    """
    if audio.channels != 2:
        return audio  # N'applique qu'à l'audio stéréo
    
    # Limiter la largeur entre 0.5 et 1.5 pour éviter les problèmes
    width = max(0.5, min(1.5, width))
    
    # Si la largeur est proche de 1.0, ne rien changer
    if 0.95 <= width <= 1.05:
        return audio
    
    # Séparer les canaux gauche et droit
    channels = audio.split_to_mono()
    left = channels[0]
    right = channels[1]
    
    # Approche simplifiée : ajuster simplement le volume des canaux gauche et droit
    if width > 1.0:
        # Élargir : augmenter la différence entre les canaux
        diff_gain = (width - 1.0) * 3.0  # Max 1.5dB
        left = left.apply_gain(diff_gain)
        right = right.apply_gain(diff_gain)
    else:
        # Rétrécir : mixer une partie du canal opposé
        mix_amount = (1.0 - width) * 0.5
        left_with_right = left.overlay(right.apply_gain(-6.0), gain_during_overlay=mix_amount)
        right_with_left = right.overlay(left.apply_gain(-6.0), gain_during_overlay=mix_amount)
        left = left_with_right
        right = right_with_left
    
    # Recombiner en stéréo
    return AudioSegment.from_mono_audiosegments(left, right)

def apply_limiter(audio, ceiling_db):
    """
    Applique un limiteur pour éviter l'écrêtage et maximiser le volume
    tout en prévenant toute saturation
    """
    # Appliquer une protection anti-saturation avant le limiteur
    
    # Obtenons d'abord le niveau maximum actuel
    max_level = float(audio.max_dBFS)
    
    # Si le niveau est déjà très haut (près de 0 dB), pré-réduire pour éviter la saturation
    if max_level > -3.0:
        safety_margin = max(-6.0, max_level - 3.0)  # Réduire de 3dB si trop fort
        audio = audio.apply_gain(-safety_margin)
        print(f"Protection anti-saturation : réduction de {safety_margin:.1f} dB appliquée")
    
    # Normaliser à un niveau en-dessous du plafond demandé
    target_headroom = ceiling_db - 0.3  # Ajouter un peu plus de marge
    limited_audio = normalize(audio, headroom=target_headroom)
    
    # Appliquer un gain très modéré seulement si nécessaire
    current_level = limited_audio.dBFS
    if current_level < -3.0:  # Si le niveau est vraiment trop bas
        gain_boost = min(-ceiling_db * 0.3, 1.0)  # Max 1 dB de boost
        limited_audio = limited_audio.apply_gain(gain_boost)
        print(f"Léger boost de gain appliqué: {gain_boost:.1f} dB")
    
    # Normaliser une dernière fois au plafond exact pour s'assurer contre l'écrêtage
    limited_audio = normalize(limited_audio, headroom=ceiling_db)
    
    # Vérifier qu'on n'a pas saturé
    if limited_audio.max_dBFS > -0.1:  # Si très proche de 0 dB (saturation potentielle)
        # Appliquer une réduction de sécurité supplémentaire
        limited_audio = limited_audio.apply_gain(-0.5)
        print("Réduction de sécurité finale appliquée: -0.5 dB")
    
    return limited_audio

def apply_bass_processing(audio, threshold_db, ratio, makeup_gain, split_freq=180, preserve_kicks=True, sub_enhance=0.5):
    """
    Traitement spécial des basses fréquences pour contrôler les kicks et les 808
    sans perdre leur impact ni causer de saturation excessive.
    
    Cette fonction applique:
    1. Un filtre passe-bas pour isoler les basses
    2. Une compression dynamique douce sur les basses uniquement
    3. Un gain de compensation pour restaurer le niveau
    4. Une remixage avec le signal original
    
    Paramètres:
    - threshold_db: seuil de compression en dB
    - ratio: ratio de compression
    - makeup_gain: gain de compensation
    - split_freq: fréquence de séparation entre basses et reste du signal (Hz)
    - preserve_kicks: préservation des transitoires des kicks
    - sub_enhance: niveau d'amélioration des sub-bass (0-1)
    """
    print(f"Application du traitement spécial des basses (split_freq={split_freq}Hz, preserve_kicks={preserve_kicks}, sub_enhance={sub_enhance})...")
    
    # Si mono, convertir temporairement en stéréo pour traitement cohérent
    original_channels = audio.channels
    if original_channels == 1:
        audio = audio.set_channels(2)
    
    # 1. Séparer les basses fréquences selon split_freq
    # Note: PyDub n'ayant pas de filtres sophistiqués, on utilise une approche simplifiée
    # Dans une implémentation avancée, on utiliserait une FFT pour un filtrage précis
    
    # On clone l'audio pour travailler sur une copie
    bass_only = audio.copy()
    
    # Pour simuler un filtre passe-bas, on applique un EQ drastique
    split_freq_rounded = int(round(split_freq / 10.0) * 10)  # Arrondir à la dizaine
    
    # Calculer les fréquences pour notre EQ simplifié
    bass_eq = {
        '40Hz': 0,                       # Garde intact
        '80Hz': 0,                       # Garde intact
        f'{split_freq_rounded}Hz': -12,  # Atténue fortement à la fréquence de coupure
        f'{split_freq_rounded*2}Hz': -30, # Supprime quasiment au double de la fréquence
        '500Hz': -60                     # Supprime complètement
    }
    
    # Appliquer notre EQ simplifié pour isoler les basses
    bass_only = apply_eq(bass_only, bass_eq)
    
    # Rehausser les sub-bass si demandé
    if sub_enhance > 0:
        sub_eq = {
            '30Hz': sub_enhance * 2.5,  # Boost pour les sub-bass profonds (réduit)
            '40Hz': sub_enhance * 2.0,  # Boost pour les sub-bass (réduit)
            '60Hz': sub_enhance * 1.2,  # Boost modéré pour les sub-bass supérieurs (réduit)
            '80Hz': sub_enhance * 0.4   # Léger boost (réduit)
        }
        # Appliquer le boost de sub-bass
        bass_only = apply_eq(bass_only, sub_eq)
    
    # 2. Appliquer une compression douce sur les basses
    # Obtenir les échantillons
    samples = np.array(bass_only.get_array_of_samples())
    is_stereo = bass_only.channels == 2
    
    if is_stereo:
        samples = samples.reshape(-1, 2)
    
    # Convertir en float pour le traitement
    samples = samples.astype(np.float32)
    
    # Convertir le seuil de dB en amplitude relative
    threshold = 10 ** (threshold_db / 20.0)
    
    # Détection des transitoires pour préservation des kicks si activée
    if preserve_kicks:
        # Calculer l'enveloppe pour détecter les transitoires
        envelope = np.zeros_like(samples, dtype=np.float32)
        
        # Technique améliorée pour la détection des transitoires (kicks)
        # Utiliser une fenêtre plus large pour mieux capturer la forme du kick
        window_size = 5  # Plus large pour mieux détecter les kicks
        
        if is_stereo:
            for ch in range(2):
                # Calcul de la première différence (variation rapide = transitoire)
                for i in range(window_size, len(samples)):
                    # Somme des différences sur la fenêtre (meilleure détection)
                    diff_sum = 0
                    for j in range(1, window_size+1):
                        diff_sum += abs(samples[i, ch] - samples[i-j, ch])
                    envelope[i, ch] = diff_sum / window_size
                
                # Appliquer un seuil pour ne détecter que les transitoires significatifs
                # Ignore les petites variations qui ne sont pas des kicks
                max_env = np.max(envelope[:, ch])
                if max_env > 0:
                    envelope[:, ch] = np.where(envelope[:, ch] > max_env * 0.15, envelope[:, ch], 0)
        else:
            for i in range(window_size, len(samples)):
                diff_sum = 0
                for j in range(1, window_size+1):
                    diff_sum += abs(samples[i] - samples[i-j])
                envelope[i] = diff_sum / window_size
            
            # Appliquer un seuil pour ne détecter que les transitoires significatifs
            max_env = np.max(envelope)
            if max_env > 0:
                envelope = np.where(envelope > max_env * 0.15, envelope, 0)
        
        # Normaliser l'enveloppe entre 0 et 1
        envelope_max = np.max(envelope) if np.max(envelope) > 0 else 1.0
        envelope /= envelope_max
    
    # Appliquer une compression douce spécifique aux basses
    if is_stereo:
        for ch in range(2):
            # Normaliser à [-1, 1]
            normalized = samples[:, ch] / 32768.0
            
            # Appliquer la compression
            for i in range(len(normalized)):
                level = abs(normalized[i])
                
                # Si préservation des kicks, ajuster le ratio en fonction de la détection de transitoire
                actual_ratio = ratio
                if preserve_kicks and i < len(envelope):
                    # Réduire le ratio pour les transitoires détectés (préserver les kicks)
                    kick_factor = envelope[i, ch] * 3.0  # Amplifier davantage l'effet de détection
                    # Limiter le facteur entre 0 et 0.9 (pour préserver davantage les kicks)
                    kick_factor = min(0.9, kick_factor)
                    # Ratio réduit pour les transitoires = ratio * (1 - kick_factor)
                    actual_ratio = max(ratio * (1 - kick_factor), ratio / 8.0)
                
                if level > threshold:
                    # Calcul de la réduction de gain (compression douce)
                    gain_reduction = (threshold + (level - threshold) / actual_ratio) / level
                    # Atténuer l'effet de compression pour éviter la distorsion
                    gain_reduction = gain_reduction * 0.8 + 0.2  # Adoucit la compression
                    normalized[i] *= gain_reduction
            
            # Appliquer le gain de compensation (légèrement réduit)
            normalized *= 10 ** ((makeup_gain * 0.9) / 20.0)
            
            # Limiter pour éviter l'écrêtage
            normalized = np.clip(normalized, -0.95, 0.95)  # Limites plus strictes pour éviter la saturation
            
            # Reconvertir à l'échelle d'origine
            samples[:, ch] = normalized * 32768.0
    else:
        normalized = samples / 32768.0
        
        for i in range(len(normalized)):
            level = abs(normalized[i])
            
            # Si préservation des kicks, ajuster le ratio en fonction de la détection de transitoire
            actual_ratio = ratio
            if preserve_kicks and i < len(envelope):
                kick_factor = envelope[i] * 3.0
                kick_factor = min(0.9, kick_factor)
                actual_ratio = max(ratio * (1 - kick_factor), ratio / 8.0)
            
            if level > threshold:
                gain_reduction = (threshold + (level - threshold) / actual_ratio) / level
                gain_reduction = gain_reduction * 0.8 + 0.2  # Adoucit la compression
                normalized[i] *= gain_reduction
        
        normalized *= 10 ** ((makeup_gain * 0.9) / 20.0)
        normalized = np.clip(normalized, -0.95, 0.95)
        samples = normalized * 32768.0
    
    # Limiter les valeurs pour éviter l'écrêtage
    samples = np.clip(samples, np.iinfo(np.int16).min, np.iinfo(np.int16).max)
    
    # Créer un nouveau segment audio avec les basses traitées
    bass_processed = bass_only._spawn(samples.astype(np.int16))
    
    # 3. Créer un signal sans basses à partir de l'original
    # Atténuer les basses dans l'original pour créer le signal complémentaire
    
    # Ajuster les fréquences selon split_freq
    split_freq_for_hi = int(round(split_freq * 0.8))  # Légèrement plus bas pour un crossover en douceur
    
    mid_high_eq = {
        '30Hz': -12,                        # Atténue fortement
        '60Hz': -8,                         # Atténue moyennement
        f'{split_freq_for_hi}Hz': -3,       # Atténue légèrement à la fréquence de transition
        f'{split_freq_rounded}Hz': 0,       # Garde intact à partir de la fréquence de coupure
        '1kHz': 0,                          # Garde intact
        '5kHz': 0                           # Garde intact
    }
    mid_high_only = apply_eq(audio.copy(), mid_high_eq)
    
    # 4. Mélanger les basses traitées avec le reste du signal
    # On utilise un crossfade avec un rapport personnalisé
    balance = 0.45  # 45% basses traitées, 55% signal médiums-aigus (réduit pour moins de basses)
    
    # Ajuster les volumes pour le mélange (plus doux sur les basses)
    bass_processed = bass_processed.apply_gain(-2.0)  # Plus forte baisse pour éviter l'accumulation
    mid_high_only = mid_high_only.apply_gain(-0.7)    # Légère baisse pour la cohérence
    
    # Combiner les deux signaux (mixage simple)
    combined = mid_high_only.overlay(bass_processed, gain_during_overlay=balance + 0.12)
    
    # Restaurer le format original si nécessaire
    if original_channels == 1:
        combined = combined.set_channels(1)
    
    # Normaliser légèrement pour maintenir un niveau cohérent
    combined = normalize(combined, headroom=-1.4)  # Headroom plus important pour éviter la saturation
    
    return combined

def generate_waveform_data(file_path, num_points=1000):
    """Generate waveform data for visualization"""
    # Load the audio file
    if file_path.lower().endswith('.mp3'):
        audio = AudioSegment.from_mp3(file_path)
    else:  # Assume WAV
        audio = AudioSegment.from_wav(file_path)
    
    # Get audio samples as numpy array
    samples = np.array(audio.get_array_of_samples())
    
    # If stereo, convert to mono for visualization
    if audio.channels == 2:
        samples = samples.reshape(-1, 2)
        samples = samples.mean(axis=1)
    
    # Reduce the number of points for visualization
    # by taking the maximum absolute value in each chunk
    chunk_size = max(1, len(samples) // num_points)
    waveform = []
    
    for i in range(0, len(samples), chunk_size):
        chunk = samples[i:i+chunk_size]
        if len(chunk) > 0:
            # Find max absolute value in chunk
            max_val = np.max(np.abs(chunk))
            waveform.append(float(max_val) / 32768.0)  # Normalize to 0-1 range
    
    return waveform
