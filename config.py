"""Configuration management for Reddit Persona Generator."""

import json
import logging
import os
from typing import Dict

# Default models in order of preference (fastest to slowest)
DEFAULT_MODELS = [
    "microsoft/DialoGPT-medium",  # Faster, conversation-focused
    "gpt2",  # Reliable fallback
    "distilgpt2",  # Even faster fallback
]

class Config:
    """Configuration management class."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config if not found
            default_config = {
                "reddit": {
                    "client_id": "YOUR_CLIENT_ID",
                    "client_secret": "YOUR_CLIENT_SECRET",
                    "user_agent": "RedditPersonaGenerator/1.0 by YourUsername"
                },
                "model": {
                    "name": "microsoft/DialoGPT-medium",
                    "max_new_tokens": 256,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                "scraping": {
                    "max_posts": 100,
                    "max_comments": 200,
                    "days_limit": 365
                }
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            print(f"Created default config at {self.config_path}. Please update with your Reddit API credentials.")
            return default_config
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def get_reddit_config(self) -> Dict:
        """Get Reddit API configuration."""
        return self.config.get('reddit', {})
    
    def get_model_config(self) -> Dict:
        """Get model configuration."""
        return self.config.get('model', {})
    
    def get_scraping_config(self) -> Dict:
        """Get scraping configuration."""
        return self.config.get('scraping', {})
