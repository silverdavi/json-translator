#!/usr/bin/env python3
"""
Test script to verify that the package structure is correctly set up.
"""

import os
import sys
import json

def print_section(title):
    print("\n" + "=" * 40)
    print(f" {title} ".center(40, "="))
    print("=" * 40)

def main():
    # Check Python version
    print_section("Python Version")
    print(f"Python {sys.version}")
    
    # Check package structure
    print_section("Package Structure")
    for package in ["core", "utils", "data", "examples", "prompts"]:
        exists = os.path.isdir(package)
        print(f"{package}: {'✓' if exists else '✗'}")
    
    # Check language codes file
    print_section("Language Codes")
    try:
        with open("data/languages.json", "r", encoding="utf-8") as f:
            language_codes = json.load(f)
        print(f"Found {len(language_codes)} language codes")
        print(f"Sample: {list(language_codes.items())[:3]}")
    except Exception as e:
        print(f"Error loading language codes: {e}")
    
    # Check example files
    print_section("Example Files")
    try:
        examples = os.listdir("examples/en")
        print(f"Found {len(examples)} example files:")
        for example in examples:
            print(f"- {example}")
    except Exception as e:
        print(f"Error loading examples: {e}")
    
    # Check prompt templates
    print_section("Prompt Templates")
    try:
        with open("prompts/default_prompts.json", "r", encoding="utf-8") as f:
            prompts = json.load(f)
        print(f"Found prompt template file with following keys:")
        for key in prompts:
            if key == "tasks":
                print(f"- {key} (Contains {len(prompts[key])} tasks)")
                for task in prompts[key]:
                    print(f"  - {task}")
            else:
                print(f"- {key}")
    except Exception as e:
        print(f"Error loading prompt templates: {e}")
    
    # Check if we can import key modules
    print_section("Module Imports")
    try:
        sys.path.insert(0, os.getcwd())
        import core
        import utils
        print("Successfully imported core and utils packages")
    except Exception as e:
        print(f"Error importing packages: {e}")
    
    print("\nSetup verification complete!")

if __name__ == "__main__":
    main() 