import os, sys
from pathlib import Path
import platform
from datetime import datetime

# Add the backend directory to Python path
backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from flask import Flask, request, send_file, jsonify, make_response
from flask_cors import CORS
from src.pdf.constructor import PDF_Constructor
import uuid

app = Flask(__name__)

# Configure CORS based on environment
CORS(app, resources={
    r"/*": {
        "origins": ["https://whatsapp-wrapped-delta.vercel.app", "http://localhost:8080"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Disposition", "Content-Type"]
    }
})

# Configure temporary directories
TEMP_DIR = '/tmp' if os.getenv('RENDER') else str(Path(__file__).parent.parent / 'temp')
PDF_DIR = '/tmp' if os.getenv('RENDER') else str(Path(__file__).parent.parent / 'pdfs')

# Create directories if they don't exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# Track server start time
SERVER_START_TIME = datetime.now()

@app.post("/generate")
def generate():
    try:
        if 'chat' not in request.files:
            return jsonify({'error': 'No chat file provided'}), 400
            
        f = request.files["chat"]
        lang = request.form.get("lang", "en")
        
        # Save uploaded file
        tmp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.txt")
        f.save(tmp_path)
        
        # Generate PDF
        pdf = PDF_Constructor(tmp_path, lang=lang)
        from src.seeds import seed1
        seed1(pdf)
        pdf_path = pdf.save()
        
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
        # Create response with PDF file
        response = make_response(send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name="whatsapp_wrapped.pdf"
        ))
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition, Content-Type'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")  # Log the error
        return jsonify({'error': str(e)}), 500

@app.get("/health")
def health():
    # Check if temp directories exist and are writable
    temp_ok = os.path.exists(TEMP_DIR) and os.access(TEMP_DIR, os.W_OK)
    pdf_ok = os.path.exists(PDF_DIR) and os.access(PDF_DIR, os.W_OK)
    
    # Calculate uptime
    uptime = datetime.now() - SERVER_START_TIME
    
    return jsonify({
        'status': 'ok' if temp_ok and pdf_ok else 'error',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'python_version': platform.python_version(),
        'server_uptime': str(uptime),
        'temp_directory': {
            'path': TEMP_DIR,
            'exists': os.path.exists(TEMP_DIR),
            'writable': os.access(TEMP_DIR, os.W_OK)
        },
        'pdf_directory': {
            'path': PDF_DIR,
            'exists': os.path.exists(PDF_DIR),
            'writable': os.access(PDF_DIR, os.W_OK)
        }
    })

if __name__ == "__main__":
    # For local development
    app.run(debug=True, port=5000)