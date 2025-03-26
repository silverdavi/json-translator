"""
Configuration module for the JSON Translation Pipeline.
Centralizes all settings, paths, and configuration options.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
ROOT_DIR = Path(__file__).parent
DEFAULT_DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_INPUT_DIR = os.path.join(DEFAULT_DATA_DIR, "input")
DEFAULT_OUTPUT_DIR = os.path.join(DEFAULT_DATA_DIR, "output")
DEFAULT_TEST_DIR = os.path.join(ROOT_DIR, "tests", "data")
DEFAULT_PROMPT_CONFIG_PATH = os.path.join(ROOT_DIR, "prompts", "default_prompts.json")

# Create necessary directories
os.makedirs(DEFAULT_INPUT_DIR, exist_ok=True)
os.makedirs(DEFAULT_OUTPUT_DIR, exist_ok=True)

# API Configuration
API_CONFIG = {
    "openai": {
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "defaults": {
            "options_model": os.environ.get("OPENAI_OPTIONS_MODEL", "o1"),
            "selection_model": os.environ.get("OPENAI_SELECTION_MODEL", "gpt-4o"),
            "refinement_model": os.environ.get("OPENAI_REFINEMENT_MODEL", "o1"),
            "validation_model": os.environ.get("OPENAI_VALIDATION_MODEL", "gpt-4o"),
            "context_generator_model": os.environ.get("OPENAI_CONTEXT_GENERATOR_MODEL", "gpt-4o"),
            "min_delay": float(os.environ.get("OPENAI_MIN_DELAY", "0.5")),
            "max_retries": int(os.environ.get("OPENAI_MAX_RETRIES", "3")),
            "retry_delay": int(os.environ.get("OPENAI_RETRY_DELAY", "1")),
        }
    }
}

# Default translation settings
DEFAULT_OPTIONS_COUNT = int(os.environ.get("DEFAULT_OPTIONS_COUNT", "4"))
DEFAULT_BATCH_SIZE = int(os.environ.get("DEFAULT_BATCH_SIZE", "20"))

# Default context description (if no user input is provided)
DEFAULT_PROJECT_DESCRIPTION = """
JSON translation system for localizing application content across multiple languages.
The system extracts strings from JSON files, generates translation options,
selects the best translations, refines them, and then validates the results.
"""

class Config:
    """Configuration class for the translation pipeline."""
    
    def __init__(
        self,
        input_dir: str,
        output_dir: str,
        languages: List[str],
        options_model: Optional[str] = None,
        selection_model: Optional[str] = None,
        refinement_model: Optional[str] = None,
        validation_model: Optional[str] = None,
        options_count: int = DEFAULT_OPTIONS_COUNT,
        batch_size: int = DEFAULT_BATCH_SIZE,
        project_description: Optional[str] = None,
        regenerate_context: bool = False,
        prompt_config_path: Optional[str] = None
    ):
        """
        Initialize configuration settings.
        
        Args:
            input_dir: Directory containing input JSON files
            output_dir: Directory for output files
            languages: List of target languages
            options_model: Model for generating translation options
            selection_model: Model for selecting best translations
            refinement_model: Model for refining translations
            validation_model: Model for validating translations
            options_count: Number of translation options to generate
            batch_size: Number of strings to process in each batch
            project_description: Description of the project for context generation
            regenerate_context: Whether to regenerate context configuration
            prompt_config_path: Path to custom prompt configuration file
        """
        # Get default models from config if not provided
        openai_defaults = API_CONFIG.get("openai", {}).get("defaults", {})
        
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.languages = languages
        self.options_model = options_model or openai_defaults.get("options_model", "o1")
        self.selection_model = selection_model or openai_defaults.get("selection_model", "gpt-4o")
        self.refinement_model = refinement_model or openai_defaults.get("refinement_model", "o1")
        self.validation_model = validation_model or openai_defaults.get("validation_model", "gpt-4o")
        self.context_generator_model = openai_defaults.get("context_generator_model", "gpt-4o")
        self.options_count = options_count
        self.batch_size = batch_size
        self.project_description = project_description
        self.regenerate_context = regenerate_context
        self.prompt_config_path = prompt_config_path or DEFAULT_PROMPT_CONFIG_PATH
        
        # API settings
        self.min_delay = openai_defaults.get("min_delay", 0.5)
        self.max_retries = openai_defaults.get("max_retries", 3)
        self.retry_delay = openai_defaults.get("retry_delay", 1)

def load_prompt_templates(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load prompt templates from a JSON file.
    
    Args:
        path: Path to the JSON file containing prompt templates.
              If None, uses the default path.
    
    Returns:
        Dictionary containing prompt templates
    """
    path = path or DEFAULT_PROMPT_CONFIG_PATH
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # If file doesn't exist, return empty dict (will be created later)
    if not os.path.exists(path):
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
        print(f"Error loading prompt templates: {e}")
        return {}

def save_prompt_templates(templates: Dict[str, Any], path: Optional[str] = None) -> bool:
    """
    Save prompt templates to a JSON file.
    
    Args:
        templates: Dictionary containing prompt templates
        path: Path to save the JSON file. If None, uses the default path.
    
    Returns:
        True if successful, False otherwise
    """
    path = path or DEFAULT_PROMPT_CONFIG_PATH
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)
        return True
    except (PermissionError, OSError) as e:
        print(f"Error saving prompt templates: {e}")
        return False

# Output directory structure
def get_output_dirs(base_output_dir: str) -> Dict[str, str]:
    """
    Create and return paths to all necessary output directories.
    
    Args:
        base_output_dir: Base output directory
    
    Returns:
        Dictionary mapping directory names to their paths
    """
    dirs = {
        "base": base_output_dir,
        "extracted": os.path.join(base_output_dir, "1_extracted_strings"),
        "options": os.path.join(base_output_dir, "2_translation_options"),
        "selected": os.path.join(base_output_dir, "3_selected_translations"),
        "refined": os.path.join(base_output_dir, "4_refined_translations"),
        "final": os.path.join(base_output_dir, "5_final_json"),
        "validated": os.path.join(base_output_dir, "6_validation_results"),
        "logs": os.path.join(base_output_dir, "logs"),
    }

    # Create all directories
    for path in dirs.values():
        os.makedirs(path, exist_ok=True)

    return dirs 