# Reddit Persona Generator

The **Reddit Persona Generator** is a tool that analyzes a Reddit user's activity and generates a detailed persona based on their posts and comments.

---

## Overview

[![Watch the demo](https://github.com/user-attachments/assets/f5a15e6f-a06e-4312-8f14-1386f2c52777)](https://www.youtube.com/watch?v=g3Jl2Y5tm0s)


### [📺 Watch Demo on YouTube](https://youtu.be/g3Jl2Y5tm0s)


This application scrapes a Reddit user's post and comment history, analyzes the content using AI or statistical methods, and generates a comprehensive persona that includes:

- Communication style and tone
- Main interests and topics
- Personality traits
- Online behavior patterns
- Subreddit preferences
- Engagement patterns

---

## Project Structure

```
# Setup and Configuration
├── __init__.py
├── config.json        # Configuration settings
├── config.py          # Configuration management
├── install.bat        # Windows installation script
├── install.py         # Installation script
├── requirements.txt   # Python dependencies
├── setup.py           # Setup utilities
├── README.md          # Documentation

# Backend Components
├── main.py            # Main application entry point
├── file_manager.py    # File operations handler
├── model_manager.py   # AI model management
├── persona_generator.py # Core persona generation
├── reddit_persona_generator.py # Reddit-specific persona generator
├── reddit_scraper.py  # Reddit data scraping
├── utils.py           # Utility functions
├── output/            # Generated personas and data
│   ├── *_data_*.json  # User data JSON files
│   └── *_persona_*.txt # Generated persona text files

# Web Interface (Frontend)
├── web_interface.py   # Web server and API endpoints
├── static/            # Static web assets
│   ├── css/           # Stylesheets
│   │   ├── components.css
│   │   ├── progress.css
│   │   └── styles.css
│   └── js/            # JavaScript files
│       ├── api.js     # API communication
│       ├── main.js    # Main application logic
│       └── utils.js   # Utility functions
└── templates/         # HTML templates
    ├── base.html      # Base template
    └── index.html     # Main page
```

---

## Features

- **Web Interface:** Easy-to-use browser interface for generating personas
- **Command Line Usage:** Generate personas directly from the command line
- **Progress Tracking:** Real-time progress updates during generation
- **GPU Acceleration:** Utilizes GPU for faster processing when available
- **Fallback Generation:** Statistical analysis as backup if AI generation fails
- **Downloadable Results:** Output available as text files for download

---

## Installation

### Windows

```sh
install.bat
```

### Linux/macOS

```sh
python install.py
```

### Manual Setup

Install required dependencies:

```sh
pip install -r requirements.txt
```

---

## Getting Reddit API Credentials

To use this tool, you need Reddit API credentials. Follow these steps:

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps).
2. Click **"create another app"** at the bottom.
3. Fill in the name, select **"script"** as the type.
4. Set the redirect URI to `http://localhost:8080` (or any valid URI).
5. After creation, copy the **client ID** (under the app name) and **client secret**.
6. Update your `config.json`:

```json
{
  "reddit": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "user_agent": "RedditPersonaGenerator/2.0 by YOUR_USERNAME"
  }
}
```

---

## Usage

### Web Interface

```sh
python main.py --web
```

Then open your browser and navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Command Line

```sh
python main.py USERNAME
```

Replace `USERNAME` with the Reddit username you want to analyze.

### Check GPU Status

```sh
python main.py --gpu-info
```

---

## How It Works

1. **Data Collection:** Scrapes the user's posts and comments from Reddit using the Reddit API.
2. **Data Processing:** Analyzes the content, identifying patterns, topics, and writing style.
3. **Persona Generation:** Uses AI model or statistical analysis to create a comprehensive persona.
4. **Result Storage:** Saves the persona and raw data to JSON and text files.

---

## Technical Details

- **AI Models:** Uses machine learning models for natural language processing
- **Error Handling:** Robust error handling with fallback mechanisms
- **Progress Reporting:** Real-time progress updates for better user experience
- **Memory Management:** Optimized for handling large datasets efficiently

---

## Recent Fixes

- Model loading now works correctly with GPU acceleration
- Better error handling for troubleshooting
- Improved memory management
- Fixed dtype conflict issues

---

## Requirements

- Python 3.7+
- torch >= 1.9.0
- transformers >= 4.20.0
- praw >= 7.6.0
- flask >= 2.0.0
- tqdm >= 4.64.0
- numpy >= 1.21.0
- requests >= 2.28.0

---

## License

MIT License
