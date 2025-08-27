# whatsapp-wrapped

![Example](https://imgur.com/pVzVEwE.png)

## 📝 Description
Transform your WhatsApp chat history into a beautiful PDF report filled with interesting insights, data visualizations, and engaging analytics. This tool analyzes your exported chat file and creates a comprehensive report showing your messaging patterns, favorite emojis, and much more!

✨ **Supported Platforms:** iOS and Android

🌍 **Supported Languages:** English and Italian

## 📱 How to Export Your WhatsApp Chat
1. Open the WhatsApp chat you want to analyze
2. Tap the three dots (⋮) in the top right corner
3. Select **More**
4. Choose **Export chat**
5. Select **Without media**
6. Save the file to your device
7. Upload it to WhatsApp Wrapped!

## 🎨 Features

### 📊 Visualizations
- Message frequency timeline
- Most used emoji analysis
- Popular words analysis (bar plot & wordcloud)
- Weekly messaging patterns (spider plot)
- Most active participants
- Daily message distribution

### 📈 Analytics
- Total message count
- Peak activity periods (day/month/year/weekday)
- Conversation streaks (active & inactive)
- Response time analysis
- And many more insights!


## 🗂️ Project Structure

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

## 🚀 Getting Started

### Prerequisites
- Python 3.12
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Crippius/whatsapp-wrapped.git
   cd whatsapp-wrapped
   ```

2. **Create a Python environment**
   ```bash
   conda create -n ww python=3.12
   conda activate ww
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

Launch the application locally with:
```bash
./run_local.sh
```

This will start:
- 🌐 Frontend: [http://localhost:8080](http://localhost:8080)
- ⚙️ Backend: [http://localhost:5000](http://localhost:5000)

Simply open the frontend URL in your browser to start generating your WhatsApp reports!

---

📚 For detailed documentation, check the README files in each subfolder.
