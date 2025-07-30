import os, sys
from pathlib import Path
import platform
from datetime import datetime
from collections import defaultdict
import traceback
import threading
import time
from flask import Flask, request, send_file, jsonify, make_response
from flask_cors import CORS
import uuid

backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from src.pdf.constructor import PDF_Constructor
from src.seeds import *

app = Flask(__name__)

CORS(app, resources={
    r"/*": {
        "origins": ["https://whatsapp-wrapped-delta.vercel.app", "http://localhost:8080"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Disposition", "Content-Type", "X-Request-ID"]
    }
})

TEMP_DIR = '/tmp' if os.getenv('RENDER') else str(Path(__file__).parent.parent / 'temp')
PDF_DIR = '/tmp' if os.getenv('RENDER') else str(Path(__file__).parent.parent / 'pdfs')

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

SERVER_START_TIME = datetime.now()

# pdf_progress stores the progress of the PDF generation
pdf_progress = defaultdict(lambda: {
    "progress": 0,
    "status": "not_started",
    "pdf_path": None
})

def generate_pdf(request_id, file_path, lang):
    """Background thread to generate the PDF
    request_id: the id of the request
    file_path: the path of the file to generate the PDF from
    lang: the language of the PDF
    """

    try:
        pdf_progress[request_id]["status"] = "generating"
        
    
        pdf = PDF_Constructor(file_path, lang=lang)
        seed1(pdf)
        
        # Continuously update progress while generating
        while pdf_progress[request_id]["status"] == "generating":
            current_progress = pdf.load
            if current_progress >= 99:  
                break
            pdf_progress[request_id]["progress"] = current_progress
            time.sleep(0.5)
            
        pdf_progress[request_id]["status"] = "finalizing"
        pdf_progress[request_id]["progress"] = 99
        
        pdf_path = pdf.save()
        
        # Store the PDF path and set final progress
        pdf_progress[request_id].update({
            "status": "completed",
            "progress": 100, 
            "pdf_path": pdf_path
        })
        
    except Exception as e:
        pdf_progress[request_id].update({
            "status": "error",
            "error": str(e)
        })
    finally:
        # Cleanup input file
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/generate")
def generate():
    """
    Main function to generate the PDF
    """
    try:
        if 'chat' not in request.files:
            return jsonify({'error': 'No chat file provided'}), 400
            
        f = request.files["chat"]
        lang = request.form.get("lang", "en")
        
        request_id = str(uuid.uuid4())

        pdf_progress[request_id] = {
            "progress": 0,
            "status": "starting",
            "pdf_path": None
        }
        
        # Preserve original filename, ensuring it matches expected format
        original_filename = f.filename
        if not any(pattern in original_filename for pattern in ["Chat WhatsApp con", "Chat_WhatsApp_con_", "WhatsApp Chat -"]):
            # If filename doesn't match expected format, rename it to match
            original_filename = f"Chat WhatsApp con {original_filename}"
        
        tmp_path = os.path.join(TEMP_DIR, original_filename)
        f.save(tmp_path)
        
        # Start PDF generation in background thread
        thread = threading.Thread(
            target=generate_pdf,
            args=(request_id, tmp_path, lang),
            daemon=True
        )
        thread.start()
        
        # Return the request ID to identify the request
        response = jsonify({
            'request_id': request_id,
            'status': 'processing'
        })
        response.headers['X-Request-ID'] = request_id
        return response
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.get("/progress/<request_id>")
def get_progress(request_id):
    """Get the progress of the PDF generation"""
    if request_id not in pdf_progress:
        return jsonify({
            "error": "Request ID not found"
        }), 404
        
    progress_data = pdf_progress[request_id].copy()
    
    # Remove internal data before sending
    if "pdf_path" in progress_data:
        del progress_data["pdf_path"]
        
    return jsonify(progress_data)

@app.get("/download/<request_id>")
def download_pdf(request_id):
    """Download the PDF"""
    if request_id not in pdf_progress:
        return jsonify({
            "error": "PDF not found"
        }), 404
        
    progress_data = pdf_progress[request_id]
    
    if progress_data["status"] != "completed":
        return jsonify({
            "error": "PDF generation not completed"
        }), 400
        
    if not progress_data["pdf_path"] or not os.path.exists(progress_data["pdf_path"]):
        return jsonify({
            "error": "PDF file not found"
        }), 404
        
    pdf_path = progress_data["pdf_path"]
    
    del pdf_progress[request_id]
    
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=os.path.basename(pdf_path)
    )

@app.get("/health")
def health():
    temp_ok = os.path.exists(TEMP_DIR) and os.access(TEMP_DIR, os.W_OK)
    pdf_ok = os.path.exists(PDF_DIR) and os.access(PDF_DIR, os.W_OK)

    return jsonify({
        'status': 'ok' if temp_ok and pdf_ok else 'error',
        'environment': os.getenv('FLASK_ENV', 'development'),
        'server_uptime': str(datetime.now() - SERVER_START_TIME),
    })

if __name__ == "__main__":
    # For local development
    app.run(debug=True, port=5000)