"""Main Reddit Persona Generator class."""

import logging
import sys
from typing import Dict, List
from config import Config
from reddit_scraper import RedditScraper
from model_manager import ModelManager
from persona_generator import PersonaGenerator
from file_manager import FileManager

# Global variables for progress tracking
current_status = {"stage": "idle", "progress": 0, "message": "Ready", "error": None, "completed": False, "generation_id": None}
generation_lock = False

class RedditPersonaGenerator:
    """Main Reddit Persona Generator class."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the Reddit Persona Generator."""
        self.config = Config(config_path)
        self.setup_logging()
        
        # Initialize components with progress callback
        self.scraper = RedditScraper(self.config, self.update_progress)
        self.model_manager = ModelManager(self.config, self.update_progress)
        self.persona_generator = PersonaGenerator(self.model_manager, self.update_progress)
        self.file_manager = FileManager(progress_callback=self.update_progress)
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('persona_generator.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def update_progress(self, stage: str, progress: int, message: str):
        """Update progress for UI."""
        global current_status
        current_status.update({
            "stage": stage,
            "progress": progress,
            "message": message,
            "completed": stage == "completed",  # Set completed flag when stage is completed
            "error": None if stage != "error" else current_status.get("error")
        })
        self.logger.info(f"[{stage}] {progress}% - {message}")
    
    def reset_status(self):
        """Reset the generation status."""
        global current_status
        current_status = {
            "stage": "idle", 
            "progress": 0, 
            "message": "Ready", 
            "error": None, 
            "completed": False, 
            "generation_id": None
        }
    
    def generate_full_persona(self, username: str) -> str:
        """Complete persona generation pipeline."""
        global current_status
        # Reset status before starting
        self.reset_status()
        self.logger.info(f"Persona generation started for user: {username}")
        try:
            self.update_progress("initializing", 0, "Setting up generation environment...")
            
            # Load model if not already loaded
            if self.model_manager.generator is None:
                self.update_progress("initializing", 50, "Loading AI model...")
                self.model_manager.load_model()
            
            self.update_progress("initializing", 100, "Initialization complete")
            
            # Scrape user data with detailed progress
            self.update_progress("fetching_posts", 0, "Starting to fetch user posts...")
            posts, comments = self.scraper.scrape_user(username, progress_callback=self.update_progress)
            
            if not posts and not comments:
                self.update_progress("error", 0, f"No data found for user '{username}'")
                raise ValueError(f"No data found for user '{username}'")
            
            self.update_progress("preparing_data", 0, "Processing collected data...")
            self.update_progress("preparing_data", 50, f"Found {len(posts)} posts and {len(comments)} comments")
            self.update_progress("preparing_data", 100, "Data preparation complete")
            
            # Generate persona with progress updates
            self.update_progress("generating_persona", 0, "Starting AI persona generation...")
            persona, sentiment_data = self.persona_generator.generate_persona(
                username, posts, comments, progress_callback=self.update_progress
            )
            
            # Save results
            self.update_progress("saving_results", 0, "Saving persona to file...")
            output_file = self.file_manager.save_persona(username, persona, posts, comments, sentiment_data)
            self.update_progress("saving_results", 100, "Results saved successfully")
            
            self.update_progress("finalizing", 0, "Finalizing generation...")
            self.update_progress("finalizing", 100, "Generation complete!")
            
            # Return the full file path (the web interface will handle path extraction)
            return output_file
            
        except Exception as e:
            self.update_progress("error", 0, f"Generation failed: {str(e)}")
            self.logger.error(f"Error in persona generation pipeline: {e}")
            raise
        finally:
            self.logger.info(f"Persona generation finished for user: {username}")
