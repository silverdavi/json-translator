"""
Translation Pipeline module that orchestrates the entire translation process.
This class coordinates all steps of the pipeline from extraction to validation.
"""

import os
import json
import datetime
import logging
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
                prompt_config_path=config.prompt_config_path
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
        
        # Step 2: Generate translation options
        logging.info("Step 2: Generating translation options...")
        with tqdm(total=len(self.config.languages), desc="Generating options", unit="language") as pbar:
            options = generate_translation_options(
                extracted,
                self.config.languages,
                self.config.options_model,
                self.config.options_count,
                self.output_dirs["options"],
                self.project_context,
                batch_size=self.config.batch_size
            )
            pbar.update(len(self.config.languages))
            
            # Count words processed
            for language in self.config.languages:
                total_words = sum(
                    len(text.split()) * self.config.options_count 
                    for strings in extracted.values() 
                    for text in strings.values()
                )
                model_usage.add_words(self.config.options_model, total_words)
        
        # Step 3: Select best translations
        logging.info("Step 3: Selecting best translations...")
        with tqdm(total=len(self.config.languages), desc="Selecting translations", unit="language") as pbar:
            selected = select_best_translations(
                options,
                json_files,
                self.config.languages,
                self.config.selection_model,
                self.output_dirs["selected"],
                self.project_context,
                batch_size=self.config.batch_size
            )
            pbar.update(len(self.config.languages))
            
            # Count words processed
            for language in self.config.languages:
                total_words = sum(
                    len(str(options).split()) 
                    for filename, lang_options in options.items()
                    if language in lang_options
                )
                model_usage.add_words(self.config.selection_model, total_words)
        
        # Step 4: Refine translations
        logging.info("Step 4: Refining translations...")
        with tqdm(total=len(self.config.languages), desc="Refining translations", unit="language") as pbar:
            refined = refine_translations(
                selected,
                json_files,
                self.config.languages,
                self.config.refinement_model,
                self.output_dirs["refined"],
                self.project_context,
                batch_size=self.config.batch_size
            )
            pbar.update(len(self.config.languages))
            
            # Count words processed
            for language in self.config.languages:
                total_words = sum(
                    len(text.split()) 
                    for filename, lang_selected in selected.items()
                    if language in lang_selected
                    for text in lang_selected[language].values()
                )
                model_usage.add_words(self.config.refinement_model, total_words)
        
        # Step 5: Generate translated JSON files
        logging.info("Step 5: Generating translated JSON files...")
        with tqdm(total=len(self.config.languages), desc="Generating JSON files", unit="language") as pbar:
            translated_jsons = generate_translated_jsons(
                refined,
                json_files,
                self.config.languages,
                self.output_dirs["final"]
            )
            pbar.update(len(self.config.languages))
        
        # Step 6: Validate translations
        logging.info("Step 6: Validating translations...")
        with tqdm(total=len(self.config.languages), desc="Validating translations", unit="language") as pbar:
            validation_results = validate_translations(
                translated_jsons,
                json_files,
                self.config.languages,
                self.config.validation_model,
                self.output_dirs["validated"],
                self.project_context,
                batch_size=self.config.batch_size
            )
            pbar.update(len(self.config.languages))
            
            # Count words processed
            for language in self.config.languages:
                # Roughly estimate validation token usage
                original_words = sum(
                    len(str(value).split()) 
                    for data in json_files.values() 
                    for value in self._extract_all_values(data)
                )
                translated_words = sum(
                    len(str(value).split()) 
                    for lang_data in translated_jsons.values() 
                    if language in lang_data
                    for value in self._extract_all_values(lang_data[language])
                )
                model_usage.add_words(self.config.validation_model, original_words + translated_words)
        
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