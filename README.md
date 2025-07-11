# whatsapp-wrapped

![Example](https://imgur.com/tZYIfJb.png)

## Description
This repository contains the project I developed during the summmer of '22, in which I created a script 
that takes an exported .txt file from a Whatsapp chat and
outputs a PDF that explores lots of interesting information and data about its conversations through graphs
and made-up messages.

The program supports both IOS and Android exported files.
The supported languages are English and Italian.

## How to export a Whatsapp chat
* Go to the chat you want to want to know more
* Click the three dots on the top right of your screen 
* Click "More"
* Click "Export chat" 
* Click "Without media"
* Download it into your device 
* Use it in this script!

## Functionalities
Possible plots:
* Number of messages from the start of your texting journey to today (line plot)
* Most used emojis (bar plot)
* Most used words (bar plot / wordcloud)
* Number of messages per weekday (spider plot)
* Most active people (bar plot)
* Number of messages per time of day (line plot)

You can also get info about
* Total number of messages
* Most active day/month/year/weekday
* Longest (in)active streak
* Average response time
* And much more!!! 

## File Structure

```
whatsapp-wrapped/
├── api/                    # Flask web app (routes/controllers)
│   └── application.py      # Flask app entry point
├── src/                    # Source code
│   ├── pdf/                # PDF generation logic
│   │   ├── constructor.py      # PDF_Constructor class and PDF logic
│   │   └── plots.py            # All plotting functions (matplotlib, wordcloud, etc.)
│   ├── data/               # Data extraction and cleaning
│   │   ├── parser.py           # get_data, remove_header, etc.
│   │   └── seeds.py            # Seeds/templates for PDF content
│   ├── utils.py            # Utility functions (legacy)
│   ├── flask_classes.py    # Flask forms and validators
│   └── __init__.py         # Package marker
├── static/                 # Static assets (images, CSS)
├── templates/              # HTML templates
├── text_files/             # Uploaded WhatsApp chat files
├── pdfs/                   # Generated PDF files
├── my_fonts/               # Custom fonts for PDF/plots
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Crippius/whatsapp-wrapped.git
   cd whatsapp-wrapped
   ```

2. **Set up a Python environment (recommended):**
   ```bash
   conda create -n ww python=3.12
   conda activate ww
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the Flask App

1. **Set environment variables (optional):**
   - For local development, you may want to set `FLASK_APP` and `FLASK_ENV`:
     ```bash
     export FLASK_APP=api/application.py
     export FLASK_ENV=development
     ```
     On Windows (PowerShell):
     ```powershell
     $env:FLASK_APP = "api/application.py"
     $env:FLASK_ENV = "development"
     ```

2. **Start the app:**
   ```bash
   flask run
   ```
   The app will be available at http://127.0.0.1:5000

3. **Upload a WhatsApp chat file** on the web interface to generate your PDF report.

---

For more details, see the README files in each subfolder. 
