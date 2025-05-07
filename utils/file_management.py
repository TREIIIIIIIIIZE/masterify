import os
import shutil
from datetime import datetime, timedelta

def allowed_file(filename, allowed_extensions):
    """Check if a file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def clean_old_files(directory, hours=24):
    """Delete files older than the specified hours"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Check file modification time
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        if file_mod_time < cutoff_time:
            try:
                os.remove(file_path)
                print(f"Removed old file: {file_path}")
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")

def ensure_directory_exists(directory):
    """Ensure that a directory exists, creating it if necessary"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
