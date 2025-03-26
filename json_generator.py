"""
Module for generating translated JSON files from refined translations.
This module handles the fifth step of the translation pipeline.
"""

import os
import json
import copy
from typing import Dict, List, Any

# Language code mapping (for standard folder naming)
LANGUAGE_CODES = {
    "Thai": "th",
    "Malay": "ms",
    "Simplified Chinese": "zh-CN",
    "Traditional Chinese": "zh-TW",
    "Hebrew": "he",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
    "Arabic": "ar",
    "Burmese": "my"  # Added Burmese language code
    # Add more languages as needed
}

def generate_translated_jsons(
    refined: Dict[str, Dict[str, Dict[str, str]]],
    json_files: Dict[str, Dict],
    languages: List[str],
    output_dir: str
) -> Dict[str, Dict[str, Dict]]:
    """
    Generate translated JSON files from refined translations.

    Args:
        refined: Dictionary mapping filenames to dictionaries mapping paths to
               dictionaries mapping languages to refined translations
        json_files: Original JSON files
        languages: List of target languages
        output_dir: Directory to save translated JSON files

    Returns:
        Dictionary mapping filenames to dictionaries mapping languages to
        translated JSON objects
    """
    translated_jsons = {}

    for filename, paths in refined.items():
        translated_jsons[filename] = {}

        # Create a translated JSON for each language
        for language in languages:
            # Start with a deep copy of the original JSON
            translated_json = copy.deepcopy(json_files[filename])

            # Replace strings with translations
            for path, lang_translations in paths.items():
                translation = lang_translations[language]

                # Navigate to the path
                _set_value_at_path(translated_json, path, translation)

            # Store the translated JSON
            translated_jsons[filename][language] = translated_json

            # Get language code for folder name
            language_code = LANGUAGE_CODES.get(language, language.lower())

            # Create language-specific directory
            lang_dir = os.path.join(output_dir, language_code)
            os.makedirs(lang_dir, exist_ok=True)

            # Save the translated JSON using the original filename
            json_path = os.path.join(lang_dir, filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(translated_json, f, ensure_ascii=False, indent=2)

            print(f"Generated {filename} for {language} in {lang_dir}")

    return translated_jsons

def _set_value_at_path(json_data: Dict, path: str, value: Any) -> None:
    """
    Set a value in a nested dictionary using a dot-separated path.
    Creates intermediate dictionaries if they don't exist.

    Args:
        json_data: Dictionary to modify
        path: Dot-separated path to the value
        value: Value to set
    """
    parts = path.split('.')
    current = json_data
    
    # Traverse/create the path except for the last part
    for i, part in enumerate(parts[:-1]):
        if part.isdigit():
            part = int(part)
            # Handle list indices
            if isinstance(current, list):
                while len(current) <= part:
                    current.append({})
            else:
                # Convert to list if needed
                if not isinstance(current, dict):
                    current = {}
                if part not in current:
                    current[part] = {}
        else:
            # Handle dictionary keys
            if not isinstance(current, dict):
                current = {}
            if part not in current:
                current[part] = {}
        current = current[part]

    # Set the final value
    last_part = parts[-1]
    if last_part.isdigit():
        last_part = int(last_part)
        if isinstance(current, list):
            while len(current) <= last_part:
                current.append(None)
        current[last_part] = value
    else:
        if not isinstance(current, dict):
            current = {}
        current[last_part] = value

# Example usage (for testing)
if __name__ == "__main__":
    # Sample data from previous step
    refined = {
        "auth.json": {
            "login": {
                "Spanish": "Iniciar sesión",
                "French": "Connexion"
            },
            "register": {
                "Spanish": "Registrarse",
                "French": "S'inscrire"
            }
        },
        "dashboard.json": {
            "welcome": {
                "Spanish": "Bienvenido",
                "French": "Bienvenue"
            },
            "stats": {
                "Spanish": "Estadísticas",
                "French": "Statistiques"
            }
        }
    }

    # Sample JSON files
    json_files = {
        "auth.json": {
            "login": "Login",
            "register": "Register"
        },
        "dashboard.json": {
            "welcome": "Welcome",
            "stats": "Statistics"
        }
    }

    # Languages
    languages = ["Spanish", "French"]

    # Create test output directory
    os.makedirs("test_output", exist_ok=True)

    # Generate translated JSONs
    translated_jsons = generate_translated_jsons(
        refined,
        json_files,
        languages,
        "test_output"
    )

    # Print results
    for filename, lang_jsons in translated_jsons.items():
        for language, translated_json in lang_jsons.items():
            print(f"\n{filename} - {language}:")
            print(json.dumps(translated_json, ensure_ascii=False, indent=2))