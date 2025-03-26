#!/usr/bin/env python3
"""
Test script for the main entry point json_translator_main.py.
"""

import os
import sys
import subprocess
import logging
import tempfile
import shutil
import json
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("test_main")

def run_command(cmd: List[str], expect_failure: bool = False) -> bool:
    """
    Run a shell command and return whether it succeeded.
    
    Args:
        cmd: Command and arguments to run
        expect_failure: Whether the command is expected to fail
        
    Returns:
        True if the command succeeded (or failed as expected), False otherwise
    """
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=not expect_failure, capture_output=True, text=True)
        
        # Log output if verbose
        logger.debug(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.debug(f"STDERR: {result.stderr}")
        
        if expect_failure:
            if result.returncode == 0:
                logger.error("Command succeeded but was expected to fail")
                return False
            else:
                logger.info("Command failed as expected")
                return True
        else:
            logger.info("Command succeeded")
            return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False

def test_help():
    """Test the --help option."""
    logger.info("Testing --help option...")
    return run_command(["python", "json_translator_main.py", "--help"])

def test_check_only():
    """Test the --check-only option."""
    logger.info("Testing --check-only option...")
    return run_command([
        "python", "json_translator_main.py",
        "--source", "examples/en",
        "--languages", "Spanish",
        "--output", "examples/test_output",
        "--check-only"
    ])

def test_invalid_source():
    """Test with an invalid source directory."""
    logger.info("Testing with invalid source directory...")
    return run_command([
        "python", "json_translator_main.py",
        "--source", "nonexistent_directory",
        "--languages", "Spanish",
        "--output", "examples/test_output",
        "--mock"
    ], expect_failure=True)

def test_mock_translation():
    """Test mock translation."""
    logger.info("Testing mock translation...")
    test_output = "examples/test_main_output"
    
    # Clean up any previous test output
    if os.path.exists(test_output):
        shutil.rmtree(test_output)
    
    success = run_command([
        "python", "json_translator_main.py",
        "--source", "examples/en",
        "--languages", "German,Italian",
        "--output", test_output,
        "--mock"
    ])
    
    if not success:
        return False
    
    # Verify output files exist
    for lang_code in ["de", "it"]:
        lang_dir = os.path.join(test_output, lang_code)
        if not os.path.isdir(lang_dir):
            logger.error(f"Language directory {lang_dir} not found")
            return False
        
        for filename in ["dashboard.json", "homepage.json"]:
            translated_file = os.path.join(lang_dir, filename)
            if not os.path.isfile(translated_file):
                logger.error(f"Translated file {translated_file} not found")
                return False
    
    logger.info("Mock translation test passed")
    return True

def main():
    """Run all tests."""
    tests = [
        test_help,
        test_check_only,
        test_invalid_source,
        test_mock_translation
    ]
    
    failures = 0
    for test in tests:
        try:
            if not test():
                failures += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {str(e)}")
            failures += 1
    
    if failures == 0:
        logger.info("All tests passed successfully!")
    else:
        logger.error(f"{failures} tests failed")
    
    return failures

if __name__ == "__main__":
    sys.exit(main()) 