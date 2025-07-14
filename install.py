#!/usr/bin/env python3
"""
Quick installation and setup script for Reddit Persona Generator
"""

import os
import sys
import subprocess
import json

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {str(e)}")
        return False
    except FileNotFoundError:
        print("❌ pip not found. Please install pip first.")
        return False

def create_config_if_missing():
    """Create config file if it doesn't exist."""
    if not os.path.exists("config.py"):
        print("📝 Creating default config.py...")
        config_content = '''"""Configuration file for Reddit Persona Generator."""

# Reddit API Configuration
# Get these from: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID = "your_client_id_here"
REDDIT_CLIENT_SECRET = "your_client_secret_here"
REDDIT_USER_AGENT = "PersonaGenerator/1.0"

# Model Configuration
MODEL_NAME = "microsoft/DialoGPT-medium"
MAX_LENGTH = 1000
TEMPERATURE = 0.8

# Output Configuration
OUTPUT_DIR = "output"
'''
        with open("config.py", "w") as f:
            f.write(config_content)
        print("✅ Default config.py created!")
        print("⚠️  Please edit config.py with your Reddit API credentials")
        return False
    return True

def create_directories():
    """Create necessary directories."""
    dirs = ["output", "templates", "static/css", "static/js"]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")

def main():
    """Main setup function."""
    print("🔧 Reddit Persona Generator - Setup")
    print("="*40)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        return False
    
    print(f"✅ Python version: {sys.version}")
    
    # Create directories
    create_directories()
    
    # Create config if missing
    config_exists = create_config_if_missing()
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    print("\n" + "="*40)
    print("🎉 Setup complete!")
    
    if not config_exists:
        print("\n⚠️  IMPORTANT: Please configure your Reddit API credentials:")
        print("1. Go to: https://www.reddit.com/prefs/apps")
        print("2. Create a new app (script type)")
        print("3. Edit config.py with your client ID and secret")
        print("4. Run: python start.py")
    else:
        print("\n🚀 Ready to start! Run: python start.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
