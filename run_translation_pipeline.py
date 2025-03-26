#!/usr/bin/env python3
"""
Run Translation Pipeline

This script executes the full translation pipeline from extraction to validation,
providing a command-line interface to the TranslationPipeline class.
"""

import os
import sys
import argparse
import logging
from typing import List
from utils.config.config import Config
from core.translation_pipeline import TranslationPipeline
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("translation_pipeline")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the full translation pipeline")
    
    # Required arguments
    parser.add_argument("--source", required=True, 
                        help="Directory containing source JSON files")
    parser.add_argument("--languages", required=True, 
                        help="Comma-separated list of target languages")
    parser.add_argument("--output", required=True, 
                        help="Output directory for translated files")
    
    # Optional arguments
    parser.add_argument("--options-count", type=int, default=3, 
                        help="Number of translation options to generate")
    parser.add_argument("--batch-size", type=int, default=20, 
                        help="Number of strings to translate in each batch")
    parser.add_argument("--project-description", 
                        help="Description of the project for context generation")
    parser.add_argument("--regenerate-context", action="store_true", 
                        help="Regenerate context even if project description is not provided")
    parser.add_argument("--prompt-config-path", 
                        help="Path to prompt configuration file")
    
    # Model settings
    parser.add_argument("--options-model", 
                        help="Model to use for generating translation options")
    parser.add_argument("--selection-model", 
                        help="Model to use for selecting the best translations")
    parser.add_argument("--refinement-model", 
                        help="Model to use for refining translations")
    parser.add_argument("--validation-model", 
                        help="Model to use for validating translations")
    parser.add_argument("--context-model", 
                        help="Model to use for generating context")
    
    # Debug options
    parser.add_argument("--debug", action="store_true", 
                        help="Enable debug logging")
    parser.add_argument("--mock", action="store_true",
                        help="Run in mock mode without making real API calls")
    
    return parser.parse_args()

def create_config_from_args(args):
    """
    Create a Config object from command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Config object
    """
    # Create the base Config object
    config = Config()
    
    # Set basic settings
    config.input_dir = args.source
    config.output_dir = args.output
    config.languages = args.languages.split(",")
    
    # Set processing settings
    config.options_count = args.options_count
    config.batch_size = args.batch_size
    
    # Set context settings
    if args.project_description:
        config.project_description = args.project_description
    config.regenerate_context = args.regenerate_context
    if args.prompt_config_path:
        config.prompt_config_path = args.prompt_config_path
    
    # Set model settings if provided
    if args.options_model:
        config.options_model = args.options_model
    if args.selection_model:
        config.selection_model = args.selection_model
    if args.refinement_model:
        config.refinement_model = args.refinement_model
    if args.validation_model:
        config.validation_model = args.validation_model
    if args.context_model:
        config.context_generator_model = args.context_model
    
    # Set mock mode if requested
    config.mock_mode = args.mock
    
    return config

def main():
    """Main function to run the translation pipeline."""
    # Parse command line arguments
    args = parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Load environment variables and check API key
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not args.mock and not api_key:
        logger.error("No OpenAI API key found. Please set OPENAI_API_KEY in your .env file or use --mock mode.")
        return 1
    
    if not args.mock and api_key:
        # Verify the API key format
        if "mock" in api_key.lower() or api_key == "your_api_key":
            logger.warning("API key appears to be a placeholder. Using mock mode instead.")
            args.mock = True
        elif '\n' in api_key or ' ' in api_key:
            # Clean up the key
            cleaned_key = api_key.replace('\n', '').replace(' ', '')
            logger.info("API key contains newlines or spaces. Using cleaned version.")
            os.environ["OPENAI_API_KEY"] = cleaned_key
        else:
            # Log partial key for verification
            logger.debug(f"Using API key: {api_key[:7]}...{api_key[-4:] if len(api_key) > 10 else '****'}")
    
    # Create configuration
    try:
        config = create_config_from_args(args)
        logger.info(f"Configuration created for {len(config.languages)} languages")
    except Exception as e:
        logger.error(f"Error creating configuration: {str(e)}")
        return 1
    
    # Initialize and run the pipeline
    try:
        pipeline = TranslationPipeline(config)
        logger.info("Translation pipeline initialized")
        
        results = pipeline.process_directory()
        
        if not results:
            logger.warning("No results returned from pipeline")
            return 1
        
        logger.info(f"Translation pipeline completed successfully")
        
        # Print summary of results
        total_files = len(results)
        total_languages = len(config.languages)
        logger.info(f"Processed {total_files} files into {total_languages} languages")
        logger.info(f"Output saved to {config.output_dir}")
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error running translation pipeline: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1) 