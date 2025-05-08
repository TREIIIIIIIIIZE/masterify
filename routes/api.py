from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
import os
from datetime import datetime
from models import db, MasteredFile, User
from audio_processing.processor import generate_waveform_data
from audio_processing.matchering_processor import process_with_matchering, get_available_references, save_user_reference
from werkzeug.utils import secure_filename
import mimetypes

api_bp = Blueprint('api', __name__)

UPLOAD_FOLDER = 'temp_uploads'
PROCESSED_FOLDER = 'attached_assets'
ALLOWED_MIME_TYPES = {'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/x-pn-wav'}
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

def allowed_file(file):
    # Vérifie le mimetype
    if file.mimetype in ALLOWED_MIME_TYPES:
        return True
    # Vérifie l'extension si présente
    filename = file.filename
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        return True
    return False

@api_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files and 'audio' not in request.files and 'filepond' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    # Essayer de récupérer le fichier avec différents noms de paramètres possibles
    file = request.files.get('file') or request.files.get('audio') or request.files.get('filepond')
    if file is None or file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
    
    if not allowed_file(file):
        return jsonify({'success': False, 'message': 'File type not allowed. Please upload MP3 or WAV files only.'}), 400
    
    try:
        # On garde le nom original, mais on sécurise pour le stockage
        filename = secure_filename(file.filename) or 'audio_upload'
        # Ajoute l'extension si absente
        ext = ''
        if '.' in file.filename:
            ext = '.' + file.filename.rsplit('.', 1)[1].lower()
        else:
            # Déduit l'extension du mimetype
            guessed_ext = mimetypes.guess_extension(file.mimetype)
            if guessed_ext in ['.mp3', '.wav']:
                ext = guessed_ext
        if not ext:
            ext = '.mp3'  # fallback
        if not filename.endswith(ext):
            filename += ext
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)
        
        # Récupérer le type d'upload depuis la requête
        is_reference = request.form.get('is_reference') == 'true'
        
        if is_reference:
            # Sauvegarder comme référence utilisateur
            saved_reference = save_user_reference(temp_path, current_user.id)
            if saved_reference:
                return jsonify({
                    'success': True,
                    'filename': os.path.basename(saved_reference),
                    'original_filename': file.filename,
                    'message': 'Reference track uploaded successfully',
                    'is_reference': True
                })
            else:
                return jsonify({'success': False, 'message': 'Failed to save reference track'}), 500
        else:
            # Upload normal de piste à masteriser
            return jsonify({
                'success': True,
                'filename': filename,
                'original_filename': file.filename,
                'suggested_preset': 'masterify_v1',  # Masterify V.1 comme preset par défaut
                'message': 'File uploaded successfully'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload error: {str(e)}'}), 500

@api_bp.route('/api/process', methods=['POST'])
@login_required
def process_track():
    data = request.get_json()
    filename = data.get('filename')
    original_filename = data.get('original_filename')
    preset_name = data.get('preset')
    use_reference = data.get('use_reference', False)
    reference_file = data.get('reference_file')
    
    if not filename or not preset_name:
        return jsonify({'success': False, 'message': 'Missing filename or preset'}), 400

    # Chemins
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    processed_filename = f"mastered_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    output_path = os.path.join(PROCESSED_FOLDER, processed_filename)

    # Gestion crédits (illimités pour Studio ou pour bryanlerustre)
    if current_user.username == 'bryanlerustre':
        # Aucune vérification de crédits pour bryanlerustre (dev)
        pass
    elif (current_user.plan != 'studio') and (current_user.credits <= 0):
        return jsonify({'success': False, 'message': 'Not enough credits.'}), 403

    try:
        # Vérifier que le preset est valide (masterify_v1 ou masterify_ia)
        if preset_name not in ["masterify_v1", "masterify_ia"]:
            return jsonify({'success': False, 'message': 'Invalid preset. Choose Masterify V.1 or Masterify A.I.'}), 400
            
        # Chemin du fichier de référence si utilisé
        reference_path = None
        if use_reference and reference_file:
            reference_path = os.path.join('user_references', reference_file)
            if not os.path.exists(reference_path):
                return jsonify({'success': False, 'message': 'Reference file not found'}), 400
        
        # Traitement avec Matchering
        result = process_with_matchering(
            input_path, 
            preset_name,
            PROCESSED_FOLDER,
            original_filename,
            reference_path,
            use_reference
        )
        
        if not result.get('success'):
            return jsonify({'success': False, 'message': f'Processing error: {result.get("error")}'}), 500
            
        processed_filename = result.get('processed_filename')
        output_path = os.path.join(PROCESSED_FOLDER, processed_filename)
        file_id = result.get('file_id')
        duration = 0  # À implémenter: récupérer la durée du fichier
    except Exception as e:
        return jsonify({'success': False, 'message': f'Processing error: {str(e)}'}), 500

    # Décrémente crédits si pas Studio et pas le compte dev
    if current_user.username != 'bryanlerustre' and current_user.plan != 'studio':
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

# Route pour récupérer les références de l'utilisateur
@api_bp.route('/api/user_references', methods=['GET'])
@login_required
def get_user_references():
    # Chemin du répertoire des références utilisateur
    user_ref_dir = 'user_references'
    user_references = []
    
    # Récupérer toutes les références de l'utilisateur
    if os.path.exists(user_ref_dir):
        for file in os.listdir(user_ref_dir):
            if file.startswith(f'user_{current_user.id}_') and file.endswith('.mp3'):
                user_references.append({
                    'filename': file,
                    'path': os.path.join(user_ref_dir, file),
                    'date_added': datetime.fromtimestamp(os.path.getctime(os.path.join(user_ref_dir, file))).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return jsonify({
        'success': True,
        'references': user_references
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

@api_bp.route('/api/admin/add_credits', methods=['POST'])
@login_required
def admin_add_credits():
    """Route d'administration pour ajouter des crédits à un utilisateur (seulement pour le développeur)"""
    # Vérification que c'est bien le compte développeur
    if current_user.username != 'bryanlerustre':
        return jsonify({'success': False, 'message': 'Unauthorized. Admin access required.'}), 403
    
    data = request.get_json()
    email = data.get('email')
    credits = data.get('credits', 1)
    
    if not email:
        return jsonify({'success': False, 'message': 'Email required'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    user.credits += credits
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Added {credits} credits to {user.username} ({user.email})',
        'current_credits': user.credits
    }) 