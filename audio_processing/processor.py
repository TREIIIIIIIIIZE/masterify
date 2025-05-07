import os
import numpy as np
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
    # Load the audio file
    if input_path.lower().endswith('.mp3'):
        audio = AudioSegment.from_mp3(input_path)
    else:  # Assume WAV
        audio = AudioSegment.from_wav(input_path)
    
    # Apply normalization if specified
    if preset.get('normalize', True):
        target_dBFS = preset.get('target_dBFS', -1.0)
        audio = normalize(audio, headroom=target_dBFS)
    
    # Apply gain
    gain_db = preset.get('gain_db', 0)
    if gain_db != 0:
        audio = audio.apply_gain(gain_db)
    
    # Apply compression
    if preset.get('compression', True):
        threshold = preset.get('threshold_db', -20)
        ratio = preset.get('ratio', 4.0)
        attack = preset.get('attack_ms', 5)
        release = preset.get('release_ms', 50)
        
        audio = apply_compression(audio, threshold, ratio, attack, release)
    
    # Apply EQ
    if preset.get('eq', True):
        eq_bands = preset.get('eq_bands', {})
        audio = apply_eq(audio, eq_bands)
        
    # Apply stereo widening if specified
    if preset.get('stereo_width', 100) != 100:
        width = preset.get('stereo_width', 100) / 100.0
        audio = apply_stereo_width(audio, width)
    
    # Apply limiter
    if preset.get('limiter', True):
        ceiling = preset.get('ceiling_db', -0.3)
        audio = apply_limiter(audio, ceiling)
    
    # Export the processed audio
    export_format = os.path.splitext(output_path)[1].lower().replace('.', '')
    if not export_format:
        export_format = 'mp3'
        
    audio.export(
        output_path,
        format=export_format,
        bitrate=preset.get('bitrate', '320k'),
        tags={"album": "Masterify", "artist": "Masterify Audio"}
    )
    
    return len(audio) / 1000.0  # Duration in seconds

def apply_compression(audio, threshold_db, ratio, attack_ms, release_ms):
    """Apply dynamic range compression to audio"""
    # This is a simplified implementation of compression
    # For production use, more sophisticated algorithms would be used
    
    # Get audio samples as numpy array
    samples = np.array(audio.get_array_of_samples())
    sample_rate = audio.frame_rate
    channels = audio.channels
    
    # Convert to float32 for processing
    samples = samples.astype(np.float32)
    if channels == 2:
        samples = samples.reshape(-1, 2)
    
    # Calculate threshold in linear scale
    threshold = 10 ** (threshold_db / 20.0)
    
    # Calculate attack and release rates
    attack_coef = np.exp(-1.0 / (sample_rate * attack_ms / 1000.0))
    release_coef = np.exp(-1.0 / (sample_rate * release_ms / 1000.0))
    
    # Apply compression
    for i in range(1, len(samples)):
        # Detect signal level (simplified)
        if channels == 2:
            level = max(abs(samples[i][0]), abs(samples[i][1]))
        else:
            level = abs(samples[i])
        
        # Apply compression if level is above threshold
        if level > threshold:
            # Calculate compression gain
            gain_reduction = (threshold + (level - threshold) / ratio) / level
            
            # Apply compression with attack/release
            if gain_reduction < 1.0:
                if channels == 2:
                    samples[i] = samples[i] * gain_reduction
                else:
                    samples[i] *= gain_reduction
    
    # Convert back to the original format
    if channels == 2:
        samples = samples.flatten()
    
    samples = samples.astype(np.int16)
    
    # Create new audio segment from processed samples
    processed_audio = audio._spawn(samples)
    
    return processed_audio

def apply_eq(audio, eq_bands):
    """Apply equalization with specified frequency bands"""
    # Apply each EQ band
    for band, gain in eq_bands.items():
        # Convert band string to frequency (e.g., '100Hz' -> 100)
        if isinstance(band, str):
            freq = int(''.join(filter(str.isdigit, band)))
        else:
            freq = band
            
        # Apply band-specific EQ
        if gain != 0:
            audio = audio.low_pass_filter(freq) if gain > 0 else audio.high_pass_filter(freq)
            audio = audio.apply_gain(gain)
    
    return audio

def apply_stereo_width(audio, width):
    """Apply stereo widening/narrowing effect"""
    if audio.channels != 2:
        return audio  # Only applies to stereo audio
    
    # Split into left and right channels
    left = audio.split_to_mono()[0]
    right = audio.split_to_mono()[1]
    
    # Calculate mid and side components
    mid = left.overlay(right)
    mid = mid.apply_gain(-3)  # -3dB to maintain energy
    
    # Create side component by inverting right channel and mixing with left
    inverted_right = right.invert_phase()
    side = left.overlay(inverted_right)
    side = side.apply_gain(-3)  # -3dB to maintain energy
    
    # Apply width factor to side component
    side = side.apply_gain(width * 6 - 3)  # Scale width factor
    
    # Recombine mid and side to stereo
    left_new = mid.overlay(side)
    inverted_side = side.invert_phase()
    right_new = mid.overlay(inverted_side)
    
    # Create new stereo audio
    stereo = AudioSegment.from_mono_audiosegments(left_new, right_new)
    
    return stereo

def apply_limiter(audio, ceiling_db):
    """Apply a limiter to prevent clipping"""
    # Normalize to the ceiling level
    return normalize(audio, headroom=ceiling_db)

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
