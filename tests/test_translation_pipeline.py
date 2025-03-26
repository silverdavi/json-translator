"""
Unit tests for the JSON translation pipeline.
"""

import os
import json
import unittest
from typing import Dict, List, Any
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from config import DEFAULT_TEST_DIR
from json_extractor import extract_strings
from translation_generator import generate_translation_options
from translation_selector import select_best_translations
from translation_refiner import refine_translations
from json_generator import generate_translated_jsons
from translation_validator import validate_translations
from context_generator import generate_context_configuration


class TestTranslationPipeline(unittest.TestCase):
    """Test case for the translation pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test directories
        self.base_dir = os.path.join(DEFAULT_TEST_DIR, "output")
        os.makedirs(self.base_dir, exist_ok=True)
        
        self.dirs = {
            "extracted": os.path.join(self.base_dir, "1_extracted_strings"),
            "options": os.path.join(self.base_dir, "2_translation_options"),
            "selected": os.path.join(self.base_dir, "3_selected_translations"),
            "refined": os.path.join(self.base_dir, "4_refined_translations"),
            "final": os.path.join(self.base_dir, "5_final_json"),
            "validated": os.path.join(self.base_dir, "6_validation_results"),
            "logs": os.path.join(self.base_dir, "logs"),
        }
        
        for d in self.dirs.values():
            os.makedirs(d, exist_ok=True)
        
        # Create sample JSON data
        self.sample_data = {
            "test.json": {
                "greeting": "Hello World",
                "buttons": {
                    "save": "Save",
                    "cancel": "Cancel"
                },
                "messages": {
                    "welcome": "Welcome to our application",
                    "goodbye": "Thank you for using our application"
                }
            }
        }
        
        # Define test settings
        self.languages = ["Spanish", "French"]
        self.options_count = 2
        self.model = "gpt-3.5-turbo"  # Use a less expensive model for tests
        
        # Save sample data to file
        self.input_dir = os.path.join(DEFAULT_TEST_DIR, "input")
        os.makedirs(self.input_dir, exist_ok=True)
        
        sample_file_path = os.path.join(self.input_dir, "test.json")
        with open(sample_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.sample_data["test.json"], f, indent=2, ensure_ascii=False)
        
        # Generate context for testing
        self.project_context = "Test project for unit testing the translation pipeline."
        try:
            # Try to generate context but don't save to avoid overwriting user config
            self.contexts = generate_context_configuration(
                self.project_context, 
                self.model,
                save_to_file=False
            )
        except Exception as e:
            print(f"Warning: Could not generate context configuration: {e}")
            self.contexts = {}

    def test_extract_strings(self):
        """Test string extraction from JSON files."""
        # Load sample JSON file
        json_files = {}
        for filename in os.listdir(self.input_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.input_dir, filename), 'r', encoding='utf-8') as f:
                    json_files[filename] = json.load(f)
        
        # Extract strings
        extracted = extract_strings(json_files, self.dirs["extracted"])
        
        # Check if extraction worked
        self.assertIsInstance(extracted, dict)
        self.assertIn("test.json", extracted)
        
        # Check if all keys were extracted
        self.assertIn("greeting", extracted["test.json"])
        self.assertIn("buttons.save", extracted["test.json"])
        self.assertIn("buttons.cancel", extracted["test.json"])
        self.assertIn("messages.welcome", extracted["test.json"])
        self.assertIn("messages.goodbye", extracted["test.json"])
        
        return extracted

    def test_pipeline_integration(self):
        """Test the full pipeline integration."""
        # This is an integration test that checks if the pipeline components work together
        # We'll just call each stage and verify it doesn't raise exceptions
        try:
            # Get extracted strings
            extracted = self.test_extract_strings()
            
            # Generate options
            options = generate_translation_options(
                extracted, 
                self.languages, 
                self.model, 
                self.options_count, 
                self.dirs["options"],
                self.project_context
            )
            
            # Load JSON files for context
            json_files = {}
            for filename in os.listdir(self.input_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(self.input_dir, filename), 'r', encoding='utf-8') as f:
                        json_files[filename] = json.load(f)
            
            # Select best translations
            selected = select_best_translations(
                options, 
                json_files, 
                self.languages, 
                self.model, 
                self.dirs["selected"],
                self.project_context
            )
            
            # Refine translations
            refined = refine_translations(
                selected, 
                json_files, 
                self.languages, 
                self.model, 
                self.dirs["refined"],
                self.project_context
            )
            
            # Generate translated JSONs
            translated = generate_translated_jsons(
                refined, 
                json_files, 
                self.languages, 
                self.dirs["final"]
            )
            
            # Validate translations
            validation_results = validate_translations(
                translated, 
                json_files, 
                self.languages, 
                self.model, 
                self.dirs["validated"],
                self.project_context
            )
            
            # Check that we have validation results
            self.assertIsInstance(validation_results, dict)
            self.assertTrue(len(validation_results) > 0)
            
        except Exception as e:
            self.fail(f"Pipeline integration test failed with error: {e}")


if __name__ == "__main__":
    unittest.main() 