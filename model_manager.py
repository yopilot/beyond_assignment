"""AI model management for persona generation."""

import logging
import sys
from typing import Optional, List, Dict
import torch
from transformers import pipeline, AutoTokenizer
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
        """Load the language model with proper tokenizer configuration and timeout protection."""
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
                self.update_progress("loading", 20, f"Trying {model_name} on {device}...")
                
                # Load tokenizer first with proper configuration
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                
                # Set padding token if not exists
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                self.update_progress("loading", 60, "Loading model weights...")
                
                # Simple pipeline configuration without complex GPU parameters
                try:
                    if device == "cuda:0":
                        # Simple GPU configuration
                        self.generator = pipeline(
                            'text-generation',
                            model=model_name,
                            tokenizer=self.tokenizer,
                            device=0
                        )
                    else:
                        # CPU configuration
                        self.generator = pipeline(
                            'text-generation',
                            model=model_name,
                            tokenizer=self.tokenizer,
                            device=-1
                        )
                except Exception as simple_error:
                    # Even simpler fallback - let pipeline auto-decide device
                    self.logger.warning(f"Device-specific loading failed, trying auto-device: {simple_error}")
                    self.generator = pipeline(
                        'text-generation',
                        model=model_name,
                        tokenizer=self.tokenizer
                    )
                
                # Test the model with a simple generation
                test_response = self.generator(
                    "Hello",
                    max_new_tokens=5,
                    do_sample=False,
                    pad_token_id=self.tokenizer.eos_token_id
                )
                
                self.update_progress("loading", 100, f"Model {model_name} loaded successfully on {device}!")
                self.logger.info(f"Successfully loaded {model_name} on {device}")
                
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
        """Generate with timeout protection."""
        try:
            model_config = self.config.get_model_config()
            
            with timeout(300):  # 5-minute timeout
                response = self.generator(
                    prompt,
                    max_new_tokens=model_config.get('max_new_tokens', 256),
                    temperature=model_config.get('temperature', 0.7),
                    top_p=model_config.get('top_p', 0.9),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    truncation=True,  # KEY FIX: Explicit truncation
                    num_return_sequences=1,
                    return_full_text=False,  # Only return generated text
                    clean_up_tokenization_spaces=True
                )
                
                generated_text = response[0]['generated_text']
                
                # Extract only the persona part (after "PERSONA:")
                if "PERSONA:" in generated_text:
                    persona = generated_text.split("PERSONA:")[-1].strip()
                else:
                    persona = generated_text
                
                return persona
                
        except TimeoutError:
            self.logger.error("Generation timed out after 5 minutes")
            return None
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            return None
