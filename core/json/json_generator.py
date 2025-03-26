"""
Module for generating translated JSON files from refined translations.
This module handles the fifth step of the translation pipeline.
"""

import os
import json
import copy
from typing import Dict, List, Any

def load_language_codes() -> Dict[str, str]:
    """
    Load language codes from the languages.json file.
    
    Returns:
        Dictionary mapping language names to language codes
    """
    try:
        with open("data/languages.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: data/languages.json not found. Using fallback minimal language codes.")
        # Fallback to minimal set of language codes
        return {
            "English": "en",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Chinese": "zh",
            "Simplified Chinese": "zh-CN",
            "Traditional Chinese": "zh-TW"
        }

# Load language codes from file
LANGUAGE_CODES = load_language_codes()

def generate_translated_jsons(
    refined: Dict[str, Dict[str, Dict[str, str]]],
    json_files: Dict[str, Dict],
    languages: List[str],
    output_dir: str
) -> Dict[str, Dict[str, Dict]]:
    """
    Generate translated JSON files from refined translations.

    Args:
        refined: Dictionary mapping filenames to dictionaries mapping languages to
                dictionaries mapping paths to refined translations
        json_files: Original JSON files
        languages: List of target languages
        output_dir: Directory to save translated JSON files

    Returns:
        Dictionary mapping filenames to dictionaries mapping languages to
        translated JSON objects
    """
    translated_jsons = {}

    for filename, lang_paths in refined.items():
        translated_jsons[filename] = {}

        # Create a translated JSON for each language
        for language in languages:
            # Skip if this language wasn't processed
            if language not in lang_paths:
                print(f"Skipping {language} for {filename} (no translations available)")
                continue
                
            # Start with a deep copy of the original JSON
            translated_json = copy.deepcopy(json_files[filename])

            # Replace strings with translations
            for path, translation in lang_paths[language].items():
                # Navigate to the path
                _set_value_at_path(translated_json, path, translation)

            # Store the translated JSON
            translated_jsons[filename][language] = translated_json

            # Get language code for folder name
            language_code = LANGUAGE_CODES.get(language, language.lower())
            
            # Special handling for Chinese
            if language.lower() == "chinese" and language not in LANGUAGE_CODES:
                language_code = "zh" # Default to general Chinese code
                if "simplified" in language.lower():
                    language_code = LANGUAGE_CODES.get("Simplified Chinese", "zh-CN")
                elif "traditional" in language.lower():
                    language_code = LANGUAGE_CODES.get("Traditional Chinese", "zh-TW")

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
        "homepage.json": {
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
        "homepage.json": {
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
    os.makedirs("examples/output", exist_ok=True)

    # Generate translated JSONs
    translated_jsons = generate_translated_jsons(
        refined,
        json_files,
        languages,
        "examples/output"
    )

    # Print results
    for filename, lang_jsons in translated_jsons.items():
        for language, translated_json in lang_jsons.items():
            print(f"\n{filename} - {language}:")
            print(json.dumps(translated_json, ensure_ascii=False, indent=2)) 