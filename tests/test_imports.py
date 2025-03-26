#!/usr/bin/env python3
"""
Test script to verify imports and basic functionality.
"""

import sys
import importlib
import traceback

def test_import(module_name):
    """Test importing a module and report success or failure."""
    try:
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to import {module_name}: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run tests for all core modules."""
    failures = 0
    
    # Core modules
    core_modules = [
        "core.json.json_extractor",
        "core.json.json_generator",
        "core.translation.translation_generator",
        "core.translation.translation_selector",
        "core.translation.translation_refiner",
        "core.translation.translation_validator",
        "core.translation_pipeline"
    ]
    
    # Utility modules
    util_modules = [
        "utils.api.util_call",
        "utils.api.llm_api",
        "utils.config.config",
        "utils.config.context_configuration",
        "utils.config.context_generator",
        "utils.logging.logging_config",
        "utils.reporting.report_generator",
        "utils.validation.validation"
    ]
    
    # Test core modules
    print("\n=== Testing Core Modules ===")
    for module_name in core_modules:
        if not test_import(module_name):
            failures += 1
    
    # Test utility modules
    print("\n=== Testing Utility Modules ===")
    for module_name in util_modules:
        if not test_import(module_name):
            failures += 1
    
    # Report results
    if failures == 0:
        print("\n✅ All imports successful!")
    else:
        print(f"\n❌ {failures} import failures")
    
    return failures

if __name__ == "__main__":
    sys.exit(main()) 