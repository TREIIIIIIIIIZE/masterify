import random
import numpy as np
from pydub import AudioSegment

# Preset definitions for audio mastering
PRESETS = {
    'clean': {
        'name': 'Clean',
        'description': 'Balanced mastering for acoustic and vocal-focused tracks',
        'normalize': True,
        'target_dBFS': -1.0,
        'gain_db': 0,
        'compression': True,
        'threshold_db': -20,
        'ratio': 2.5,
        'attack_ms': 5,
        'release_ms': 50,
        'eq': True,
        'eq_bands': {
            '60Hz': 1.0,    # Slight bass boost
            '120Hz': 0.5,   # Lower mids
            '500Hz': -0.5,  # Reduce mud
            '1kHz': 0.0,    # Flat mids
            '3kHz': 1.0,    # Presence
            '5kHz': 1.5,    # Detail
            '10kHz': 1.0,   # Air
            '16kHz': 0.5,   # Shimmer
        },
        'stereo_width': 110,  # Slight widening
        'limiter': True,
        'ceiling_db': -0.3,
        'bitrate': '320k'
    },
    
    'warm': {
        'name': 'Warm',
        'description': 'Rich low-end with smooth highs for organic sound',
        'normalize': True,
        'target_dBFS': -1.2,
        'gain_db': 0,
        'compression': True,
        'threshold_db': -18,
        'ratio': 3.0,
        'attack_ms': 10,
        'release_ms': 80,
        'eq': True,
        'eq_bands': {
            '60Hz': 2.0,    # Bass boost
            '120Hz': 1.5,   # Low end warmth
            '250Hz': 1.0,   # Body
            '500Hz': 0.0,   # Mid neutrality
            '1kHz': -0.5,   # Reduce harshness
            '3kHz': -1.0,   # Soften presence
            '5kHz': 0.0,    # Neutral detail
            '10kHz': -1.0,  # Reduce sibilance
            '16kHz': -1.5,  # Smooth air
        },
        'stereo_width': 105,  # Slight widening
        'limiter': True,
        'ceiling_db': -0.5,
        'bitrate': '320k'
    },
    
    'lofi': {
        'name': 'Lo-Fi',
        'description': 'Vintage character with subtle imperfections',
        'normalize': True,
        'target_dBFS': -2.0,
        'gain_db': -1.0,
        'compression': True,
        'threshold_db': -15,
        'ratio': 4.0,
        'attack_ms': 1,
        'release_ms': 30,
        'eq': True,
        'eq_bands': {
            '60Hz': -1.0,   # Reduce deep bass
            '120Hz': 2.0,   # Boost low mids
            '500Hz': 3.0,   # Boost mids for warmth
            '1kHz': 1.5,    # Presence
            '3kHz': -2.0,   # Reduce high mids
            '5kHz': -3.0,   # Dull the highs
            '10kHz': -4.0,  # Reduce high end
            '16kHz': -6.0,  # Cut air frequencies
        },
        'stereo_width': 90,   # Narrower stereo
        'limiter': True,
        'ceiling_db': -1.0,
        'bitrate': '192k'   # Lower quality for lo-fi aesthetic
    },
    
    'trap': {
        'name': 'Trap',
        'description': 'Heavy bass, punchy drums, and crisp highs',
        'normalize': True,
        'target_dBFS': -0.8,
        'gain_db': 1.0,
        'compression': True,
        'threshold_db': -12,
        'ratio': 5.0,
        'attack_ms': 1,
        'release_ms': 20,
        'eq': True,
        'eq_bands': {
            '40Hz': 4.0,    # Sub bass boost
            '60Hz': 3.0,    # Bass boost
            '120Hz': 2.0,   # Low end
            '250Hz': -1.0,  # Reduce mud
            '500Hz': -2.0,  # Clear mids
            '1kHz': 0.0,    # Neutral mids
            '3kHz': 2.0,    # Vocal presence
            '5kHz': 3.0,    # Crisp highs
            '10kHz': 2.0,   # Air
            '16kHz': 1.0,   # Extended highs
        },
        'stereo_width': 120,  # Wide stereo
        'limiter': True,
        'ceiling_db': -0.3,
        'bitrate': '320k'
    },
    
    'bright': {
        'name': 'Bright',
        'description': 'Clear and detailed with emphasized highs',
        'normalize': True,
        'target_dBFS': -1.0,
        'gain_db': 0.5,
        'compression': True,
        'threshold_db': -18,
        'ratio': 2.0,
        'attack_ms': 5,
        'release_ms': 40,
        'eq': True,
        'eq_bands': {
            '60Hz': 0.0,    # Neutral bass
            '120Hz': -0.5,  # Reduce low mids
            '500Hz': -1.0,  # Reduce mids
            '1kHz': 0.0,    # Neutral mids
            '3kHz': 2.0,    # Enhance presence
            '5kHz': 3.0,    # Boost detail
            '10kHz': 2.5,   # Air boost
            '16kHz': 2.0,   # Extended highs
        },
        'stereo_width': 115,  # Enhanced width
        'limiter': True,
        'ceiling_db': -0.3,
        'bitrate': '320k'
    }
}

def get_preset_by_name(name):
    """Get a preset by its name"""
    return PRESETS.get(name.lower())

def get_all_presets():
    """Get all available presets"""
    return PRESETS

def analyze_and_suggest_preset(file_path):
    """
    Analyze audio file and suggest an appropriate preset
    
    This is a simplified analysis that checks for:
    - Bass presence (suggests trap or warm)
    - Treble presence (suggests clean or bright)
    - Dynamics (suggests lofi if compressed)
    """
    try:
        # Load the audio file
        if file_path.lower().endswith('.mp3'):
            audio = AudioSegment.from_mp3(file_path)
        else:  # Assume WAV
            audio = AudioSegment.from_wav(file_path)
        
        # Get audio samples as numpy array
        samples = np.array(audio.get_array_of_samples())
        
        # If stereo, convert to mono for analysis
        if audio.channels == 2:
            samples = samples.reshape(-1, 2)
            samples = samples.mean(axis=1)
        
        # Normalize samples for analysis
        samples = samples / np.max(np.abs(samples))
        
        # Split audio into frequency bands using simple FFT
        fft = np.abs(np.fft.rfft(samples))
        freq = np.fft.rfftfreq(len(samples), 1.0/audio.frame_rate)
        
        # Determine band energy
        bass_mask = (freq < 250)
        mid_mask = (freq >= 250) & (freq < 2000)
        high_mask = (freq >= 2000)
        
        bass_energy = np.sum(fft[bass_mask])
        mid_energy = np.sum(fft[mid_mask])
        high_energy = np.sum(fft[high_mask])
        
        # Calculate dynamics (simplified)
        rms = np.sqrt(np.mean(samples**2))
        peak = np.max(np.abs(samples))
        crest_factor = peak / rms if rms > 0 else 1.0
        
        # Determine preset based on analysis
        if crest_factor < 3.0:  # Already compressed, likely lofi or trap
            if bass_energy > high_energy:
                return 'trap'
            else:
                return 'lofi'
        elif bass_energy > mid_energy and bass_energy > high_energy:  # Bass-heavy
            return 'warm'
        elif high_energy > bass_energy:  # Bright/detailed
            return 'bright'
        else:  # Balanced
            return 'clean'
            
    except Exception as e:
        print(f"Error analyzing audio: {e}")
        # Default to clean preset if analysis fails
        return 'clean'
