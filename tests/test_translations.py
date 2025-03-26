#!/usr/bin/env python3
"""
Test script to verify the translation functionality.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_translations")

# Import necessary modules
from core.json.json_extractor import process_json_files
from core.json.json_generator import generate_translated_jsons, load_language_codes

def test_translation_pipeline():
    """Test the basic translation pipeline."""
    # Test parameters
    source_dir = "examples/en"
    languages = ["Spanish", "French"]
    output_dir = "examples/test_output"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Extract strings from source files
    logger.info("Step 1: Extracting strings from source files...")
    try:
        extracted_strings, json_files = process_json_files(source_dir)
        
        # Check if extraction was successful
        if not extracted_strings:
            logger.error("No strings extracted from source files")
            return False
        
        logger.info(f"Successfully extracted strings from {len(extracted_strings)} files")
    except Exception as e:
        logger.error(f"Error extracting strings: {str(e)}")
        return False
    
    # Step 2: Create mock translations
    logger.info("Step 2: Creating mock translations...")
    try:
        refined_translations = {}
        for filename, paths in extracted_strings.items():
            refined_translations[filename] = {}
            for path, value in paths.items():
                refined_translations[filename][path] = {}
                for language in languages:
                    refined_translations[filename][path][language] = f"[TEST-{language}] {value}"
        
        logger.info("Successfully created mock translations")
    except Exception as e:
        logger.error(f"Error creating mock translations: {str(e)}")
        return False
    
    # Step 3: Generate translated JSON files
    logger.info("Step 3: Generating translated JSON files...")
    try:
        translated_jsons = generate_translated_jsons(
            refined_translations,
            json_files,
            languages,
            output_dir
        )
        
        logger.info(f"Successfully generated translated files in {output_dir}")
    except Exception as e:
        logger.error(f"Error generating translated files: {str(e)}")
        return False
    
    # Step 4: Verify translated files exist
    logger.info("Step 4: Verifying translated files...")
    for language in languages:
        language_code = load_language_codes().get(language, language.lower())
        lang_dir = os.path.join(output_dir, language_code)
        
        if not os.path.isdir(lang_dir):
            logger.error(f"Language directory {lang_dir} not found")
            return False
        
        for filename in extracted_strings.keys():
            translated_file = os.path.join(lang_dir, filename)
            if not os.path.isfile(translated_file):
                logger.error(f"Translated file {translated_file} not found")
                return False
            
            # Check file content
            try:
                with open(translated_file, 'r', encoding='utf-8') as f:
                    translated_data = json.load(f)
                logger.info(f"Successfully verified {translated_file}")
            except Exception as e:
                logger.error(f"Error reading translated file {translated_file}: {str(e)}")
                return False
    
    logger.info("All tests passed successfully!")
    return True

def main():
    """Run all tests."""
    success = test_translation_pipeline()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 