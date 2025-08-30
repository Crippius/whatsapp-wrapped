import os, sys

os.environ["MPLBACKEND"] = "Agg"  # Use non-interactive backend for matplotlib
import warnings

warnings.simplefilter("ignore")  # Ignore all warnings

import uuid
import time
import traceback
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from flask_cors import CORS
from flask import Flask, request, send_file, jsonify, Response

import matplotlib

matplotlib.use("Agg", force=True)
matplotlib.set_loglevel("critical")

backend_dir = str(Path(__file__).parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from src.seeds import *
from src.pdf.constructor import PDF_Constructor
from src.db import init_db, save_pdf_generation, save_chat_analytics


SERVER_START_TIME = datetime.now()

TEMP_DIR = "/tmp" if os.getenv("RENDER") else str(Path(__file__).parent.parent / "temp")
PDF_DIR = "/tmp" if os.getenv("RENDER") else str(Path(__file__).parent.parent / "pdfs")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

app = Flask(__name__)

# Enable CORS for specified origins
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://whatsapp-wrapped-delta.vercel.app",
                "http://localhost:8080",
                "http://whatsapp-wrapped.it",
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
            "expose_headers": ["Content-Disposition", "Content-Type", "X-Request-ID"],
        }
    },
)

# Database setup
init_db()

# pdf_progress stores the progress of the PDF generation
pdf_progress = defaultdict(
    lambda: {"progress": 0, "status": "not_started", "pdf_path": None}
)


def monitor_progress(request_id: str, pdf: PDF_Constructor) -> None:
    """Monitor the progress of PDF generation in a separate thread
    :param request_id: the id of the request
    :param pdf: the PDF_Constructor instance
    """
    try:
        while pdf_progress[request_id]["status"] == "generating":
            current_progress = pdf.load
            pdf_progress[request_id]["progress"] = current_progress
            print(f"[{request_id}] Current progress: {current_progress}%")
            if current_progress >= 99:
                break
            time.sleep(0.5)
    except Exception as e:
        print(
            f"[{request_id}] Progress monitoring error: {str(e)}\n{traceback.format_exc()}"
        )


def generate_pdf(request_id: str, file_path: str, lang: str) -> None:
    """Background thread to generate the PDF
    :param request_id: the id of the request
    :param file_path: the path of the file to generate the PDF from
    :param lang: the language of the PDF
    """
    print(
        f"[{request_id}] Starting PDF generation for file: {os.path.basename(file_path)}, language: {lang}"
    )
    start_time = time.time()
    try:
        pdf_progress[request_id]["status"] = "generating"

        pdf = PDF_Constructor(file_path, lang=lang)

        # Start progress monitoring in a separate thread
        monitor_thread = threading.Thread(
            target=monitor_progress, args=(request_id, pdf), daemon=True
        )
        monitor_thread.start()

        # Actual PDF generation steps
        seed1(pdf)

        print(f"[{request_id}] PDF processing complete, finalizing")
        pdf_progress[request_id]["status"] = "finalizing"
        pdf_progress[request_id]["progress"] = 99

        pdf_path = pdf.save()

        # Store the PDF path and set final progress
        pdf_progress[request_id].update(
            {"status": "completed", "progress": 100, "pdf_path": pdf_path}
        )

        # Store analytics
        try:
            processing_ms = int((time.time() - start_time) * 1000)
            save_pdf_generation(
                request_id=request_id,
                language=lang,
                status="completed",
                processing_time_ms=processing_ms,
                error=None,
            )
            analytics = pdf.get_analytics()
            save_chat_analytics(request_id, analytics)

        except Exception as analytics_err:
            print(
                f"[{request_id}] Analytics/DB save error: {str(analytics_err)}\n{traceback.format_exc()}"
            )

    except Exception as e:
        pdf_progress[request_id].update({"status": "error", "error": str(e)})
        try:
            processing_ms = int((time.time() - start_time) * 1000)
            save_pdf_generation(
                request_id=request_id,
                language=lang,
                status="error",
                processing_time_ms=processing_ms,
                error=str(e),
            )
        except Exception as status_err:
            print(
                f"[{request_id}] Status save error: {str(status_err)}\n{traceback.format_exc()}"
            )
    finally:
        # Cleanup input file
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/generate")
def generate() -> Response:
    """
    Main function to generate the PDF

    :return: JSON response with request ID and status
    """
    try:
        if "chat" not in request.files:
            return jsonify({"error": "No chat file provided"}), 400

        f = request.files["chat"]
        lang = request.form.get("lang", "en")

        request_id = str(uuid.uuid4())

        pdf_progress[request_id] = {
            "progress": 0,
            "status": "starting",
            "pdf_path": None,
        }

        tmp_path = os.path.join(TEMP_DIR, f.filename)
        f.save(tmp_path)

        # Start PDF generation in background thread
        thread = threading.Thread(
            target=generate_pdf, args=(request_id, tmp_path, lang), daemon=True
        )
        thread.start()

        # Return the request ID to identify the request
        response = jsonify({"request_id": request_id, "status": "processing"})
        response.headers["X-Request-ID"] = request_id
        return response

    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.get("/progress/<request_id>")
def get_progress(request_id: str) -> Response:
    """Get the progress of the PDF generation

    :param request_id: the id of the request
    :return: JSON response with progress details"""
    if request_id not in pdf_progress:
        return jsonify({"error": "Request ID not found"}), 404

    progress_data = pdf_progress[request_id].copy()

    if "pdf_path" in progress_data:
        del progress_data["pdf_path"]

    return jsonify(progress_data)


@app.get("/download/<request_id>")
def download_pdf(request_id) -> Response:
    """Download the PDF

    :param request_id: the id of the request
    :return: the PDF file or error message"""

    if request_id not in pdf_progress:
        return jsonify({"error": "PDF not found"}), 404

    progress_data = pdf_progress[request_id]

    if progress_data["status"] != "completed":
        return jsonify({"error": "PDF generation not completed"}), 400

    if not progress_data["pdf_path"] or not os.path.exists(progress_data["pdf_path"]):
        return jsonify({"error": "PDF file not found"}), 404

    pdf_path = progress_data["pdf_path"]

    del pdf_progress[request_id]

    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=os.path.basename(pdf_path),
    )


@app.get("/health")
def health() -> Response:
    """Health check endpoint

    :return: JSON response with health status"""

    temp_ok = os.path.exists(TEMP_DIR) and os.access(TEMP_DIR, os.W_OK)
    pdf_ok = os.path.exists(PDF_DIR) and os.access(PDF_DIR, os.W_OK)

    return jsonify(
        {
            "status": "ok" if temp_ok and pdf_ok else "error",
            "environment": os.getenv("FLASK_ENV", "development"),
            "server_uptime": str(datetime.now() - SERVER_START_TIME),
        }
    )


if __name__ == "__main__":
    # For local development
    app.run(debug=True, port=5000)
