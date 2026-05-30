from flask import Flask, render_template, jsonify, request
import subprocess
import sys
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

EVENT_PHOTOS_FOLDER = 'event_photos'

# --- 1. Main Dashboard Page ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

# --- 2. API Endpoint to Upload Event Photos ---
@app.route('/upload-photos', methods=['POST'])
def upload_photos():
    """Saves uploaded event photos."""
    if not os.path.exists(EVENT_PHOTOS_FOLDER):
        os.makedirs(EVENT_PHOTOS_FOLDER)
        
    if 'photos' not in request.files:
        return jsonify(status="error", message="No file part in the request")
        
    files = request.files.getlist('photos')
    
    if not files or files[0].filename == '':
        return jsonify(status="error", message="No files selected for uploading")

    filenames = []
    for file in files:
        if file:
            filename = secure_filename(file.filename)
            save_path = os.path.join(EVENT_PHOTOS_FOLDER, filename)
            file.save(save_path)
            filenames.append(filename)
            
    print(f"Uploaded {len(filenames)} files: {', '.join(filenames)}")
    return jsonify(status="success", message=f"Successfully uploaded {len(filenames)} photos.")

# --- 3. API Endpoint to Run Indexing ---
@app.route('/run-indexing', methods=['POST'])
def run_indexing():
    """Runs the 'create_index.py' script."""
    print("Received request to run face indexing...")
    try:
        result = subprocess.run(
            [sys.executable, 'create_index.py'],
            capture_output=True, text=True, check=True
        )
        print("Script output:", result.stdout)
        return jsonify(status="success", message="Face index created!", output=result.stdout)
    except subprocess.CalledProcessError as e:
        print("Script error:", e.stderr)
        return jsonify(status="error", message="Script failed!", output=e.stderr)

# --- 4. API Endpoint to Run Matching ---
@app.route('/run-matching', methods=['POST'])
def run_matching():
    """Runs the 'find_matches.py' script."""
    print("Received request to run face matching...")
    try:
        result = subprocess.run(
            [sys.executable, 'find_matches.py'],
            capture_output=True, text=True, check=True
        )
        print("Script output:", result.stdout)
        return jsonify(status="success", message="Face matching complete!", output=result.stdout)
    except subprocess.CalledProcessError as e:
        print("Script error:", e.stderr)
        return jsonify(status="error", message="Matching script failed!", output=e.stderr)

# --- 5. NEW: API Endpoint to Send Emails ---
@app.route('/send-emails', methods=['POST'])
def send_email_route():
    """Runs the 'send_emails.py' script."""
    print("Received request to send emails...")
    try:
        result = subprocess.run(
            [sys.executable, 'send_emails.py'],
            capture_output=True, text=True, check=True
        )
        print("Script output:", result.stdout)
        # Check stdout for the 401 error as well
        if "401" in result.stdout or "Unauthorized" in result.stdout:
             return jsonify(status="error", message="Emails failed to send! Check SendGrid API Key.", output=result.stdout)
            
        return jsonify(status="success", message="Emails sent successfully!", output=result.stdout)
    except subprocess.CalledProcessError as e:
        # This catches scripts that exit with an error
        print("Script error:", e.stderr)
        return jsonify(status="error", message="Email script failed!", output=e.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify(status="error", message=f"An unexpected error occurred: {e}")

# --- Run the app ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)