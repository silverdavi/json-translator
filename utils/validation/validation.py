"""
Utility functions for validating configuration and environment.
These checks run before the main process to ensure all prerequisites are met.
"""

import os
import json
import logging
from typing import Optional
from openai import OpenAI
import time

def test_openai_access(api_key: str) -> bool:
    """
    Test OpenAI API access by making a simple completion request.
    
    Args:
        api_key: OpenAI API key to test
        
    Returns:
        Boolean indicating whether the API key is valid and working
    """
    try:
        from utils.api.util_call import call_openai
        
        # Create a simple test prompt that includes the word 'json' for response_format compatibility
        test_prompt = {
            "system": "You are a helpful assistant. Please respond with a simple JSON test message.",
            "user": "Return a simple JSON test response.",
            "response_format": {"type": "json_object"}
        }
        
        # Use the proper API wrapper with rate limiting
        response = call_openai(
            prompt=test_prompt,
            model="gpt-4o",
            timeout=10  # Add a reasonable timeout
        )
        
        # If we got here, the API call was successful
        return True
    except Exception as e:
        logging.error(f"OpenAI API access test failed: {str(e)}")
        return False

def run_preflight_checks(
    input_dir: str,
    output_dir: str,
    prompt_config: Optional[str] = None,
    mock_mode: bool = False
) -> bool:
    """
    Run checks to validate configuration and environment before launching the pipeline.
    
    Args:
        input_dir: Input directory containing JSON files
        output_dir: Output directory for generated files
        prompt_config: Optional custom prompt configuration file
        mock_mode: Whether to run in mock mode without API calls
        
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
    
    # Check API key and access if not in mock mode
    if not mock_mode:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logging.error("OPENAI_API_KEY not found in environment variables")
            checks_passed = False
        else:
            # Verify API key format
            if not api_key.startswith(("sk-", "sk-proj-")):
                logging.error("Invalid OpenAI API key format. Key should start with 'sk-' or 'sk-proj-'")
                checks_passed = False
            else:
                # Test API access
                logging.info("Testing OpenAI API access...")
                if not test_openai_access(api_key):
                    logging.error("Failed to connect to OpenAI API. Please check your API key and internet connection.")
                    checks_passed = False
                else:
                    logging.info("OpenAI API access verified successfully")
    
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