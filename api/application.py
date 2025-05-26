from flask import Flask, render_template, flash, send_from_directory, redirect, url_for, jsonify

from werkzeug.utils import secure_filename

from os import path, remove # To move and REmove ( ;) ) files in their directories
from os import getenv, makedirs

import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
utilities_dir = current_dir.parent / 'src'

sys.path.append(str(utilities_dir.parent))

from src.flask_classes import UploadFileForm   # Libraries for the backend
from src.PDF_Constructor import PDF_Constructor # My tool to create the pdf
from src.seeds import * # All my manually created seeds for the pdf

application = Flask(__name__, template_folder="../templates", static_folder="../static")
app = application

app.config["SECRET_KEY"] = getenv("ww_secret_key")

# Set up directories for both Vercel and local environments
if getenv('VERCEL') == '1':
    app.config["UPLOAD_FOLDER"] = '/tmp/text_files/'
    app.config["PDF_FOLDER"] = '/tmp/pdfs/'
else:
    app.config["UPLOAD_FOLDER"] = path.abspath(path.join(path.dirname(__file__), '../text_files/'))
    app.config["PDF_FOLDER"] = path.abspath(path.join(path.dirname(__file__), '../pdfs/'))

# Create necessary directories
makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
makedirs(app.config["PDF_FOLDER"], exist_ok=True)

file_loc = ""
pdf = ""

@app.route("/index")
@app.route("/", methods=["GET", "POST"])
def index():
    global file_loc

    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = " ".join(secure_filename(file.filename).split("_"))
        loc = path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(loc)
        file_loc = loc
        return redirect(url_for("download"))

    if form.errors != {}:
        for error in form.errors.values():
            flash(f"There has been an error during the upload: {error}", "danger")
        
    return render_template("index.html", form=form)

@app.route("/download")
def download():
    global file_loc
    global pdf

    try:
        if not file_loc:
            flash("No file was uploaded", "danger")
            return redirect(url_for("index"))

        file = file_loc
        pdf = PDF_Constructor(file, lang="en")
        seed1(pdf)
        new_file = pdf.save()
        
        # Clean up the uploaded file
        if path.exists(file):
            remove(file)

        # Send the PDF file
        directory = path.dirname(new_file)
        filename = path.basename(new_file)
        return send_from_directory(directory, filename, as_attachment=True)

    except Exception as e:
        flash(f"An error occurred during file analysis: {str(e)}", "danger")
        # Clean up any temporary files
        if path.exists(file_loc):
            remove(file_loc)
        return redirect(url_for("index"))

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/data")
def data():
    global pdf
    info = {
        "Name": "",
        "Language": "",
        "Loading": ""
    }

    if isinstance(pdf, PDF_Constructor):
        info["Name"] = pdf.name
        info["Language"] = pdf.lang
        info["Loading"] = pdf.load
    
    return jsonify(info)

if __name__ == "__main__":
    app.run()