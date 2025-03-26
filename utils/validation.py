import os
import sys
from pathlib import Path
from typing import List, Optional
import logging
from dotenv import load_dotenv

def validate_environment() -> bool:
    """
    Validate the environment setup and API keys.
    
    Returns:
        bool: True if all validations pass, False otherwise
    """
    logging.info("Starting environment validation...")
    
    # Load environment variables
    load_dotenv()
    
    # Check Python version
    if sys.version_info < (3, 8):
        logging.error(f"Python version {sys.version_info.major}.{sys.version_info.minor} is not supported. Please use Python 3.8 or higher.")
        return False
    
    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY not found in environment variables")
        return False
    if api_key == "your_openai_api_key_here":
        logging.error("Please replace the default OpenAI API key in your .env file")
        return False
    
    # Test OpenAI API connection
    try:
        import openai
        openai.api_key = api_key
        # Make a minimal API call to test the connection
        openai.models.list()
        logging.info("OpenAI API connection successful")
    except Exception as e:
        logging.error(f"Failed to connect to OpenAI API: {str(e)}")
        return False
    
    return True

def validate_paths(
    input_dir: str,
    output_dir: str,
    prompt_config_path: Optional[str] = None
) -> bool:
    """
    Validate input/output paths and permissions.
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        prompt_config_path: Optional path to prompt configuration file
    
    Returns:
        bool: True if all validations pass, False otherwise
    """
    logging.info("Starting path validation...")
    
    # Validate input directory
    input_path = Path(input_dir)
    if not input_path.exists():
        logging.error(f"Input directory does not exist: {input_dir}")
        return False
    if not input_path.is_dir():
        logging.error(f"Input path is not a directory: {input_dir}")
        return False
    if not os.access(input_path, os.R_OK):
        logging.error(f"No read permission for input directory: {input_dir}")
        return False
    
    # Validate output directory
    output_path = Path(output_dir)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        if not os.access(output_path, os.W_OK):
            logging.error(f"No write permission for output directory: {output_dir}")
            return False
    except Exception as e:
        logging.error(f"Failed to create output directory: {str(e)}")
        return False
    
    # Validate prompt config if provided
    if prompt_config_path:
        prompt_path = Path(prompt_config_path)
        if not prompt_path.exists():
            logging.error(f"Prompt configuration file does not exist: {prompt_config_path}")
            return False
        if not os.access(prompt_path, os.R_OK):
            logging.error(f"No read permission for prompt configuration file: {prompt_config_path}")
            return False
    
    logging.info("Path validation successful")
    return True

def validate_json_files(input_dir: str) -> List[str]:
    """
    Validate JSON files in the input directory.
    
    Args:
        input_dir: Input directory path
    
    Returns:
        List[str]: List of valid JSON file paths
    """
    import json
    valid_files = []
    
    logging.info(f"Validating JSON files in {input_dir}...")
    
    for file_path in Path(input_dir).glob("**/*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            valid_files.append(str(file_path))
            logging.debug(f"Valid JSON file: {file_path}")
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON file {file_path}: {str(e)}")
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {str(e)}")
    
    if not valid_files:
        logging.warning("No valid JSON files found in input directory")
    else:
        logging.info(f"Found {len(valid_files)} valid JSON files")
    
    return valid_files

def run_preflight_checks(
    input_dir: str,
    output_dir: str,
    prompt_config_path: Optional[str] = None
) -> bool:
    """
    Run all pre-flight checks before starting the pipeline.
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        prompt_config_path: Optional path to prompt configuration file
    
    Returns:
        bool: True if all checks pass, False otherwise
    """
    logging.info("Starting pre-flight checks...")
    
    # Run environment validation
    if not validate_environment():
        logging.error("Environment validation failed")
        return False
    
    # Run path validation
    if not validate_paths(input_dir, output_dir, prompt_config_path):
        logging.error("Path validation failed")
        return False
    
    # Validate JSON files
    valid_files = validate_json_files(input_dir)
    if not valid_files:
        logging.error("No valid JSON files found")
        return False
    
    logging.info("All pre-flight checks passed successfully")
    return True 