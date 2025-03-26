"""
Utility functions for validating configuration and environment.
These checks run before the main process to ensure all prerequisites are met.
"""

import os
import json
import logging
from typing import Optional

def run_preflight_checks(
    input_dir: str,
    output_dir: str,
    prompt_config: Optional[str] = None,
) -> bool:
    """
    Run checks to validate configuration and environment before launching the pipeline.
    
    Args:
        input_dir: Input directory containing JSON files
        output_dir: Output directory for generated files
        prompt_config: Optional custom prompt configuration file
        
    Returns:
        Boolean indicating whether all checks passed
    """
    checks_passed = True
    
    # Check input directory
    if not os.path.exists(input_dir):
        logging.error(f"Input directory does not exist: {input_dir}")
        checks_passed = False
    elif not os.path.isdir(input_dir):
        logging.error(f"Input path is not a directory: {input_dir}")
        checks_passed = False
    elif not any(f.endswith('.json') for f in os.listdir(input_dir)):
        logging.warning(f"No JSON files found in input directory: {input_dir}")
    
    # Check output directory
    if os.path.exists(output_dir) and not os.path.isdir(output_dir):
        logging.error(f"Output path exists but is not a directory: {output_dir}")
        checks_passed = False
    elif not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Created output directory: {output_dir}")
        except Exception as e:
            logging.error(f"Failed to create output directory: {e}")
            checks_passed = False
    
    # Check prompt configuration if provided
    if prompt_config and not os.path.exists(prompt_config):
        logging.error(f"Prompt configuration file not found: {prompt_config}")
        checks_passed = False
    elif prompt_config:
        try:
            with open(prompt_config, 'r', encoding='utf-8') as f:
                json.load(f)  # Validate JSON format
            logging.info(f"Prompt configuration file validated: {prompt_config}")
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format in prompt configuration: {prompt_config}")
            checks_passed = False
        except Exception as e:
            logging.error(f"Error reading prompt configuration: {e}")
            checks_passed = False
    
    # Check API keys and environment
    if "OPENAI_API_KEY" not in os.environ and not os.path.exists(".env"):
        logging.warning("OPENAI_API_KEY not found in environment variables or .env file")
        logging.warning("You will need to provide an API key in the configuration")
    
    # Print check results
    if checks_passed:
        logging.info("All pre-flight checks passed successfully")
    else:
        logging.error("Some pre-flight checks failed")
    
    return checks_passed

def validate_languages(languages: list) -> list:
    """
    Validate the list of target languages.
    
    Args:
        languages: List of language codes or names
        
    Returns:
        Validated and normalized list of languages
    """
    # Make a copy to avoid modifying the original
    validated_languages = list(languages)
    
    # Normalize language names
    for i, lang in enumerate(validated_languages):
        # Capitalize first letter of each word
        validated_languages[i] = ' '.join(word.capitalize() for word in lang.split())
    
    # Log warning for any potentially unsupported languages
    standard_languages = {
        "Thai", "Malay", "Simplified Chinese", "Traditional Chinese", 
        "Hebrew", "Spanish", "French", "German", "Italian", "Japanese",
        "Korean", "Portuguese", "Russian", "Arabic", "English", "Dutch",
        "Vietnamese", "Indonesian", "Greek", "Turkish", "Hindi", "Bengali",
        "Polish", "Swedish", "Norwegian", "Danish", "Finnish", "Burmese"
    }
    
    for lang in validated_languages:
        if lang not in standard_languages:
            logging.warning(f"Language '{lang}' might not be fully supported")
    
    return validated_languages 