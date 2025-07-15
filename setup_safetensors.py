#!/usr/bin/env python3
"""
Unified setup and test script for safetensors-only model loading.
Performs environment setup, checks safetensors support, verifies model caching,
loads model, and tests generation using safetensors format.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# ────────────────────── Logging Setup ────────────────────── #
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ────────────────────── Env Vars ────────────────────── #
def set_environment_variables():
    os.environ['TRANSFORMERS_PREFER_SAFETENSORS'] = '1'
    os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
    logger.info("✅ Environment variables set for safetensors-only")

# ────────────────────── Install Requirements ────────────────────── #
def install_requirements():
    try:
        logger.info("📦 Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"])
        logger.info("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install requirements: {e}")
        sys.exit(1)

# ────────────────────── Safetensors Verification ────────────────────── #
def verify_safetensors():
    try:
        import safetensors
        import transformers
        logger.info(f"✅ safetensors version: {safetensors.__version__}")
        logger.info(f"✅ transformers version: {transformers.__version__}")
    except ImportError as e:
        logger.error(f"❌ Required module not found: {e}")
        sys.exit(1)

# ────────────────────── Cache Check ────────────────────── #
def verify_cache(model_name="DialoGPT-medium"):
    cache_dir = Path.home() / ".cache" / "huggingface" / "transformers"
    if not cache_dir.exists():
        logger.info("ℹ️ No cache directory found.")
        return False

    model_dirs = list(cache_dir.glob(f"**/*{model_name.replace('/', '_')}*"))
    found_safetensors, found_bin = False, False

    for model_dir in model_dirs:
        safetensors_files = list(model_dir.glob("*.safetensors"))
        bin_files = list(model_dir.glob("pytorch_model*.bin"))

        if safetensors_files:
            found_safetensors = True
        if bin_files:
            found_bin = True

        logger.info(f"🗂️ Cache: {model_dir.name} - Safetensors: {len(safetensors_files)}, Bin: {len(bin_files)}")

    if found_safetensors and not found_bin:
        logger.info("✅ Cache OK: Only safetensors found")
    elif found_bin:
        logger.warning("⚠️ PyTorch bin files also found. Setup may not be safetensors-only.")
    else:
        logger.info("🔄 Model not yet cached")
    
    return found_safetensors

# ────────────────────── Model Loading Test ────────────────────── #
def test_model_loading():
    try:
        model_name = "microsoft/DialoGPT-medium"
        logger.info(f"🧠 Loading model: {model_name}")

        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True, trust_remote_code=False)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            use_safetensors=True,
            trust_remote_code=False,
            low_cpu_mem_usage=True,
            torch_dtype=torch.float32
        )

        generator = pipeline(
            'text-generation',
            model=model,
            tokenizer=tokenizer,
            device=-1
        )

        output = generator("Hello, how are you?", max_new_tokens=10, do_sample=False)
        logger.info(f"✅ Test output: {output[0]['generated_text']}")
        return True

    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        return False

# ────────────────────── Main Entry ────────────────────── #
def main():
    logger.info("🚀 Starting safetensors-only setup & test")

    set_environment_variables()
    install_requirements()
    verify_safetensors()

    logger.info("🔍 Checking existing cache...")
    already_cached = verify_cache()

    logger.info("🧪 Testing model loading...")
    if test_model_loading():
        logger.info("🎉 All tests passed! Safetensors-only setup is working.")
        if not already_cached:
            logger.info("🔁 Verifying updated cache after model load...")
            verify_cache()
    else:
        logger.error("❌ Safetensors test failed. Check above logs for issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
