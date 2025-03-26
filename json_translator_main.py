"""
Main entry point for the JSON translation pipeline.
Coordinates the translation workflow from extraction to validation.
"""

import os
import json
import datetime
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import sys

# Import configuration
from config import (
    API_CONFIG, 
    DEFAULT_INPUT_DIR, 
    DEFAULT_OUTPUT_DIR, 
    DEFAULT_OPTIONS_COUNT,
    get_output_dirs
)

# Import modules for each pipeline step
from json_extractor import extract_strings
from translation_generator import generate_translation_options
from translation_selector import select_best_translations
from translation_refiner import refine_translations
from json_generator import generate_translated_jsons
from translation_validator import validate_translations
from report_generator import generate_summary_report
from context_generator import generate_context_configuration
from utils.logging_config import setup_logging, model_usage
from utils.validation import run_preflight_checks
from translation_pipeline import TranslationPipeline
from config import Config


def run_translation_pipeline(
        input_dir: str,
        output_dir: str,
        languages: List[str],
        options_model: Optional[str] = None,
        selection_model: Optional[str] = None,
        refinement_model: Optional[str] = None,
        validation_model: Optional[str] = None,
        options_count: int = DEFAULT_OPTIONS_COUNT,
        project_description: Optional[str] = None,
        regenerate_context: bool = False
):
    """
    Run the complete translation pipeline.
    
    Args:
        input_dir: Directory containing input JSON files
        output_dir: Directory for output files
        languages: List of target languages
        options_model: Model for generating translation options
        selection_model: Model for selecting best translations
        refinement_model: Model for refining translations
        validation_model: Model for validating translations
        options_count: Number of translation options to generate
        project_description: Description of the project for context generation
        regenerate_context: Whether to regenerate context configuration
    """
    start_time = datetime.datetime.now()
    print(f"Starting translation pipeline at {start_time}")

    # Get default models from config if not provided
    openai_defaults = API_CONFIG.get("openai", {}).get("defaults", {})
    options_model = options_model or openai_defaults.get("options_model", "o1")
    selection_model = selection_model or openai_defaults.get("selection_model", "gpt-4o")
    refinement_model = refinement_model or openai_defaults.get("refinement_model", "o1")
    validation_model = validation_model or openai_defaults.get("validation_model", "gpt-4o")
    
    # Generate specialized context if provided or regeneration requested
    if project_description or regenerate_context:
        print("\nGenerating specialized context for the translation...")
        # Use a higher quality model for context generation
        context_model = openai_defaults.get("context_generator_model", "gpt-4o")
        context_config = generate_context_configuration(
            project_description=project_description,
            model=context_model,
            save_to_file=True
        )
        project_context = context_config.get("default_project_context", "")
        print("Context generation complete.")
    else:
        # Use existing context configuration
        project_context = None

    # Create output directories
    dirs = get_output_dirs(output_dir)

    # Load JSON files
    json_files = load_json_files(input_dir)

    # Step 1: Extract strings for translation
    print("\nStep 1: Extracting strings for translation...")
    extracted = extract_strings(json_files, dirs["extracted"])

    # Step 2: Generate translation options
    print("\nStep 2: Generating translation options...")
    options = generate_translation_options(
        extracted,
        languages,
        options_model,
        options_count,
        dirs["options"],
        project_context
    )

    # Step 3: Select best translations
    print("\nStep 3: Selecting best translations...")
    selected = select_best_translations(
        options,
        json_files,
        languages,
        selection_model,
        dirs["selected"],
        project_context
    )

    # Step 4: Refine translations
    print("\nStep 4: Refining translations...")
    refined = refine_translations(
        selected,
        json_files,
        languages,
        refinement_model,
        dirs["refined"],
        project_context
    )

    # Step 5: Generate translated JSON files
    print("\nStep 5: Generating translated JSON files...")
    translated_jsons = generate_translated_jsons(
        refined,
        json_files,
        languages,
        dirs["final"]
    )

    # Step 6: Validate translations
    print("\nStep 6: Validating translations...")
    validation_results = validate_translations(
        translated_jsons,
        json_files,
        languages,
        validation_model,
        dirs["validated"],
        project_context
    )

    # Generate summary report
    print("\nGenerating summary report...")
    generate_summary_report(
        validation_results,
        input_dir,
        output_dir,
        languages,
        list(json_files.keys()),
        {
            "options_generation": options_model,
            "selection": selection_model,
            "refinement": refinement_model,
            "validation": validation_model
        },
        dirs["logs"]
    )

    end_time = datetime.datetime.now()
    duration = end_time - start_time
    print(f"\nTranslation pipeline completed at {end_time}")
    print(f"Total duration: {duration}")


