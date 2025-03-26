"""
Module for refining translations to improve quality and consistency.
This module handles the fourth step of the translation pipeline.
"""

import os
import csv
import json
from typing import Dict, List, Any, Optional

# Import the user-provided OpenAI wrapper and context configuration
from util_call import call_openai
from context_configuration import get_system_prompt


def refine_translations(
        selected: Dict[str, Dict[str, Dict[str, str]]],
        original_jsons: Dict[str, Any],
        languages: List[str],
        model: str,
        output_dir: str,
        project_context: str = None,
        batch_size: int = 50
) -> Dict[str, Dict[str, Dict[str, str]]]:
    """
    Refine the selected translations for improved quality and consistency.

    Args:
        selected: Dictionary mapping filenames to dictionaries mapping languages to
                  dictionaries mapping paths to selected translations
        original_jsons: Dictionary mapping filenames to original JSON data
        languages: List of target languages
        model: Model to use for refining translations
        output_dir: Directory to save refined translations CSV files
        project_context: Custom project context (or None to use default)
        batch_size: Number of strings to process in each batch

    Returns:
        Dictionary mapping filenames to dictionaries mapping languages to
        dictionaries mapping paths to refined translations
    """
    refined = {}

    for filename, lang_selections in selected.items():
        refined[filename] = {}
        
        for language in languages:
            # Skip if this language wasn't processed
            if language not in lang_selections:
                print(f"Skipping language {language} (no selections available)")
                continue
                
            # Check if output file exists
            csv_path = os.path.join(
                output_dir, f"{filename}_{language}_refined.csv"
            )
            if os.path.exists(csv_path):
                print(f"Loading existing refinements for {language} in {filename}")
                
                # Load existing refinements
                if language not in refined[filename]:
                    refined[filename][language] = {}
                    
                with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)  # Skip header
                    for row in reader:
                        if len(row) >= 3:
                            path, original, translation = row[0], row[1], row[2]
                            refined[filename][language][path] = translation
                
                continue

            # Prepare data for refinement
            refinement_data = []
            for path, translation in lang_selections[language].items():
                # Get original string
                original = ""
                components = path.split('.')
                obj = original_jsons[filename]
                try:
                    for comp in components:
                        obj = obj[comp]
                    if isinstance(obj, str):
                        original = obj
                except (KeyError, TypeError):
                    pass
                
                refinement_data.append({
                    "path": path,
                    "original": original,
                    "translation": translation
                })
            
            # Process in batches
            if language not in refined[filename]:
                refined[filename][language] = {}
                
            for i in range(0, len(refinement_data), batch_size):
                batch = refinement_data[i:i + batch_size]
                
                # Refine this batch
                batch_refined = _refine_batch(batch, language, model, original_jsons[filename], project_context)
                
                # Store refined translations
                for item in batch_refined:
                    refined[filename][language][item["path"]] = item["refined"]
                
                print(
                    f"Refined batch {i // batch_size + 1}/{(len(refinement_data) - 1) // batch_size + 1} for {language} in {filename}")
            
            # Save refined translations to CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Path", "Original", "Refined Translation"])
                
                for path, translation in refined[filename][language].items():
                    # Get original string
                    original = ""
                    components = path.split('.')
                    obj = original_jsons[filename]
                    try:
                        for comp in components:
                            obj = obj[comp]
                        if isinstance(obj, str):
                            original = obj
                    except (KeyError, TypeError):
                        pass
                    
                    writer.writerow([path, original, translation])
            
            print(f"Saved refined translations for {language} in {filename}")
    
    return refined


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


def _refine_batch(
        batch: List[Dict],
        language: str,
        model: str,
        filename: str,
        project_context: str = None
) -> List[str]:
    """
    Refine a batch of translations.

    Args:
        batch: List of dictionaries with translations to refine
        language: Target language
        model: Model to use for refinement
        filename: Name of the file being processed (for context)
        project_context: Custom project context (or None to use default)

    Returns:
        List of refined translations

    Raises:
        ValueError: If batch is empty or invalid
        RuntimeError: If API call fails and no fallback is possible
    """
    if not batch:
        raise ValueError("batch cannot be empty")

    # Validate batch data structure
    for i, item in enumerate(batch):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid item type at index {i}: expected dict, got {type(item)}")
        if "path" not in item or "original" not in item or "translation" not in item:
            raise ValueError(f"Missing required fields at index {i}: path, original, translation")
        if not isinstance(item["translation"], str):
            raise ValueError(f"Invalid translation type at index {i}: expected str, got {type(item['translation'])}")

    # Get the appropriate system prompt using the project context
    system_prompt = get_system_prompt(
        "refine_translations",
        language=language,
        project_context=project_context
    ) + "\nRespond with a JSON object containing a 'refined_translations' array."  # Add explicit JSON mention

    # Use the provided wrapper function with simplified response format
    technical_prompt = {
        "system": system_prompt,
        "user": f"Please refine the following translations and provide your response in JSON format:\nFile: {filename}\n{json.dumps(batch, indent=2)}",  # Add explicit JSON mention
        "response_format": {"type": "json_object"}
    }

    try:
        response_text = call_openai(prompt=technical_prompt, model=model)
        print(f"Raw refinement response: {response_text[:200]}...")  # Debug output
        
        response_data = json.loads(response_text)
        
        if "refined_translations" not in response_data:
            print("Missing 'refined_translations' in response")
            return [item["translation"] for item in batch]  # Fallback to original
            
        refined = response_data["refined_translations"]
        
        if len(refined) != len(batch):
            print(f"Mismatch in refined translations count. Expected {len(batch)}, got {len(refined)}")
            return [item["translation"] for item in batch]  # Fallback to original
            
        return [str(trans) if trans else item["translation"] for trans, item in zip(refined, batch)]
        
    except Exception as e:
        print(f"Error during refinement: {str(e)}")
        return [item["translation"] for item in batch]  # Fallback to original


# Example usage (for testing)
if __name__ == "__main__":
    # Sample data from previous step
    selected = {
        "test.json": {
            "hello": {
                "Spanish": "Hola",
                "French": "Bonjour"
            },
            "welcome": {
                "Spanish": "Bienvenido a nuestra aplicación",
                "French": "Bienvenue dans notre application"
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

    # Refine translations
    refined = refine_translations(
        selected,
        json_files,
        languages,
        "gpt-3.5-turbo",
        "test_output",
        "Software context: Medical application for fertility clinics.",
        batch_size=50
    )

    # Print results
    for filename, paths in refined.items():
        for path, lang_refinements in paths.items():
            print(f"\nPath: {path}, Original: {json_files[filename][path]}")
            for lang, refinement in lang_refinements.items():
                print(f"  {lang} (Selected): {selected[filename][path][lang]}")
                print(f"  {lang} (Refined): {refinement}")