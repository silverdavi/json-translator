"""
Module for selecting the best translation option from multiple candidates.
This module handles the third step of the translation pipeline.
"""

import os
import csv
import json
from typing import Dict, List, Any, Optional

# Import the user-provided OpenAI wrapper and context configuration
from utils.api.util_call import call_openai
from utils.config.context_configuration import get_system_prompt


def select_best_translations(
    options: Dict[str, Dict[str, Dict[str, List[str]]]],
    original_jsons: Dict[str, Any],
    languages: List[str],
    model: str,
    output_dir: str,
    project_context: str = None,
    batch_size: int = 20
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Select the best translation from the options for each string.

    Args:
        options: Dictionary mapping filenames to dictionaries mapping paths to
                 dictionaries mapping languages to lists of translation options
        original_jsons: Dictionary mapping filenames to original JSON data
        languages: List of target languages
        model: Model to use for selecting best translations
        output_dir: Directory to save selected translations CSV files
        project_context: Custom project context (or None to use default)
        batch_size: Number of string selections to process in each batch

    Returns:
        Dictionary mapping filenames to dictionaries mapping languages to
        dictionaries mapping paths to selected translations
    """
    selected = {}

    for filename, path_options in options.items():
        selected[filename] = {}

        # Prepare selection data
        path_items = list(path_options.items())

        for i in range(0, len(path_items), batch_size):
            batch = path_items[i:i + batch_size]
            
            for language in languages:
                # Check if output file exists - if so, skip this language
                csv_path = os.path.join(
                    output_dir, f"{filename}_{language}_selected.csv"
                )
                if os.path.exists(csv_path):
                    print(f"Skipping existing selections for {language} in {filename}")

                    # Load existing selections from CSV
                    if language not in selected[filename]:
                        selected[filename][language] = {}

                    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        next(reader)  # Skip header
                        for row in reader:
                            if len(row) >= 3:
                                path, original, translation = row[0], row[1], row[2]
                                selected[filename][language][path] = translation

                    continue

                # Select best translations for this batch
                selection_data = []
                for path, lang_options in batch:
                    if language in lang_options:
                        selection_data.append({
                            "path": path,
                            "options": lang_options[language]
                        })

                # Make API call to select best translations
                batch_selected = _select_best_translations(
                    selection_data, 
                    language, 
                    model, 
                    original_jsons[filename],
                    project_context
                )

                # Store selected translations
                if language not in selected[filename]:
                    selected[filename][language] = {}

                for selection in batch_selected:
                    path = selection["path"]
                    selected_translation = selection["selected"]
                    selected[filename][language][path] = selected_translation

            print(
                f"Selected translations for batch {i // batch_size + 1}/{(len(path_items) - 1) // batch_size + 1} for {filename}"
            )

        # Save selected translations to CSV for each language
        for language in languages:
            # Skip if this language wasn't processed
            if language not in selected[filename]:
                continue

            csv_path = os.path.join(
                output_dir, f"{filename}_{language}_selected.csv"
            )

            # Skip writing if file already exists
            if os.path.exists(csv_path):
                continue

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Path", "Original", "Selected Translation"])

                for path, translations in selected[filename][language].items():
                    original = ""
                    # Find original text from options dictionary
                    if filename in original_jsons and path in path_options:
                        # Extract original text by traversing the JSON using path components
                        components = path.split('.')
                        obj = original_jsons[filename]
                        try:
                            for comp in components:
                                obj = obj[comp]
                            if isinstance(obj, str):
                                original = obj
                        except (KeyError, TypeError):
                            pass

                    writer.writerow([path, original, translations])

            print(f"Saved selected translations for {language} in {filename}")

    return selected


def _get_value_at_path(json_data: Dict, path: str) -> Any:
    """Get a value from a nested dictionary using a dot-separated path."""
    try:
        current = json_data
        for p in path.split('.'):
            if p.isdigit():
                p = int(p)
            current = current[p]
        return current
    except (KeyError, IndexError, TypeError):
        return f"Error: Could not retrieve value at path {path}"


def _select_best_batch(
        batch_data: List[Dict[str, Any]],
        language: str,
        model: str,
        project_context: str = None
) -> List[str]:
    """
    Select the best translation options for a batch of strings.
    """
    # Validate input batch
    if not batch_data:
        raise ValueError("Empty batch data provided")

    # Format the batch data for the prompt
    formatted_data = []
    for item in batch_data:
        formatted_data.append({
            "path": item["path"],
            "original": item["original"],
            "options": item["options"]
        })

    # Get the system prompt
    system_prompt = get_system_prompt(
        "select_translations",
        language=language,
        project_context=project_context
    ) + "\nRespond with a JSON object containing a 'selections' array with the best translation for each input string in order."

    # Create the technical prompt
    technical_prompt = {
        "system": system_prompt,
        "user": f"Please analyze the following data and select the best translation option for each string. Respond with a JSON array of selected translations in the same order as the input:\n{json.dumps(formatted_data, ensure_ascii=False, indent=2)}",
        "response_format": {"type": "json_object"}
    }

    try:
        response_text = call_openai(prompt=technical_prompt, model=model)
        print(f"Raw API response: {response_text[:200]}...")  # Debug output
        
        response_data = json.loads(response_text)
        
        if "selections" not in response_data:
            print(f"Invalid API response format. Expected 'selections' field. Got: {response_text[:200]}...")
            return [item["options"][0] for item in batch_data]  # Fallback to first option
            
        selections = response_data["selections"]
        
        # Validate selections array
        if not isinstance(selections, list):
            print(f"Invalid selections format. Expected list. Got: {type(selections)}")
            return [item["options"][0] for item in batch_data]
            
        # Ensure we have the right number of selections
        if len(selections) != len(batch_data):
            print(f"Mismatch in selections count. Expected {len(batch_data)}, got {len(selections)}")
            return [item["options"][0] for item in batch_data]
            
        # Return selections in order
        return [str(selection) for selection in selections]

    except Exception as e:
        print(f"Error during translation selection: {str(e)}")
        return [item["options"][0] for item in batch_data]  # Fallback to first option


# Example usage (for testing)
if __name__ == "__main__":
    # Sample data from previous step
    options = {
        "test.json": {
            "hello": {
                "Spanish": ["Hola", "Saludos", "Buenos días"],
                "French": ["Bonjour", "Salut", "Bienvenue"]
            },
            "welcome": {
                "Spanish": ["Bienvenido a nuestra aplicación", "Bienvenido a nuestra app",
                            "Te damos la bienvenida a nuestra aplicación"],
                "French": ["Bienvenue dans notre application", "Bienvenue sur notre application",
                           "Bienvenue à notre application"]
            }
        }
    }

    # Sample JSON files
    json_files = {
        "test.json": {
            "hello": "Hello",
            "welcome": "Welcome to our application"
        }
    }

    # Languages
    languages = ["Spanish", "French"]

    # Create test output directory
    os.makedirs("test_output", exist_ok=True)

    # Select best translations
    selected = select_best_translations(
        options,
        json_files,
        languages,
        "gpt-3.5-turbo",
        "test_output"
    )

    # Print results
    for filename, paths in selected.items():
        for path, lang_selections in paths.items():
            print(f"\nPath: {path}, Original: {json_files[filename][path]}")
            for lang, selection in lang_selections.items():
                print(f"  {lang}: {selection}") 