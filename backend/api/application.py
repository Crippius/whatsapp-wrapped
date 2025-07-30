import os, sys
from pathlib import Path

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
if os.getenv('FLASK_ENV') == 'production':
    # In production, allow requests from your Vercel frontend
    CORS(app, resources={
        r"/*": {
            "origins": ["https://whatsapp-wrapped-delta.vercel.app"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Disposition"]
        }
    })
else:
    # In development, allow requests from localhost
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:8080"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Disposition"]
        }
    })

# Configure temporary directories
TEMP_DIR = '/tmp' if os.getenv('RENDER') else str(Path(__file__).parent.parent / 'temp')
PDF_DIR = '/tmp' if os.getenv('RENDER') else str(Path(__file__).parent.parent / 'pdfs')

# Create directories if they don't exist
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

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
        origin = request.headers.get('Origin')
        if origin in ['https://whatsapp-wrapped-delta.vercel.app', 'http://localhost:8080']:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")  # Log the error
        return jsonify({'error': str(e)}), 500

@app.get("/health")
def health():
    return jsonify(status="ok", 
                  env=os.getenv('FLASK_ENV', 'development'),
                  temp_dir=TEMP_DIR)

if __name__ == "__main__":
    # For local development
    app.run(debug=True, port=5000)