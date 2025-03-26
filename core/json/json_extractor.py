"""
Module for extracting translatable strings from JSON files.
This module handles the first step of the translation pipeline.
"""

import os
import json
from typing import Dict, List, Tuple, Any

def extract_strings_from_json(json_obj: Any, prefix: str = "") -> Dict[str, str]:
    """
    Recursively extract all string values from a JSON object along with their paths.
    
    Args:
        json_obj: The JSON object to extract strings from
        prefix: The current path prefix (used for recursion)
        
    Returns:
        Dictionary mapping paths to string values
    """
    result = {}
    
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (dict, list)):
                # Recursively process nested dictionaries and lists
                result.update(extract_strings_from_json(value, new_prefix))
            elif isinstance(value, str):
                # Add string value to result
                result[new_prefix] = value
    elif isinstance(json_obj, list):
        for i, item in enumerate(json_obj):
            new_prefix = f"{prefix}.{i}" if prefix else str(i)
            if isinstance(item, (dict, list)):
                # Recursively process nested dictionaries and lists
                result.update(extract_strings_from_json(item, new_prefix))
            elif isinstance(item, str):
                # Add string value to result
                result[new_prefix] = item
                
    return result

def process_json_files(src_dir: str) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict]]:
    """
    Process all JSON files in the given directory to extract translatable strings.
    
    Args:
        src_dir: The directory containing JSON files
        
    Returns:
        Tuple containing:
        - Dictionary mapping filenames to dictionaries mapping paths to string values
        - Dictionary mapping filenames to original JSON objects
    """
    extracted_strings = {}
    json_files = {}
    
    # Process each JSON file in the directory
    for filename in os.listdir(src_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(src_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                # Extract strings from the JSON file
                file_strings = extract_strings_from_json(json_data)
                
                # Store the extracted strings and original JSON
                extracted_strings[filename] = file_strings
                json_files[filename] = json_data
                
                print(f"Processed {filename}: {len(file_strings)} strings extracted")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    
    return extracted_strings, json_files

# Example usage (for testing)
if __name__ == "__main__":
    # Process JSON files in the examples directory
    extracted, jsons = process_json_files("examples/en")
    
    # Print extracted strings for each file
    for filename, strings in extracted.items():
        print(f"\n{filename}:")
        for path, value in strings.items():
            print(f"  {path}: {value}") 