def load_json_files(input_dir: str) -> Dict[str, Dict]:
    """
    Load all JSON files from the input directory.
    
    Args:
        input_dir: Directory containing JSON files
        
    Returns:
        Dictionary mapping filenames to JSON data
        
    Raises:
        RuntimeError: If no valid JSON files could be loaded
    """
    json_files = {}
    errors = []

    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(input_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        errors.append(f"Error in {filename}: JSON root must be an object")
                        continue
                    json_files[filename] = data
                    print(f"Loaded {filename}")
            except json.JSONDecodeError as e:
                errors.append(f"Error in {filename}: Invalid JSON format - {str(e)}")
            except UnicodeDecodeError as e:
                errors.append(f"Error in {filename}: Invalid file encoding - {str(e)}")
            except PermissionError as e:
                errors.append(f"Error in {filename}: Permission denied - {str(e)}")
            except Exception as e:
                errors.append(f"Unexpected error in {filename}: {str(e)}")

    if errors:
        print("\nErrors encountered while loading JSON files:")
        for error in errors:
            print(f"- {error}")
        if not json_files:
            raise RuntimeError("No valid JSON files could be loaded")

    return json_files


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Translate JSON files to multiple languages")
    parser.add_argument("--input-dir", required=True, help="Input directory containing JSON files")
    parser.add_argument("--output-dir", required=True, help="Output directory for translated files")
    parser.add_argument("--languages", required=True, help="Comma-separated list of target languages")
    parser.add_argument("--project-description", help="Description of the project for context generation")
    parser.add_argument("--options-model", default="o1", help="Model to use for generating translation options")
    parser.add_argument("--selection-model", default="gpt-4o", help="Model to use for selecting best translation")
    parser.add_argument("--refinement-model", default="o1", help="Model to use for refining translations")
    parser.add_argument("--validation-model", default="gpt-4o", help="Model to use for validating translations")
    parser.add_argument("--options-count", type=int, default=4, help="Number of translation options to generate")
    parser.add_argument("--batch-size", type=int, default=20, help="Number of strings to process in each batch")
    parser.add_argument("--regenerate-context", action="store_true", help="Force regeneration of context configuration")
    parser.add_argument("--prompt-config", help="Path to custom prompt configuration file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                      help="Set the logging level")
    return parser.parse_args()


def main() -> None:
    """Main entry point for the translation pipeline."""
    # Parse arguments
    args = parse_args()
    
    # Set up logging
    setup_logging(log_level=args.log_level)
    logging.info("Starting JSON Translation Pipeline")
    
    try:
        # Run pre-flight checks
        if not run_preflight_checks(args.input_dir, args.output_dir, args.prompt_config):
            logging.error("Pre-flight checks failed. Exiting.")
            sys.exit(1)
        
        # Initialize configuration
        config = Config(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            languages=args.languages.split(","),
            options_model=args.options_model,
            selection_model=args.selection_model,
            refinement_model=args.refinement_model,
            validation_model=args.validation_model,
            options_count=args.options_count,
            batch_size=args.batch_size,
            project_description=args.project_description,
            regenerate_context=args.regenerate_context,
            prompt_config_path=args.prompt_config
        )
        
        # Initialize and run pipeline
        pipeline = TranslationPipeline(config)
        
        # Process files with progress bar
        input_files = list(Path(args.input_dir).glob("**/*.json"))
        with tqdm(total=len(input_files), desc="Processing files", unit="file") as pbar:
            for file_path in input_files:
                try:
                    pipeline.process_file(file_path)
                    pbar.update(1)
                except Exception as e:
                    logging.error(f"Error processing file {file_path}: {str(e)}")
                    continue
        
        # Print model usage summary
        model_usage.print_summary()
        
        logging.info("Translation pipeline completed successfully")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()