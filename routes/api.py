import os
import uuid
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from models import MasteredFile
from audio_processing.processor import process_audio
from audio_processing.presets import get_preset_by_name, analyze_and_suggest_preset
from utils.file_management import clean_old_files, allowed_file

api_bp = Blueprint('api', __name__)

# Set up upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'temp_uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed audio file extensions
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

@api_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload an audio file for mastering"""
    # Check if the user has enough credits
    if current_user.credits <= 0:
        return jsonify({
            'success': False,
            'message': 'Not enough credits. Please purchase more credits to continue.'
        }), 402
    
    # Check if file is in the request
    if 'audio' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['audio']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    # Check if file is allowed
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        return jsonify({'success': False, 'message': 'File type not supported. Please upload MP3 or WAV files.'}), 400
    
    # Generate secure filename with UUID to avoid conflicts
    original_filename = secure_filename(file.filename)
    filename_parts = os.path.splitext(original_filename)
    unique_filename = f"{filename_parts[0]}_{uuid.uuid4().hex}{filename_parts[1]}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    # Save the file
    file.save(file_path)
    
    # Clean old files
    clean_old_files(UPLOAD_FOLDER, hours=24)
    
    # Analyze audio and suggest preset
    suggested_preset = analyze_and_suggest_preset(file_path)
    
    return jsonify({
        'success': True,
        'message': 'File uploaded successfully',
        'filename': unique_filename,
        'original_filename': original_filename,
        'suggested_preset': suggested_preset
    })

@api_bp.route('/process', methods=['POST'])
@login_required
def process_file():
    """Process an uploaded audio file with a selected preset"""
    data = request.get_json()
    filename = data.get('filename')
    preset_name = data.get('preset', 'clean')
    
    if not filename:
        return jsonify({'success': False, 'message': 'No filename provided'}), 400
    
    # Check if file exists
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    # Check if the user has enough credits
    if current_user.credits <= 0:
        return jsonify({
            'success': False,
            'message': 'Not enough credits. Please purchase more credits to continue.'
        }), 402
        
    # Get the preset
    preset = get_preset_by_name(preset_name)
    if not preset:
        return jsonify({'success': False, 'message': 'Invalid preset'}), 400
    
    # Use a credit
    current_user.use_credit()
    
    # Process the audio file
    try:
        processed_filename = f"mastered_{os.path.splitext(filename)[0]}_{uuid.uuid4().hex}.mp3"
        processed_path = os.path.join(UPLOAD_FOLDER, processed_filename)
        
        # Process audio with the selected preset
        duration = process_audio(file_path, processed_path, preset)
        
        # Save to database
        original_filename = data.get('original_filename', filename)
        mastered_file = MasteredFile(
            user_id=current_user.id,
            original_filename=original_filename,
            processed_filename=processed_filename,
            preset_used=preset_name,
            file_path=processed_path,
            file_size=os.path.getsize(processed_path),
            duration=duration
        )
        
        db.session.add(mastered_file)
        db.session.commit()
        
        # Return success response
        return jsonify({
            'success': True,
            'message': 'Audio processed successfully',
            'file_id': mastered_file.id,
            'processed_filename': processed_filename,
            'credits_remaining': current_user.credits
        })
        
    except Exception as e:
        # Refund the credit if processing fails
        current_user.add_credits(1)
        db.session.commit()
        
        return jsonify({
            'success': False,
            'message': f'Error processing audio: {str(e)}'
        }), 500

@api_bp.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download_file(file_id):
    """Download a processed audio file"""
    # Get the file from database
    mastered_file = db.session.query(MasteredFile).filter_by(id=file_id, user_id=current_user.id).first()
    
    if not mastered_file:
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    # Increment download counter
    mastered_file.increment_download()
    db.session.commit()
    
    # Send the file
    return send_from_directory(
        UPLOAD_FOLDER, 
        mastered_file.processed_filename,
        as_attachment=True,
        download_name=f"masterify_{mastered_file.original_filename}"
    )

@api_bp.route('/files', methods=['GET'])
@login_required
def get_user_files():
    """Get all processed files for the current user"""
    mastered_files = db.session.query(MasteredFile).filter_by(user_id=current_user.id).order_by(MasteredFile.created_at.desc()).all()
    
    files = [{
        'id': file.id,
        'original_filename': file.original_filename,
        'processed_filename': file.processed_filename,
        'preset_used': file.preset_used,
        'created_at': file.created_at.isoformat(),
        'file_size': file.file_size,
        'duration': file.duration,
        'download_count': file.download_count
    } for file in mastered_files]
    
    return jsonify({
        'success': True,
        'files': files
    })

@api_bp.route('/waveform/<filename>', methods=['GET'])
def get_waveform(filename):
    """Get waveform data for an audio file"""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'File not found'}), 404
    
    try:
        from audio_processing.processor import generate_waveform_data
        waveform_data = generate_waveform_data(file_path)
        
        return jsonify({
            'success': True,
            'waveform': waveform_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating waveform: {str(e)}'
        }), 500
