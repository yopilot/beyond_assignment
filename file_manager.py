"""File operations for saving persona results."""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List

class FileManager:
    """File management class for saving results."""
    
    def __init__(self, output_dir: str = 'output', progress_callback=None):
        # Convert to absolute path if it's not already
        if not os.path.isabs(output_dir):
            self.output_dir = os.path.abspath(output_dir)
        else:
            self.output_dir = output_dir
            
        self.progress_callback = progress_callback
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"Created output directory: {self.output_dir}")
        else:
            self.logger.info(f"Using output directory: {self.output_dir}")
    
    def update_progress(self, stage: str, progress: int, message: str):
        """Update progress for UI."""
        if self.progress_callback:
            self.progress_callback(stage, progress, message)
        self.logger.info(f"[{stage}] {progress}% - {message}")
    
    def save_persona(self, username: str, persona: str, posts: List[Dict], comments: List[Dict], sentiment_data: Dict = None) -> str:
        """Save persona and data to files."""
        self.update_progress("saving", 0, "Saving results...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save persona
        persona_file = os.path.join(self.output_dir, f'{username}_persona_{timestamp}.txt')
        with open(persona_file, 'w', encoding='utf-8') as f:
            f.write(f"Reddit Persona for: {username}\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Posts analyzed: {len(posts)}\n")
            f.write(f"Comments analyzed: {len(comments)}\n")
            f.write("=" * 50 + "\n\n")
            f.write(persona)
        
        # Save raw data
        data_file = os.path.join(self.output_dir, f'{username}_data_{timestamp}.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'username': username,
                'generated_at': datetime.now().isoformat(),
                'posts': posts,
                'comments': comments,
                'persona': persona,
                'sentiment_data': sentiment_data if sentiment_data else {}
            }, f, indent=2)
        
        self.update_progress("saving", 100, f"Results saved to {persona_file}")
        
        return persona_file
