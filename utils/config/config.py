"""
Configuration module for the JSON translation pipeline.
Centralizes configuration loading, environment setup, and directory management.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.info("dotenv package not found, skipping .env file loading")

# Default directories
DEFAULT_INPUT_DIR = "examples/en"
DEFAULT_OUTPUT_DIR = "examples/output"
DEFAULT_OPTIONS_COUNT = 3

# API configuration
API_CONFIG = {
    "openai": {
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "defaults": {
            "options_model": os.environ.get("OPTIONS_MODEL", "o1"),
            "selection_model": os.environ.get("SELECTION_MODEL", "gpt-4o"),
            "refinement_model": os.environ.get("REFINEMENT_MODEL", "o1"),
            "validation_model": os.environ.get("VALIDATION_MODEL", "gpt-4o"),
            "context_generator_model": os.environ.get("CONTEXT_MODEL", "gpt-4o"),
            "min_delay": float(os.environ.get("MIN_DELAY", "0.5")),
            "max_retries": int(os.environ.get("MAX_RETRIES", "3")),
            "retry_delay": int(os.environ.get("RETRY_DELAY", "1"))
        }
    }
}

@dataclass
class Config:
    """Configuration data class for the translation pipeline."""
    
    # Basic settings
    input_dir: str = DEFAULT_INPUT_DIR
    output_dir: str = DEFAULT_OUTPUT_DIR
    languages: List[str] = field(default_factory=list)
    
    # Model settings
    options_model: str = API_CONFIG["openai"]["defaults"]["options_model"]
    selection_model: str = API_CONFIG["openai"]["defaults"]["selection_model"]
    refinement_model: str = API_CONFIG["openai"]["defaults"]["refinement_model"]
    validation_model: str = API_CONFIG["openai"]["defaults"]["validation_model"]
    context_generator_model: str = API_CONFIG["openai"]["defaults"]["context_generator_model"]
    
    # Processing settings
    options_count: int = DEFAULT_OPTIONS_COUNT
    batch_size: int = 20
    
    # Context settings
    project_description: Optional[str] = None
    regenerate_context: bool = False
    prompt_config_path: Optional[str] = None


def get_output_dirs(base_output_dir: str) -> Dict[str, str]:
    """
    Create and return the output directory structure.
    
    Args:
        base_output_dir: Base output directory
        
    Returns:
        Dictionary of output directories
    """
    dirs = {
        "extracted": os.path.join(base_output_dir, "extracted"),
        "options": os.path.join(base_output_dir, "options"),
        "selected": os.path.join(base_output_dir, "selected"),
        "refined": os.path.join(base_output_dir, "refined"),
        "final": base_output_dir,
        "validated": os.path.join(base_output_dir, "validated"),
        "logs": os.path.join(base_output_dir, "logs")
    }
    
    # Create directories if they don't exist
    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)
    
    return dirs


def load_config(config_path: str) -> Config:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the JSON configuration file
        
    Returns:
        Configuration object
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = json.load(f)
    
    # Convert to Config object
    return Config(**config_dict)


def save_config(config: Config, config_path: str) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration object
        config_path: Path to save the JSON configuration file
    """
    # Convert Config to dictionary
    config_dict = {k: v for k, v in config.__dict__.items()}
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2) 