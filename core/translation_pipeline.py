"""
Translation Pipeline module that orchestrates the entire translation process.
This class coordinates all steps of the pipeline from extraction to validation.
"""

import os
import json
import datetime
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from tqdm import tqdm

from utils.config.config import get_output_dirs, Config
from core.json.json_extractor import extract_strings
from core.translation.translation_generator import generate_translation_options
from core.translation.translation_selector import select_best_translations
from core.translation.translation_refiner import refine_translations
from core.json.json_generator import generate_translated_jsons
from core.translation.translation_validator import validate_translations
from utils.reporting.report_generator import generate_summary_report
from utils.config.context_generator import generate_context_configuration
from utils.logging.logging_config import model_usage


class TranslationPipeline:
    """
    Orchestrates the entire translation pipeline from extraction to validation.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the translation pipeline with configuration settings.
        
        Args:
            config: Configuration object with all settings for the pipeline
        """
        self.config = config
        self.output_dirs = get_output_dirs(config.output_dir)
        self.project_context = None
        
        # Generate specialized context if provided or regeneration requested
        if config.project_description or config.regenerate_context:
            logging.info("Generating specialized context for translation...")
            context_model = config.context_generator_model
            context_config = generate_context_configuration(
                project_description=config.project_description,
                model=context_model,
                save_to_file=True,
                prompt_config_path=config.prompt_config_path,
                mock_mode=config.mock_mode
            )
            self.project_context = context_config.get("default_project_context", "")
            logging.info("Context generation complete")
        
        logging.info(f"Translation pipeline initialized with {len(config.languages)} languages")
    
    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a single JSON file through the entire pipeline.
        
        Args:
            file_path: Path to the JSON file to process
            
        Returns:
            Dictionary with validation results for the file
        """
        start_time = datetime.datetime.now()
        file_name = file_path.name
        logging.info(f"Starting translation for {file_name}")
        
        # Load JSON file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                if not isinstance(json_data, dict):
                    raise ValueError("JSON root must be an object")
                json_files = {file_name: json_data}
        except Exception as e:
            logging.error(f"Error loading {file_name}: {str(e)}")
            raise
        
        # Step 1: Extract strings
        logging.info("Step 1: Extracting strings for translation...")
        extracted = extract_strings(json_files, self.output_dirs["extracted"])
        
        # Calculate estimated minimum processing time
        total_strings = sum(len(strings) for strings in extracted.values())
        total_languages = len(self.config.languages)
        
        # Calculate delays:
        # - 5 seconds between languages
        # - 2 seconds between steps (6 steps per language)
        # - 2 seconds initial delay
        delay_between_languages = 5
        delay_between_steps = 2
        initial_delay = 2
        
        total_delays = (
            initial_delay +  # Initial delay
            (total_languages - 1) * delay_between_languages +  # Delays between languages
            total_languages * 6 * delay_between_steps  # Delays between steps for each language
        )
        
        # Estimate API call time (rough estimate of 2 seconds per API call)
        # Each string goes through 4 API calls (options, selection, refinement, validation)
        api_call_time = total_strings * total_languages * 4 * 2
        
        estimated_min_time = total_delays + api_call_time
        
        logging.info(f"\nEstimated minimum processing time:")
        logging.info(f"- Total strings to process: {total_strings}")
        logging.info(f"- Number of languages: {total_languages}")
        logging.info(f"- Total delays: {total_delays} seconds")
        logging.info(f"- Estimated API call time: {api_call_time} seconds")
        logging.info(f"- Total estimated minimum time: {estimated_min_time} seconds ({estimated_min_time/60:.1f} minutes)")
        
        # Process each language sequentially
        options = {}
        selected = {}
        refined = {}
        translated_jsons = {}
        validation_results = {}
        
        for language in self.config.languages:
            logging.info(f"Processing language: {language}")
            
            # Step 2: Generate translation options for this language
            logging.info(f"Step 2: Generating translation options for {language}...")
            lang_options = generate_translation_options(
                extracted,
                [language],  # Process only one language at a time
                self.config.options_model,
                self.config.options_count,
                self.output_dirs["options"],
                self.project_context,
                batch_size=self.config.batch_size,
                mock_mode=self.config.mock_mode
            )
            options.update(lang_options)
            
            # Count words processed
            total_words = sum(
                len(text.split()) * self.config.options_count 
                for strings in extracted.values() 
                for text in strings.values()
            )
            model_usage.add_words(self.config.options_model, total_words)
            
            # Step 3: Select best translations for this language
            logging.info(f"Step 3: Selecting best translations for {language}...")
            lang_selected = select_best_translations(
                lang_options,
                json_files,
                [language],  # Process only one language at a time
                self.config.selection_model,
                self.output_dirs["selected"],
                self.project_context,
                batch_size=self.config.batch_size,
                mock_mode=self.config.mock_mode
            )
            selected.update(lang_selected)
            
            # Count words processed
            total_words = sum(
                len(str(options).split()) 
                for filename, lang_options in lang_options.items()
                if language in lang_options
            )
            model_usage.add_words(self.config.selection_model, total_words)
            
            # Step 4: Refine translations for this language
            logging.info(f"Step 4: Refining translations for {language}...")
            lang_refined = refine_translations(
                lang_selected,
                json_files,
                [language],  # Process only one language at a time
                self.config.refinement_model,
                self.output_dirs["refined"],
                self.project_context,
                batch_size=self.config.batch_size,
                mock_mode=self.config.mock_mode
            )
            refined.update(lang_refined)
            
            # Count words processed
            total_words = sum(
                len(text.split()) 
                for filename, lang_selected in lang_selected.items()
                if language in lang_selected
                for text in lang_selected[language].values()
            )
            model_usage.add_words(self.config.refinement_model, total_words)
            
            # Step 5: Generate translated JSON files for this language
            logging.info(f"Step 5: Generating translated JSON files for {language}...")
            lang_translated = generate_translated_jsons(
                lang_refined,
                json_files,
                [language],  # Process only one language at a time
                self.output_dirs["final"]
            )
            translated_jsons.update(lang_translated)
            
            # Step 6: Validate translations for this language
            logging.info(f"Step 6: Validating translations for {language}...")
            lang_validation = validate_translations(
                lang_translated,
                json_files,
                [language],  # Process only one language at a time
                self.config.validation_model,
                self.output_dirs["validated"],
                self.project_context,
                batch_size=self.config.batch_size,
                mock_mode=self.config.mock_mode
            )
            validation_results.update(lang_validation)
            
            # Count words processed
            original_words = sum(
                len(str(value).split()) 
                for data in json_files.values() 
                for value in self._extract_all_values(data)
            )
            translated_words = sum(
                len(str(value).split()) 
                for lang_data in lang_translated.values() 
                if language in lang_data
                for value in self._extract_all_values(lang_data[language])
            )
            model_usage.add_words(self.config.validation_model, original_words + translated_words)
            
            # Add a delay between languages to avoid rate limits
            if not self.config.mock_mode:
                logging.info(f"Waiting 5 seconds before processing next language...")
                time.sleep(5)
        
        # Generate summary report for this file
        logging.info("Generating summary report...")
        generate_summary_report(
            validation_results,
            str(file_path.parent),
            self.config.output_dir,
            self.config.languages,
            [file_name],
            {
                "options_generation": self.config.options_model,
                "selection": self.config.selection_model,
                "refinement": self.config.refinement_model,
                "validation": self.config.validation_model
            },
            self.output_dirs["logs"]
        )
        
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        logging.info(f"Translation of {file_name} completed in {duration}")
        
        return validation_results
    
    def process_directory(self) -> Dict[str, Any]:
        """
        Process all JSON files in the input directory.
        
        Returns:
            Dictionary with validation results for all files
        """
        all_results = {}
        input_path = Path(self.config.input_dir)
        
        # Find all JSON files
        json_files = list(input_path.glob("**/*.json"))
        if not json_files:
            logging.warning(f"No JSON files found in {self.config.input_dir}")
            return {}
        
        logging.info(f"Found {len(json_files)} JSON files to process")
        
        # Process each file
        with tqdm(total=len(json_files), desc="Processing files", unit="file") as pbar:
            for file_path in json_files:
                try:
                    results = self.process_file(file_path)
                    all_results[file_path.name] = results
                except Exception as e:
                    logging.error(f"Error processing {file_path.name}: {str(e)}")
                finally:
                    pbar.update(1)
        
        # Print model usage summary
        model_usage.print_summary()
        
        return all_results
    
    @staticmethod
    def _extract_all_values(data: Dict[str, Any]) -> List[str]:
        """
        Extract all string values from a nested dictionary.
        
        Args:
            data: Nested dictionary
            
        Returns:
            List of all string values
        """
        values = []
        
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, str):
                    values.append(value)
                elif isinstance(value, (dict, list)):
                    values.extend(TranslationPipeline._extract_all_values(value))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    values.append(item)
                elif isinstance(item, (dict, list)):
                    values.extend(TranslationPipeline._extract_all_values(item))
        
        return values 