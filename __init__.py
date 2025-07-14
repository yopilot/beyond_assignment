"""Reddit Persona Generator Package."""

from .config import Config
from .reddit_scraper import RedditScraper
from .model_manager import ModelManager
from .persona_generator import PersonaGenerator
from .file_manager import FileManager
from .reddit_persona_generator import RedditPersonaGenerator
from .web_interface import start_web_interface

__version__ = "1.0.0"
__author__ = "Reddit Persona Generator Team"

__all__ = [
    "Config",
    "RedditScraper",
    "ModelManager", 
    "PersonaGenerator",
    "FileManager",
    "RedditPersonaGenerator",
    "start_web_interface"
]
