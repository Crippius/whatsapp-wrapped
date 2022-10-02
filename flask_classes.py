from flask import Flask, Response, render_template, request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import InputRequired, ValidationError



def AllowedFile(form, field):
    ALLOWED_EXTENSIONS = set(['txt', 'zip'])
    
    extension = str(request.files["file"].filename)[::-1]
    dot = extension.find(".")
    extension = extension[::-1]
    print(extension)
    extension = extension[-dot:]

    if not(extension in ALLOWED_EXTENSIONS):
        raise ValidationError(f"File inserted not allowed ({'/'.join(ALLOWED_EXTENSIONS)})")

class UploadFileForm(FlaskForm):
    file_style= {'class':'btn btn-lg btn-block border border-dark rounded', 'style':'font-size:100%', 'style':'background-color:#4FB6EC'}
    file = FileField("File", validators=[InputRequired(), AllowedFile], render_kw=file_style)

    submit_style = {'class':'btn btn-lg btn-load btn-block border border-dark rounded', 'id':'submit', 'style':'font-size:100%', 'style':'background-color:#4FB6EC'}
    submit = SubmitField("Get your PDF!", render_kw=submit_style)