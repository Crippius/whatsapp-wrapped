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
├── backend/                               # Backend (Flask API and core logic)
│   ├── api/                               # Flask web app (routes/controllers)
│   │   ├── application.py                 # Flask app entry point
│   │   └── config.py                      # App configuration
│   ├── src/                               # Source code
│   │   ├── pdf/                           # PDF generation logic
│   │   │   ├── constructor.py             # PDF_Constructor class and PDF logic
│   │   │   └── plots.py                   # Plotting functions (matplotlib, wordcloud, etc.)
│   │   ├── data/                          # Data extraction and cleaning
│   │   │   └── parser.py                  # Parsing exported WhatsApp chats
│   │   ├── seeds.py                       # Seeds/templates for PDF content
│   │   ├── utils.py                       # Utility functions
│   │   ├── db.py                          # Database functions
│   │   └── flask_classes.py               # Flask forms and validators
│   ├── static/                            # Backend static assets (if any)
│   ├── pdfs/                              # Generated PDF files (backend-run)
│   ├── text_files/                        # Uploaded WhatsApp chat files (backend)
│   ├── my_fonts/                          # Custom fonts for PDF/plots
│   ├── lists/                             # Auxiliary lists/data
│   ├── requirements.txt                   # Backend Python dependencies
│   └── render.yaml                        # Deployment config (Render)
├── frontend/                              # Frontend (static site)
│   ├── index.html                         # Main UI
│   ├── faq.html                           # FAQ page
│   ├── js/
│   │   └── main.js                        # Frontend logic
│   ├── static/                            # Frontend static assets (images, CSS)
│   ├── public/                            # Public assets
│   └── vercel.json                        # Frontend deployment config
├── pdfs/                                  # Generated PDFs (root-level, optional)
├── text_files/                            # Uploaded chat files (root-level, optional)
├── run_local.sh                           # Script to start frontend and backend locally
├── README.md                              # Project documentation
└── .gitignore
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

The application can be easily started locally by running inside the root directory the following command
```bash
   ./run_local.sh
```
The script will automatically create the frontend and backend in the following ports:

* Frontend: http://localhost:8080
* Backend: http://localhost:5000

To get the application paste the frontend address inside your browser and use the web interface to generate your PDF report


For more details, see the README files in each subfolder. 
