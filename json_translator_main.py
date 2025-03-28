#!/usr/bin/env python3
"""
JSON Translator - Main Script

This script orchestrates the full JSON translation process:
1. Extract strings from source JSON files
2. Translate the strings to target languages
3. Generate translated JSON files
"""

import os
import sys
import argparse
import logging
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Import core modules
from core.json.json_extractor import process_json_files
from core.json.json_generator import generate_translated_jsons, load_language_codes
from utils.validation.validation import run_preflight_checks
from utils.api.util_call import call_openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("json_translator")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Translate JSON files to multiple languages")
    parser.add_argument("--source", required=True, help="Directory containing source JSON files")
    parser.add_argument("--languages", required=True, help="Comma-separated list of target languages")
    parser.add_argument("--output", required=True, help="Output directory for translated files")
    parser.add_argument("--options-count", type=int, default=3, help="Number of translation options to generate")
    parser.add_argument("--model", default="gpt-4o", help="LLM model to use for translation")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without API calls")
    parser.add_argument("--check-only", action="store_true", help="Run only preflight checks without translation")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of strings to translate in each batch")
    return parser.parse_args()

def setup_environment():
    """Set up the environment and load environment variables."""
    # Load environment variables from .env file
    load_dotenv(override=True)  # Add override=True to force reload
    
    # Check if API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables.")
        return False
    
    # Verify that the API key is not a placeholder or contains invalid characters
    if "mock" in api_key.lower() or api_key == "your_api_key":
        logger.warning("API key appears to be a placeholder value. Please set a valid API key.")
        return False
    
    # Basic format validation
    if not api_key.startswith(("sk-", "sk-proj-")):
        logger.warning(f"OPENAI_API_KEY has incorrect format. OpenAI keys should start with 'sk-' or 'sk-proj-'.")
        return False
    
    # Check for newlines or spaces which could cause problems
    if '\n' in api_key or ' ' in api_key:
        logger.warning("OPENAI_API_KEY contains newlines or spaces which will cause API errors.")
        # Try to clean up the key
        cleaned_key = api_key.replace('\n', '').replace(' ', '')
        logger.info("Attempting to use cleaned API key...")
        os.environ["OPENAI_API_KEY"] = cleaned_key
    
    logger.debug(f"Using API key: {api_key[:7]}...{api_key[-4:]}")
    return True

def validate_languages(languages: List[str]) -> List[str]:
    """
    Validate the provided languages against available language codes.
    
    Args:
        languages: List of languages to validate
        
    Returns:
        Validated list of languages
    """
    language_codes = load_language_codes()
    valid_languages = []
    
    # Add common aliases
    language_aliases = {
        "chinese": ["Simplified Chinese", "Chinese"],
        "simplified chinese": ["Simplified Chinese"],
        "traditional chinese": ["Traditional Chinese"],
        "mandarin": ["Simplified Chinese"],
        "cantonese": ["Traditional Chinese"],
        "taiwanese": ["Traditional Chinese"],
        "zh": ["Simplified Chinese"],
        "zh-cn": ["Simplified Chinese"],
        "zh-tw": ["Traditional Chinese"],
        "spain": ["Spanish"],
        "brazilian": ["Portuguese"],
        "brasil": ["Portuguese"]
    }
    
    for language in languages:
        language = language.strip()
        # Check for exact match
        if language in language_codes:
            valid_languages.append(language)
        else:
            # Check for aliases
            language_lower = language.lower()
            if language_lower in language_aliases:
                matched_language = language_aliases[language_lower][0]
                logger.info(f"Using '{matched_language}' instead of '{language}'")
                valid_languages.append(matched_language)
            else:
                # Try to find a case-insensitive match
                matches = [lang for lang in language_codes.keys() 
                        if lang.lower() == language.lower()]
                if matches:
                    logger.info(f"Using '{matches[0]}' instead of '{language}'")
                    valid_languages.append(matches[0])
                else:
                    logger.warning(f"Language '{language}' not found in language codes. "
                                f"Will use as provided, but translation quality may be affected.")
                    valid_languages.append(language)
    
    return valid_languages

