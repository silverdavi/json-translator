#!/usr/bin/env python3
"""
Test script for the _refine_batch function in translation_refiner.py
"""

import json
from core.translation.translation_refiner import _refine_batch

def test_refine_batch():
    # Sample batch of translations
    batch = [
        {
            "path": "welcome",
            "original": "Welcome to our application",
            "translation": "ברוכים הבאים לאפליקציה שלנו"
        },
        {
            "path": "login",
            "original": "Log in",
            "translation": "התחבר"
        },
        {
            "path": "signup",
            "original": "Sign up",
            "translation": "הרשמה"
        },
        {
            "path": "logout",
            "original": "Log out",
            "translation": "התנתק"
        }
    ]

    # Call the refine_batch function
    print("Testing refine_batch function with Hebrew translations...")
    refined = _refine_batch(batch, "he", "o1", "test.json")
    
    # Print the results
    print("\nRefined translations:")
    for item in refined:
        print(f"Path: {item['path']}, Refined: {item['refined']}")

if __name__ == "__main__":
    test_refine_batch() 