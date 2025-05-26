import os
from werkzeug.utils import secure_filename
from flask import current_app

def save_uploaded_file(file, subfolder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        
        # Create directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return filename
    return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_unique_filename(filename, subfolder):
    base, ext = os.path.splitext(filename)
    counter = 1
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    
    while os.path.exists(os.path.join(upload_folder, filename)):
        filename = f"{base}_{counter}{ext}"
        counter += 1
    
    return filename