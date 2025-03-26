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
    load_dotenv()
    
    # Check if API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables.")
        return False
    
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
    
    for language in languages:
        language = language.strip()
        # Check for exact match
        if language in language_codes:
            valid_languages.append(language)
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
    # Initialize OpenAI client
    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    # Prepare batches
    paths = list(strings.keys())
    values = list(strings.values())
    translations = {}
    
    for i in range(0, len(paths), batch_size):
        batch_paths = paths[i:i+batch_size]
        batch_values = values[i:i+batch_size]
        
        # Prepare the prompt
        source_text = "\n".join([f"{j+1}. {text}" for j, text in enumerate(batch_values)])
        prompt = [
            {"role": "system", "content": f"You are an expert translator to {language}. Translate the following texts to {language}. Keep the same format and meaning. Return ONLY the translations numbered the same way as the input."},
            {"role": "user", "content": source_text}
        ]
        
        try:
            # Call the API
            logger.debug(f"Translating batch {i//batch_size + 1} of {(len(paths) - 1)//batch_size + 1} to {language}")
            response = client.chat.completions.create(
                model=model,
                messages=prompt
            )
            
            # Extract translations
            result = response.choices[0].message.content.strip()
            
            # Parse numbered responses
            lines = result.split("\n")
            batch_translations = []
            
            current_translation = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts with a number
                if line[0].isdigit() and "." in line[:5]:
                    if current_translation:
                        batch_translations.append(current_translation.strip())
                    
                    # Start a new translation
                    parts = line.split(".", 1)
                    if len(parts) > 1:
                        current_translation = parts[1].strip()
                    else:
                        current_translation = ""
                else:
                    current_translation += " " + line
            
            # Add the last translation
            if current_translation:
                batch_translations.append(current_translation.strip())
            
            # Make sure we have the right number of translations
            if len(batch_translations) != len(batch_paths):
                logger.warning(f"Expected {len(batch_paths)} translations, but got {len(batch_translations)}. Adjusting...")
                # Adjust the translations array
                if len(batch_translations) < len(batch_paths):
                    batch_translations.extend(["[Translation error]"] * (len(batch_paths) - len(batch_translations)))
                else:
                    batch_translations = batch_translations[:len(batch_paths)]
            
            # Store translations
            for path, translation in zip(batch_paths, batch_translations):
                translations[path] = translation
            
            # Wait a bit to avoid rate limits
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error translating batch: {str(e)}")
            # Add placeholders for failed translations
            for path in batch_paths:
                translations[path] = f"[Error: {str(e)[:50]}...]"
    
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