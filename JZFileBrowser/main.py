#!/usr/bin/env python3
import os
import shutil
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your-secret-key-here'  # Change this in production!

# Default configuration
DEFAULT_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
app.config['UPLOAD_FOLDER'] = DEFAULT_UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'md', 'py', 'html', 'css', 'js'}
app.config['CONFIG_FILE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.txt')

# Load custom upload folder if exists
def load_custom_path():
    if os.path.exists(app.config['CONFIG_FILE']):
        with open(app.config['CONFIG_FILE'], 'r') as f:
            custom_path = f.read().strip()
            if os.path.isdir(custom_path):
                app.config['UPLOAD_FOLDER'] = custom_path

load_custom_path()

# Custom template filters
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    return datetime.fromtimestamp(value).strftime(format)

@app.template_filter('filesizeformat')
def filesizeformat(value):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"

@app.template_filter('dirname')
def dirname_filter(path):
    return os.path.dirname(path)

@app.context_processor
def utility_processor():
    return dict(
        os_path=os.path,
        current_upload_folder=app.config['UPLOAD_FOLDER']
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_safe_path(basedir, path):
    return os.path.abspath(path).startswith(os.path.abspath(basedir))

# Routes
@app.route('/')
def index():
    try:
        base_dir = app.config['UPLOAD_FOLDER']
        path = request.args.get('path', '')
        full_path = os.path.normpath(os.path.join(base_dir, path))
        
        if not is_safe_path(base_dir, full_path):
            return render_template('error.html', message='Access denied'), 403
        
        if not os.path.exists(full_path):
            return render_template('error.html', message='Path not found'), 404
        
        items = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            try:
                items.append({
                    'name': item,
                    'is_dir': os.path.isdir(item_path),
                    'size': os.path.getsize(item_path) if not os.path.isdir(item_path) else 0,
                    'modified': os.path.getmtime(item_path),
                    'path': os.path.join(path, item)
                })
            except OSError:
                continue
        
        parent_dir = os.path.dirname(path) if path else None
        return render_template('index.html', 
                             items=sorted(items, key=lambda x: (not x['is_dir'], x['name'].lower())),
                             current_path=path,
                             parent_dir=parent_dir)
    except Exception as e:
        return render_template('error.html', message=str(e)), 500

@app.route('/change_path', methods=['GET', 'POST'])
def change_path():
    if request.method == 'POST':
        new_path = request.form.get('new_path', '').strip()
        
        if not new_path:
            flash('Path cannot be empty', 'error')
            return redirect(url_for('settings'))
        
        try:
            if not os.path.isdir(new_path):
                os.makedirs(new_path, exist_ok=True)
            
            # Save to config file
            with open(app.config['CONFIG_FILE'], 'w') as f:
                f.write(new_path)
            
            # Update current path
            app.config['UPLOAD_FOLDER'] = new_path
            flash('Path changed successfully!', 'success')
        except Exception as e:
            flash(f'Error changing path: {str(e)}', 'error')
        
        return redirect(url_for('settings'))
    
    return render_template('settings.html')

@app.route('/reset_path', methods=['POST'])
def reset_path():
    try:
        # Reset to default path
        if os.path.exists(app.config['CONFIG_FILE']):
            os.remove(app.config['CONFIG_FILE'])
        
        app.config['UPLOAD_FOLDER'] = DEFAULT_UPLOAD_FOLDER
        os.makedirs(DEFAULT_UPLOAD_FOLDER, exist_ok=True)
        flash('Path reset to default successfully!', 'success')
    except Exception as e:
        flash(f'Error resetting path: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/view/<path:filepath>')
def view_file(filepath):
    """File editor view"""
    full_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], filepath))
    
    # Security check
    if not full_path.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
        return render_template('error.html', message='Access denied'), 403
    
    if not os.path.isfile(full_path):
        return render_template('error.html', message='File not found'), 404
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return render_template('error.html', message='Cannot display binary file'), 400
    
    return render_template('editor.html',
                         filename=os.path.basename(filepath),
                         filepath=filepath,
                         content=content)

@app.route('/save/<path:filepath>', methods=['POST'])
def save_file(filepath):
    """Save edited file"""
    full_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], filepath))
    
    # Security check
    if not full_path.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
        return render_template('error.html', message='Access denied'), 403
    
    content = request.form.get('content', '')
    
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        flash('File saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving file: {str(e)}', 'error')
    
    return redirect(url_for('view_file', filepath=filepath))

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads"""
    path = request.form.get('path', '')
    full_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], path))
    
    # Security check
    if not full_path.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
        return render_template('error.html', message='Access denied'), 403
    
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index', path=path))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index', path=path))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        try:
            file.save(os.path.join(full_path, filename))
            flash('File uploaded successfully', 'success')
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'error')
    else:
        flash('File type not allowed', 'error')
    
    return redirect(url_for('index', path=path))

@app.route('/create', methods=['POST'])
def create_file():
    """Create new file or directory"""
    path = request.form.get('path', '')
    filename = request.form.get('filename', '').strip()
    full_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], path))
    
    # Security check
    if not full_path.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
        return render_template('error.html', message='Access denied'), 403
    
    if not filename:
        flash('Filename is required', 'error')
        return redirect(url_for('index', path=path))
    
    try:
        if request.form.get('type') == 'directory':
            os.makedirs(os.path.join(full_path, filename), exist_ok=False)
            flash('Directory created successfully', 'success')
        else:
            with open(os.path.join(full_path, filename), 'w') as f:
                f.write('')
            flash('File created successfully', 'success')
    except FileExistsError:
        flash('File or directory already exists', 'error')
    except Exception as e:
        flash(f'Error creating: {str(e)}', 'error')
    
    return redirect(url_for('index', path=path))

@app.route('/delete', methods=['POST'])
def delete_item():
    """Delete file or directory"""
    path = request.form.get('path', '')
    item_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], path))
    
    # Security check
    if not item_path.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
        return render_template('error.html', message='Access denied'), 403
    
    if not os.path.exists(item_path):
        flash('Item not found', 'error')
        return redirect(url_for('index'))
    
    try:
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
        flash('Item deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'error')
    
    return redirect(url_for('index', path=os.path.dirname(path)))

@app.route('/download/<path:filepath>')
def download_file(filepath):
    """Download file"""
    directory = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], os.path.dirname(filepath)))
    filename = os.path.basename(filepath)
    
    # Security check
    if not directory.startswith(os.path.abspath(app.config['UPLOAD_FOLDER'])):
        return render_template('error.html', message='Access denied'), 403
    
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == '__main__':
    # Create folders if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)