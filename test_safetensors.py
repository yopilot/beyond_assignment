#!/usr/bin/env python3
"""
Quick test script to verify safetensors-only model loading.
This will help identify if the issue is with the model loading process.
"""

import os
import sys
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variables for safetensors preference
os.environ['TRANSFORMERS_PREFER_SAFETENSORS'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'

def test_model_loading():
    """Test model loading with safetensors."""
    try:
        model_name = "microsoft/DialoGPT-medium"
        logger.info(f"Testing model loading: {model_name}")
        
        # Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            use_fast=True,
            trust_remote_code=False
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("✅ Tokenizer loaded successfully")
        
        # Load model with safetensors
        logger.info("Loading model with safetensors...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            use_safetensors=True,
            trust_remote_code=False,
            low_cpu_mem_usage=True,
            torch_dtype=torch.float32  # Use float32 for CPU
        )
        
        logger.info("✅ Model loaded successfully")
        
        # Create pipeline
        logger.info("Creating pipeline...")
        generator = pipeline(
            'text-generation',
            model=model,
            tokenizer=tokenizer,
            device=-1  # CPU
        )
        
        logger.info("✅ Pipeline created successfully")
        
        # Test generation
        logger.info("Testing text generation...")
        response = generator(
            "Hello, how are you?",
            max_new_tokens=10,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
        
        logger.info(f"✅ Generation test successful: {response[0]['generated_text']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        return False

def verify_cache():
    """Verify that only safetensors files are downloaded."""
    try:
        from pathlib import Path
        
        cache_dir = Path.home() / ".cache" / "huggingface" / "transformers"
        if not cache_dir.exists():
            logger.info("No cache directory found yet")
            return
        
        model_dirs = list(cache_dir.glob("*DialoGPT*"))
        for model_dir in model_dirs:
            safetensors_files = list(model_dir.glob("*.safetensors"))
            pytorch_files = list(model_dir.glob("pytorch_model*.bin"))
            
            logger.info(f"Cache directory: {model_dir.name}")
            logger.info(f"  Safetensors files: {len(safetensors_files)}")
            logger.info(f"  PyTorch files: {len(pytorch_files)}")
            
            if safetensors_files and not pytorch_files:
                logger.info("  ✅ Only safetensors files found!")
            elif safetensors_files and pytorch_files:
                logger.warning("  ⚠️  Both formats found")
            elif pytorch_files and not safetensors_files:
                logger.warning("  ⚠️  Only PyTorch files found")
                
    except Exception as e:
        logger.warning(f"Could not verify cache: {e}")

if __name__ == "__main__":
    logger.info("🧪 Testing safetensors-only model loading...")
    
    # Verify cache before loading
    logger.info("Checking existing cache...")
    verify_cache()
    
    # Test model loading
    success = test_model_loading()
    
    if success:
        logger.info("🎉 All tests passed! Safetensors loading works correctly.")
        
        # Verify cache after loading
        logger.info("Checking cache after loading...")
        verify_cache()
    else:
        logger.error("❌ Tests failed. Check the errors above.")
        sys.exit(1)
