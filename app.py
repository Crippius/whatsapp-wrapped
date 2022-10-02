from flask import Flask, render_template, flash, send_from_directory, redirect, url_for, jsonify
from flask_classes import UploadFileForm   # Libraries for the backend
from werkzeug.utils import secure_filename

from config import secret_key # Key for submitting files (TOP SECRET)
from os import path, remove # To move and REmove ( ;) ) files in their directories

from PDF_Constructor import PDF_Constructor # My tool to create the pdf
from seeds import * # All my manually created seeds for the pdf

app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key
app.config["UPLOAD_FOLDER"] = "text_files/"

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
        loc = path.join(path.abspath(path.dirname(__file__)), app.config['UPLOAD_FOLDER'],filename)
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
        file = file_loc
        pdf = PDF_Constructor(file, lang="en")
        seed1(pdf)
        new_file = pdf.save()
    except Exception as e: # TODO: Add errors
        flash(f"C'è stato un errore durante l'analisi del file: {e}", "danger")
        return redirect(url_for("index"))


    directory, file = new_file.split("/")
    return send_from_directory(directory, file, as_attachment=True)


@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/data")
def data():
    global pdf
    info = {"Name":"",
            "Language":"",
            "Loading":""}

    if type(pdf) == PDF_Constructor:
        
        info["Name"] = pdf.name
        info["Language"] = pdf.lang
        info["Loading"] = pdf.load
    
    return jsonify(info)



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9090, debug=True)