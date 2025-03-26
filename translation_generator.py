"""
Module for generating multiple translation options for strings.
This module handles the second step of the translation pipeline.
"""

import os
import csv
import json
from typing import Dict, List, Any, Optional

# Import the user-provided OpenAI wrapper and context configuration
from util_call import call_openai
from context_configuration import get_system_prompt

def generate_translation_options(
    extracted: Dict[str, Dict[str, str]],
    languages: List[str],
    model: str,
    options_count: int,
    output_dir: str,
    project_context: str = None,
    batch_size: int = 10
) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """
    Generate multiple translation options for each string.

    Args:
        extracted: Dictionary mapping filenames to dictionaries of paths to strings
        languages: List of target languages
        model: Model to use for generating translation options
        options_count: Number of translation options to generate per string
        output_dir: Directory to save generated options CSV files
        project_context: Custom project context (or None to use default)
        batch_size: Number of strings to process in each batch

    Returns:
        Dictionary mapping filenames to dictionaries mapping paths to
        dictionaries mapping languages to lists of translation options
    """
    options = {}

    for filename, strings in extracted.items():
        options[filename] = {}

        # Process strings in batches to reduce API calls
        string_items = list(strings.items())

        for i in range(0, len(string_items), batch_size):
            batch = string_items[i:i+batch_size]
            batch_paths = [path for path, _ in batch]
            batch_strings = [string for _, string in batch]

            # Generate options for each language
            for language in languages:
                # Check if output file exists - if so, skip this language
                csv_path = os.path.join(
                    output_dir, f"{filename}_{language}_options.csv"
                )
                if os.path.exists(csv_path):
                    print(f"Skipping existing options for {language} in {filename}")

                    # Load existing options from CSV
                    existing_options = {}
                    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        header = next(reader)  # Skip header
                        option_count = len(header) - 2  # Subtract Path and Original columns

                        for row in reader:
                            if len(row) >= 2 + option_count:
                                path = row[0]
                                existing_options[path] = row[2:2+option_count]

                    # Add to options dictionary
                    for path in batch_paths:
                        if path not in options[filename]:
                            options[filename][path] = {}
                        if path in existing_options:
                            options[filename][path][language] = existing_options[path]
                        else:
                            # If path not found in existing options, initialize with empty list
                            options[filename][path][language] = [""] * options_count

                    continue

                # Generate new options
                batch_options = _generate_batch_options(batch_strings, language, model, options_count, project_context)

                # Store options - with better error handling
                for j, path in enumerate(batch_paths):
                    if path not in options[filename]:
                        options[filename][path] = {}

                    # Ensure batch_options has enough entries
                    if j < len(batch_options):
                        options[filename][path][language] = batch_options[j]
                    else:
                        print(f"Warning: Missing options for path {path} in {language}. Generating placeholder.")
                        # Create placeholder options
                        options[filename][path][language] = ["Translation error"] * options_count

            print(f"Processed batch {i//batch_size + 1}/{(len(string_items) - 1)//batch_size + 1} for {filename}")

        # Save options to CSV for each language
        for language in languages:
            csv_path = os.path.join(
                output_dir, f"{filename}_{language}_options.csv"
            )

            # Skip writing if file already exists
            if os.path.exists(csv_path):
                continue

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                header = ["Path", "Original"] + [f"Option {i+1}" for i in range(options_count)]
                writer.writerow(header)

                for path, string in strings.items():
                    # Check if we have options for this path and language
                    if path in options[filename] and language in options[filename][path]:
                        row = [path, string] + options[filename][path][language]
                        writer.writerow(row)
                    else:
                        # Write placeholder if missing
                        row = [path, string] + ["Translation error"] * options_count
                        writer.writerow(row)

            print(f"Saved translation options for {language} in {filename}")

    return options

def _generate_batch_options(
    strings: List[str],
    language: str,
    model: str,
    options_count: int,
    project_context: str = None
) -> List[List[str]]:
    """
    Generate translation options for a batch of strings.

    Args:
        strings: List of strings to translate
        language: Target language for translation
        model: Model to use for translation
        options_count: Number of options to generate per string
        project_context: Custom project context (or None to use default)

    Returns:
        List of lists of translation options
    """
    # Get the appropriate system prompt using the project context
    system_prompt = get_system_prompt(
        "generate_options",
        language=language,
        options_count=options_count,
        project_context=project_context
    )

    user_message = "Strings to translate:\n" + "\n".join(strings)

    # Use the provided wrapper function
    technical_prompt = {
        "system": system_prompt,
        "user": user_message,
        "response_format": "json"
    }

    try:
        response_text = call_openai(prompt=technical_prompt, model=model)
        print(f"Raw API response: {response_text[:200]}...")  # Print first 200 chars for debugging

        # Parse the response
        try:
            response_data = json.loads(response_text)
            if not isinstance(response_data, dict) or "translations" not in response_data:
                print(f"Invalid response format. Expected dict with 'translations' key. Got: {type(response_data)}")
                return [[f"Error: Invalid response format"] * options_count] * len(strings)

            options = response_data["translations"]
            if not isinstance(options, list):
                print(f"Invalid translations format. Expected list. Got: {type(options)}")
                return [[f"Error: Invalid translations format"] * options_count] * len(strings)

            # Validate and fix each translation option
            for i, opts in enumerate(options):
                if not isinstance(opts, list):
                    print(f"Invalid option format for string {i}. Expected list. Got: {type(opts)}")
                    options[i] = [f"Error: Invalid option format"] * options_count
                    continue

                # Ensure we have the correct number of options
                if len(opts) < options_count:
                    print(f"Warning: Got {len(opts)} options for string {i}, expected {options_count}. Padding with duplicates.")
                    options[i] = opts + [opts[0]] * (options_count - len(opts))
                elif len(opts) > options_count:
                    print(f"Warning: Got {len(opts)} options for string {i}, expected {options_count}. Truncating.")
                    options[i] = opts[:options_count]

                # Validate each option is a string
                options[i] = [str(opt) if opt is not None else "Translation error" for opt in options[i]]

            # Ensure we have the right number of strings
            if len(options) < len(strings):
                print(f"Warning: Got {len(options)} translations but expected {len(strings)}. Padding with empty translations.")
                while len(options) < len(strings):
                    options.append(["Translation error"] * options_count)

            return options

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response text: {response_text[:500]}...")  # Print first 500 chars for debugging
            return [[f"Error: Invalid JSON response"] * options_count] * len(strings)

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return [[f"Error: API call failed"] * options_count] * len(strings)

# Example usage (for testing)
if __name__ == "__main__":
    # Sample data
    extracted = {
        "test.json": {
            "hello": "Hello",
            "welcome": "Welcome to our application",
            "save": "Save"
        }
    }

    # Test with Spanish and French
    languages = ["Spanish", "French"]

    # Create test output directory
    os.makedirs("test_output", exist_ok=True)

    # Generate options
    options = generate_translation_options(
        extracted,
        languages,
        "gpt-3.5-turbo",
        3,
        "test_output"
    )

    # Print results
    for filename, paths in options.items():
        for path, lang_options in paths.items():
            print(f"\nPath: {path}, Original: {extracted[filename][path]}")
            for lang, opts in lang_options.items():
                print(f"  {lang}: {opts}")