"""
Module for extracting translatable strings from JSON files.
This module handles the first step of the translation pipeline.
"""

import os
import csv
from typing import Dict, List, Any


def extract_strings(json_files: Dict[str, Dict], output_dir: str) -> Dict[str, Dict[str, str]]:
    """
    Extract all translatable strings from JSON files.

    Args:
        json_files: Dictionary with file names as keys and JSON data as values
        output_dir: Directory to save extracted strings CSV files

    Returns:
        Dictionary with file names as keys and dictionaries mapping paths to string values
    """
    extracted = {}

    for filename, json_data in json_files.items():
        extracted[filename] = {}
        _extract_strings_recursive(json_data, [], extracted[filename])

        # Save extracted strings to CSV
        csv_path = os.path.join(output_dir, f"{filename}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Path", "String"])
            for path, string in extracted[filename].items():
                writer.writerow([path, string])

        print(f"Extracted {len(extracted[filename])} strings from {filename}")

    return extracted


def _extract_strings_recursive(obj: Any, path: List[str], result: Dict[str, str]):
    """Recursively extract strings from a JSON object."""
    if isinstance(obj, str):
        path_str = ".".join(path)
        result[path_str] = obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            _extract_strings_recursive(value, path + [key], result)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _extract_strings_recursive(item, path + [str(i)], result)