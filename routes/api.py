from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
import os
from datetime import datetime
from models import db, MasteredFile
from audio_processing.processor import process_audio, generate_waveform_data
from audio_processing.presets import get_preset_by_name

api_bp = Blueprint('api', __name__)

UPLOAD_FOLDER = 'temp_uploads'
PROCESSED_FOLDER = 'attached_assets'

@api_bp.route('/api/process', methods=['POST'])
@login_required
def process_track():
    data = request.get_json()
    filename = data.get('filename')
    original_filename = data.get('original_filename')
    preset_name = data.get('preset')
    if not filename or not preset_name:
        return jsonify({'success': False, 'message': 'Missing filename or preset'}), 400

    # Chemins
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    processed_filename = f"mastered_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    output_path = os.path.join(PROCESSED_FOLDER, processed_filename)

    # Récupère le preset
    preset = get_preset_by_name(preset_name)
    if not preset:
        return jsonify({'success': False, 'message': 'Invalid preset'}), 400

    # Gestion crédits (illimités pour Studio)
    if (current_user.plan != 'studio') and (current_user.credits <= 0):
        return jsonify({'success': False, 'message': 'Not enough credits.'}), 403

    # Traitement audio
    try:
        duration = process_audio(input_path, output_path, preset)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Processing error: {str(e)}'}), 500

    # Décrémente crédits si pas Studio
    if current_user.plan != 'studio':
        current_user.credits -= 1
    
    # Sauvegarde en base
    mastered = MasteredFile(
        user_id=current_user.id,
        original_filename=original_filename,
        processed_filename=processed_filename,
        preset_used=preset_name,
        created_at=datetime.utcnow(),
        file_path=output_path,
        file_size=os.path.getsize(output_path),
        duration=duration
    )
    db.session.add(mastered)
    db.session.commit()

    return jsonify({
        'success': True,
        'file_id': mastered.id,
        'processed_filename': processed_filename,
        'credits_remaining': current_user.credits
    })

@api_bp.route('/api/download/<int:file_id>')
@login_required
def download_file(file_id):
    mastered = MasteredFile.query.get_or_404(file_id)
    if mastered.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    mastered.increment_download()
    db.session.commit()
    return send_file(mastered.file_path, as_attachment=True, download_name=mastered.processed_filename)

@api_bp.route('/api/waveform/<filename>')
@login_required
def get_waveform(filename):
    file_path = os.path.join(PROCESSED_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    waveform = generate_waveform_data(file_path, num_points=200)
    return jsonify({'success': True, 'waveform': waveform}) 