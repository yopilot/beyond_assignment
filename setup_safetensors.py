#!/usr/bin/env python3
"""
Setup script to ensure safetensors-only model downloads.
This script will clear existing model cache and set up the environment
to only download safetensors format models.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_transformers_cache():
    """Clear the transformers cache to force fresh downloads."""
    try:
        cache_dir = Path.home() / ".cache" / "huggingface"
        
        if cache_dir.exists():
            logger.info(f"Clearing HuggingFace cache at: {cache_dir}")
            shutil.rmtree(cache_dir)
            logger.info("✅ Cache cleared successfully!")
            return True
        else:
            logger.info("No HuggingFace cache found.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
        return False

def install_requirements():
    """Install the updated requirements with safetensors support."""
    try:
        logger.info("Installing updated requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"])
        logger.info("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install requirements: {e}")
        return False

def verify_safetensors():
    """Verify that safetensors is properly installed."""
    try:
        import safetensors
        import transformers
        logger.info(f"✅ Safetensors version: {safetensors.__version__}")
        logger.info(f"✅ Transformers version: {transformers.__version__}")
        return True
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def set_environment_variables():
    """Set environment variables to prefer safetensors format."""
    try:
        # Set environment variables for the current session
        os.environ['TRANSFORMERS_PREFER_SAFETENSORS'] = '1'
        os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
        
        logger.info("✅ Environment variables set:")
        logger.info("   TRANSFORMERS_PREFER_SAFETENSORS=1")
        logger.info("   HF_HUB_ENABLE_HF_TRANSFER=1")
        
        # Create a .env file for persistent settings
        env_content = """# Environment variables for safetensors preference
TRANSFORMERS_PREFER_SAFETENSORS=1
HF_HUB_ENABLE_HF_TRANSFER=1
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        
        logger.info("✅ Created .env file for persistent settings")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to set environment variables: {e}")
        return False

def main():
    """Main setup function."""
    logger.info("🚀 Setting up safetensors-only environment...")
    
    success = True
    
    # Step 1: Install requirements
    if not install_requirements():
        success = False
    
    # Step 2: Verify installations
    if not verify_safetensors():
        success = False
    
    # Step 3: Set environment variables
    if not set_environment_variables():
        success = False
    
    # Step 4: Clear cache
    if not clear_transformers_cache():
        logger.warning("⚠️  Cache clearing failed, but continuing...")
    
    if success:
        logger.info("🎉 Setup completed successfully!")
        logger.info("Your app will now only download safetensors format models.")
        logger.info("You can now run your application with: python main.py")
    else:
        logger.error("❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