def translate_strings(strings: Dict[str, str], language: str, model: str, batch_size: int = 10) -> Dict[str, str]:
    """
    Translate a dictionary of strings to the target language using the OpenAI API.
    
    Args:
        strings: Dictionary mapping paths to source strings
        language: Target language for translation
        model: LLM model to use for translation
        batch_size: Number of strings to translate in each batch
        
    Returns:
        Dictionary mapping paths to translated strings
    """
    # Prepare batches
    paths = list(strings.keys())
    values = list(strings.values())
    translations = {}
    
    for i in range(0, len(paths), batch_size):
        batch_paths = paths[i:i + batch_size]
        batch_values = values[i:i + batch_size]
        
        # Create the translation prompt
        prompt = {
            "system": f"You are a professional translator. Translate the following English text to {language}.",
            "user": json.dumps(batch_values, ensure_ascii=False),
            "response_format": {"type": "json_object"}
        }
        
        try:
            # Use the proper API wrapper with rate limiting
            response = call_openai(
                prompt=prompt,
                model=model,
                timeout=30  # Add a reasonable timeout
            )
            
            # Parse the response
            batch_translations = json.loads(response)
            
            # Map translations back to paths
            for path, translation in zip(batch_paths, batch_translations):
                translations[path] = translation
                
        except Exception as e:
            logger.error(f"Error translating batch: {str(e)}")
            # On error, use original text as fallback
            for path in batch_paths:
                translations[path] = strings[path]
    
    return translations

def main():
    """Main function to run the translation pipeline."""
    # Parse command line arguments
    args = parse_args()
    
    # Set logging level based on arguments
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Setup environment
    logger.info("Setting up environment...")
    env_ok = setup_environment()
    if not env_ok and not args.mock:
        logger.warning("Environment setup incomplete. Running in mock mode.")
        args.mock = True
    
    # Run preflight checks
    logger.info("Running preflight checks...")
    checks_passed = run_preflight_checks(args.source, args.output)
    if not checks_passed:
        logger.error("Preflight checks failed. Please fix the issues and try again.")
        return 1
    
    # If check-only mode, exit here
    if args.check_only:
        logger.info("Preflight checks completed successfully. Exiting in check-only mode.")
        return 0
    
    # Split and validate languages
    raw_languages = args.languages.split(",")
    languages = validate_languages(raw_languages)
    logger.info(f"Target languages: {', '.join(languages)}")
    
    # Process source JSON files
    logger.info(f"Processing JSON files from {args.source}...")
    try:
        extracted_strings, json_files = process_json_files(args.source)
    except Exception as e:
        logger.error(f"Error processing JSON files: {str(e)}")
        return 1
    
    # Display extracted information
    total_strings = sum(len(strings) for strings in extracted_strings.values())
    total_files = len(extracted_strings)
    logger.info(f"Extracted {total_strings} strings from {total_files} files.")
    
    # If no strings found, exit
    if total_strings == 0:
        logger.warning("No strings found to translate. Check your source files.")
        return 1
    
    # Perform translations
    refined_translations = {}
    
    if args.mock:
        # Use mock translations
        logger.info("Running in mock mode with placeholder translations.")
        for filename, paths in extracted_strings.items():
            refined_translations[filename] = {}
            for path, value in paths.items():
                refined_translations[filename][path] = {}
                for language in languages:
                    # Mock translation
                    refined_translations[filename][path][language] = f"[{language}] {value}"
    else:
        # Use real translations
        logger.info("Starting translation process...")
        for filename, paths in extracted_strings.items():
            logger.info(f"Translating {filename}...")
            refined_translations[filename] = {}
            
            for language in languages:
                logger.info(f"Translating to {language}...")
                translations = translate_strings(
                    paths, language, args.model, args.batch_size
                )
                
                # Store translations
                for path, translation in translations.items():
                    if path not in refined_translations[filename]:
                        refined_translations[filename][path] = {}
                    refined_translations[filename][path][language] = translation
    
    # Generate translated JSON files
    logger.info(f"Generating translated JSON files in {args.output}...")
    try:
        translated_jsons = generate_translated_jsons(
            refined_translations,
            json_files,
            languages,
            args.output
        )
    except Exception as e:
        logger.error(f"Error generating translated files: {str(e)}")
        return 1
    
    logger.info(f"Translation complete. Files saved to {args.output}")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)