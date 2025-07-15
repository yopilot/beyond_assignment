@echo off
echo Setting up Reddit Persona Generator...



REM Install requirements
pip install -r requirements.txt --upgrade

REM Setup safetensors environment
python setup_safetensors.py

REM Create necessary directories
mkdir templates 2>nul
mkdir output 2>nul
mkdir logs 2>nul

echo Setup complete!
echo.
echo To run the application:
echo 1. Activate virtual environment: venv\Scripts\activate
echo 2. Update config.json with your Reddit API credentials
echo 2a. To get Reddit API credentials:
echo     - Go to https://www.reddit.com/prefs/apps
echo     - Click "create another app" at the bottom
echo     - Fill in name, description, and redirect uri (e.g., http://localhost:8080)
echo     - Select "script" as the type
echo     - After creation, copy the client ID and secret into config.json
echo 3. Run: python main.py --web
echo.
echo For command line usage:
echo python main.py username_here