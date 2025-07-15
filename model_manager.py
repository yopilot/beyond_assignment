"""AI model management for persona generation."""

import logging
import sys
from typing import Optional, List, Dict
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from config import Config, DEFAULT_MODELS
from utils import timeout

class ModelManager:
    """AI model management class."""
    
    def __init__(self, config: Config, progress_callback=None):
        self.config = config
        self.generator = None
        self.tokenizer = None
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        self.log_system_info()
    
    def update_progress(self, stage: str, progress: int, message: str):
        """Update progress for UI."""
        if self.progress_callback:
            self.progress_callback(stage, progress, message)
        self.logger.info(f"[{stage}] {progress}% - {message}")
    
    def log_system_info(self):
        """Log system and GPU information."""
        self.logger.info("=== SYSTEM INFORMATION ===")
        self.logger.info(f"PyTorch version: {torch.__version__}")
        self.logger.info(f"CUDA available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            self.logger.info(f"CUDA version: {torch.version.cuda}")
            self.logger.info(f"Number of GPUs: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                self.logger.info(f"GPU {i}: {gpu_name} ({memory_total:.1f}GB)")
        else:
            self.logger.info("No GPU detected - will use CPU")
        self.logger.info("===========================")
    
    def load_model(self):
        """Load the language model with safetensors format and proper tokenizer configuration."""
        if self.generator is not None:
            return
        
        self.update_progress("loading", 0, "Loading language model...")
        
        # Check if GPU is available and set device properly
        if torch.cuda.is_available():
            device = "cuda:0"  # Use string format for device
            torch_dtype = torch.float16
            self.logger.info(f"GPU detected! Using CUDA device: {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            torch_dtype = torch.float32
            self.logger.info("No GPU detected. Using CPU for inference.")
        
        # Try models in order of preference
        for model_name in DEFAULT_MODELS:
            try:
                self.update_progress("loading", 10, f"Trying {model_name} on {device}...")
                
                # Load tokenizer first with proper configuration
                self.update_progress("loading", 20, "Loading tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    use_fast=True,  # Use fast tokenizers when available
                    trust_remote_code=False
                )
                
                # Set padding token if not exists
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                self.update_progress("loading", 30, "Tokenizer loaded, downloading model with safetensors...")
                self.logger.info("Note: Initial model download may take 10-20 minutes depending on connection speed")
                
                # Load model with explicit safetensors preference
                self.update_progress("loading", 40, "Downloading model files (this may take several minutes)...")
                
                if device == "cuda:0":
                    # For GPU, use device_map but don't specify device in pipeline
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=torch_dtype,
                        use_safetensors=True,  # Force safetensors format
                        trust_remote_code=False,
                        low_cpu_mem_usage=True,  # Optimize memory usage
                        device_map="auto"  # Let accelerate handle device placement
                    )
                    
                    self.update_progress("loading", 80, "Model downloaded, creating generation pipeline...")
                    
                    # Create pipeline WITHOUT device parameter when using device_map
                    self.generator = pipeline(
                        'text-generation',
                        model=model,
                        tokenizer=self.tokenizer
                        # No device parameter - accelerate handles it
                    )
                else:
                    # For CPU, load normally and specify device
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=torch_dtype,
                        use_safetensors=True,  # Force safetensors format
                        trust_remote_code=False,
                        low_cpu_mem_usage=True  # Optimize memory usage
                    )
                    
                    # Move model to CPU
                    model = model.to(device)
                    
                    self.update_progress("loading", 80, "Model downloaded, creating generation pipeline...")
                    
                    # Create pipeline with CPU device
                    self.generator = pipeline(
                        'text-generation',
                        model=model,
                        tokenizer=self.tokenizer,
                        device=-1  # CPU
                    )
                
                self.update_progress("loading", 90, "Testing model functionality...")
                
                # Test the model with a simple generation
                test_response = self.generator(
                    "Hello",
                    max_new_tokens=5,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
                self.update_progress("loading", 100, f"Model {model_name} loaded successfully with safetensors!")
                self.logger.info(f"Successfully loaded {model_name} on {device} using safetensors format")
                
                # Verify safetensors usage
                self.verify_safetensors_usage(model_name)
                
                # Log memory usage if GPU
                if device == "cuda:0":
                    memory_allocated = torch.cuda.memory_allocated(0) / 1024**3  # GB
                    memory_reserved = torch.cuda.memory_reserved(0) / 1024**3   # GB
                    self.logger.info(f"GPU Memory - Allocated: {memory_allocated:.2f}GB, Reserved: {memory_reserved:.2f}GB")
                
                return
                
            except Exception as e:
                self.logger.warning(f"Failed to load {model_name} on {device}: {e}")
                self.update_progress("loading", 30, f"Failed to load {model_name}, trying next...")
                # Clean up GPU memory if allocation failed
                if device == "cuda:0":
                    torch.cuda.empty_cache()
                continue
        
        # If all models fail, raise error
        raise RuntimeError("No suitable model could be loaded. Please check your internet connection and try again.")
    
    def verify_safetensors_usage(self, model_name: str):
        """Verify that the model is using safetensors format."""
        try:
            import transformers
            from pathlib import Path
            
            # Check model cache for safetensors files
            cache_dir = Path.home() / ".cache" / "huggingface" / "transformers"
            model_cache_dirs = list(cache_dir.glob(f"*{model_name.replace('/', '--')}*"))
            
            for model_dir in model_cache_dirs:
                safetensors_files = list(model_dir.glob("*.safetensors"))
                pytorch_files = list(model_dir.glob("pytorch_model*.bin"))
                
                self.logger.info(f"Model cache directory: {model_dir}")
                self.logger.info(f"Safetensors files found: {len(safetensors_files)}")
                self.logger.info(f"PyTorch files found: {len(pytorch_files)}")
                
                if safetensors_files and not pytorch_files:
                    self.logger.info("✅ Model is using safetensors format only!")
                    return True
                elif safetensors_files and pytorch_files:
                    self.logger.warning("⚠️  Both safetensors and PyTorch files found")
                    return False
                elif pytorch_files and not safetensors_files:
                    self.logger.warning("⚠️  Only PyTorch files found, no safetensors")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Could not verify safetensors usage: {e}")
            return False

    def clear_model_cache(self):
        """Clear the transformers cache to force fresh downloads with safetensors."""
        try:
            import transformers
            from pathlib import Path
            import shutil
            
            # Get cache directory
            cache_dir = Path.home() / ".cache" / "huggingface" / "transformers"
            
            if cache_dir.exists():
                self.logger.info(f"Clearing transformers cache at: {cache_dir}")
                shutil.rmtree(cache_dir)
                self.logger.info("Cache cleared successfully. Next model load will use safetensors format.")
                return True
            else:
                self.logger.info("No transformers cache found.")
                return False
                
        except Exception as e:
            self.logger.warning(f"Failed to clear cache: {e}")
            return False

    def reset_model_state(self):
        """Reset model state to ensure clean generation."""
        try:
            if self.generator is not None and hasattr(self.generator, 'model'):
                # Clear any cached states
                if hasattr(self.generator.model, 'eval'):
                    self.generator.model.eval()
                
                # Clear GPU cache if using CUDA
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
            self.logger.info("Model state reset successfully")
        except Exception as e:
            self.logger.warning(f"Model state reset warning: {e}")

    def generate_with_timeout(self, prompt: str) -> Optional[str]:
        """Generate with timeout protection, optimized for CPU."""
        try:
            model_config = self.config.get_model_config()
            
            # Determine if we're using CPU and adjust settings accordingly
            is_cpu = not torch.cuda.is_available() or self.generator.device.type == 'cpu'
            
            if is_cpu:
                # More conservative settings for CPU
                max_new_tokens = min(model_config.get('max_new_tokens', 256), 128)  # Reduce tokens for CPU
                timeout_duration = 600  # 10 minutes for CPU
                self.logger.info("Using CPU-optimized generation settings")
            else:
                # Original settings for GPU
                max_new_tokens = model_config.get('max_new_tokens', 256)
                timeout_duration = 300  # 5 minutes for GPU
            
            self.logger.info(f"Starting generation with {max_new_tokens} max tokens, {timeout_duration}s timeout")
            
            with timeout(timeout_duration):
                # CPU-optimized generation parameters
                generation_params = {
                    'max_new_tokens': max_new_tokens,
                    'temperature': model_config.get('temperature', 0.7),
                    'top_p': model_config.get('top_p', 0.9),
                    'do_sample': True,
                    'pad_token_id': self.tokenizer.eos_token_id,
                    'truncation': True,
                    'num_return_sequences': 1,
                    'return_full_text': False,
                    'clean_up_tokenization_spaces': True
                }
                
                # Add CPU-specific optimizations
                if is_cpu:
                    generation_params.update({
                        'num_beams': 1,  # Disable beam search for CPU
                        'early_stopping': True,
                        'max_time': timeout_duration - 30  # Leave buffer for cleanup
                    })
                
                self.logger.info("Generating text with AI model...")
                response = self.generator(prompt, **generation_params)
                
                if response and len(response) > 0 and 'generated_text' in response[0]:
                    generated_text = response[0]['generated_text']
                    self.logger.info(f"Generation complete. Length: {len(generated_text)} characters")
                    
                    # Extract only the persona part (after "PROFILE:")
                    if "PROFILE:" in generated_text:
                        persona = generated_text.split("PROFILE:")[-1].strip()
                    else:
                        persona = generated_text.strip()
                    
                    # Ensure we have some content
                    if len(persona.strip()) < 10:
                        self.logger.warning("Generated text too short, treating as failure")
                        return None
                        
                    return persona
                else:
                    self.logger.warning("Generation returned empty or invalid response")
                    return None
                
        except TimeoutError:
            timeout_min = timeout_duration // 60
            self.logger.error(f"Generation timed out after {timeout_min} minutes")
            return None
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            return None
