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
    json_files: Dict[str, Dict],
    languages: List[str],
    model: str = "o1",
    output_dir: Optional[str] = None,
    project_context: Optional[str] = None,
    batch_size: int = 20,
    mock_mode: bool = False
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Select the best translation option for each string.
    
    Args:
        options: Dictionary mapping filenames to dictionaries mapping paths to
               dictionaries mapping languages to lists of translation options
        json_files: Original JSON files for context
        languages: List of target languages
        model: LLM model to use for selection
        output_dir: Directory to save intermediate results (optional)
        project_context: Additional context for selection
        batch_size: Number of options to select in each batch
        mock_mode: Whether to run in mock mode without API calls
        
    Returns:
        Dictionary mapping filenames to dictionaries mapping paths to
        dictionaries mapping languages to selected translations
    """
    # Create selections structure
    selections = {}
    
    # If mock mode is enabled, select the first option without API calls
    if mock_mode:
        for filename, paths in options.items():
            selections[filename] = {}
            for path, langs in paths.items():
                selections[filename][path] = {}
                for language, opts in langs.items():
                    # Select the first option as the "best" translation
                    selections[filename][path][language] = opts[0] if opts else f"[{language}] MISSING"
        
        # Save selections to file if output directory is provided
        if output_dir:
            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Save to JSON file
            for filename, paths in selections.items():
                file_path = os.path.join(output_dir, f"{filename.split('.')[0]}_selections.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(paths, f, ensure_ascii=False, indent=2)
        
        return selections

    for filename, path_options in options.items():
        selections[filename] = {}

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
                    if language not in selections[filename]:
                        selections[filename][language] = {}

                    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        next(reader)  # Skip header
                        for row in reader:
                            if len(row) >= 3:
                                path, original, translation = row[0], row[1], row[2]
                                selections[filename][language][path] = translation

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
                    json_files[filename],
                    project_context
                )

                # Store selected translations
                if language not in selections[filename]:
                    selections[filename][language] = {}

                for selection in batch_selected:
                    path = selection["path"]
                    selected_translation = selection["selected"]
                    selections[filename][language][path] = selected_translation

            print(
                f"Selected translations for batch {i // batch_size + 1}/{(len(path_items) - 1) // batch_size + 1} for {filename}"
            )

        # Save selected translations to CSV for each language
        for language in languages:
            # Skip if this language wasn't processed
            if language not in selections[filename]:
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

                for path, translations in selections[filename][language].items():
                    original = ""
                    # Find original text from options dictionary
                    if filename in json_files and path in path_options:
                        # Extract original text by traversing the JSON using path components
                        components = path.split('.')
                        obj = json_files[filename]
                        try:
                            for comp in components:
                                obj = obj[comp]
                            if isinstance(obj, str):
                                original = obj
                        except (KeyError, TypeError):
                            pass

                    writer.writerow([path, original, translations])

            print(f"Saved selected translations for {language} in {filename}")

    return selections


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
        
    # Get language name from language code by loading languages.json
    try:
        with open("data/languages.json", "r", encoding="utf-8") as f:
            language_data = json.load(f)
            # Swap keys and values to get a mapping from code to name
            code_to_name = {code: name for name, code in language_data.items()}
            language_name = code_to_name.get(language, language)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to just using the language code
        language_name = language

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
        language=language_name,
        project_context=project_context
    ) + f"\nRespond with a JSON object containing a 'selections' array with the best {language_name} translation for each input string in order."

    # Create the technical prompt
    technical_prompt = {
        "system": system_prompt,
        "user": f"Please analyze the following data and select the best {language_name} ({language}) translation option for each string. Respond with a JSON array of selected translations in the same order as the input:\n{json.dumps(formatted_data, ensure_ascii=False, indent=2)}",
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


def _select_best_translations(
    selection_data: List[Dict[str, Any]],
    language: str,
    model: str,
    json_data: Dict,
    project_context: str = None
) -> List[Dict[str, Any]]:
    """
    Select the best translation from options for a batch of strings.
    
    Args:
        selection_data: List of dictionaries containing paths and translation options
        language: Target language
        model: Model to use for selection
        json_data: Original JSON data for context
        project_context: Custom project context
        
    Returns:
        List of dictionaries containing paths and selected translations
    """
    # Format the data for the batch selection function
    batch_data = []
    for item in selection_data:
        path = item["path"]
        options = item["options"]
        
        # Get original text by traversing the JSON using path components
        original = _get_value_at_path(json_data, path)
        if not isinstance(original, str):
            original = str(original)
            
        batch_data.append({
            "path": path,
            "original": original,
            "options": options
        })
    
    # Call the batch selection function
    selected_translations = _select_best_batch(batch_data, language, model, project_context)
    
    # Format the results
    results = []
    for i, item in enumerate(selection_data):
        selected = selected_translations[i] if i < len(selected_translations) else item["options"][0]
        results.append({
            "path": item["path"],
            "selected": selected
        })
    
    return results


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