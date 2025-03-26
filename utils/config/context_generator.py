"""
Module for generating specialized context for translation tasks.
Uses LLMs to create domain-specific prompts for better translations.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from utils.api.util_call import call_openai
from utils.config.context_configuration import DEFAULT_PROJECT_DESCRIPTION

# Default path for saving generated context configuration
DEFAULT_CONTEXT_CONFIG_PATH = "prompts/context_config.json"

def generate_context_configuration(
        project_description: Optional[str] = None,
        model: str = "gpt-4o",
        save_to_file: bool = True,
        context_config_path: Optional[str] = None,
        prompt_config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate specialized context configuration for translation tasks.
    
    Args:
        project_description: Description of the project (optional)
        model: Model to use for context generation
        save_to_file: Whether to save the generated context to a file
        context_config_path: Path to save the generated context (optional)
        prompt_config_path: Path to custom prompt templates (optional)
        
    Returns:
        Dictionary with the generated context configuration
    """
    # Use provided description or default
    description = project_description or DEFAULT_PROJECT_DESCRIPTION
    
    # Create the prompt for context generation
    system_prompt = """
    You are an expert localization engineer with deep experience in software and content localization across many languages and cultures.
    
    Your task is to analyze a project description and create specialized context that will help translators produce high-quality, culturally appropriate translations.
    
    For the project described, please provide:
    
    1. DOMAIN UNDERSTANDING: Identify the specific domain (e.g., e-commerce, healthcare, gaming) and explain key terminology that should be consistently translated
    
    2. AUDIENCE ANALYSIS: Define the target audience and their expectations regarding formality, technical language, and cultural references
    
    3. STYLE GUIDELINES: Provide guidance on tone, formality level, and writing style appropriate for this content
    
    4. TECHNICAL CONSTRAINTS: Note any character limitations, UI considerations, or technical concerns for translations
    
    5. CULTURAL ADAPTATION: Identify elements that may need cultural adaptation rather than direct translation
    
    6. LANGUAGE-SPECIFIC NOTES: If applicable, provide guidance for specific language groups (e.g., right-to-left languages, languages with gender agreement)
    
    Your output should be comprehensive yet concise, giving translators the context they need to produce translations that feel native and appropriate.
    """
    
    user_prompt = f"""
    Project Description:
    {description}
    
    Please generate a specialized context for this translation project.
    Respond with JSON containing a 'default_project_context' field with the context.
    """
    
    # Call the model to generate specialized context
    technical_prompt = {
        "system": system_prompt,
        "user": user_prompt,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response_text = call_openai(prompt=technical_prompt, model=model)
        context_config = json.loads(response_text)
        
        # Validate the response format
        if "default_project_context" not in context_config:
            logging.warning("API response missing 'default_project_context' field")
            context_config = {"default_project_context": description}
    except Exception as e:
        logging.error(f"Error generating context configuration: {e}")
        # Fallback to using the project description directly
        context_config = {"default_project_context": description}
    
    # Save to file if requested
    if save_to_file:
        save_path = context_config_path or DEFAULT_CONTEXT_CONFIG_PATH
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(context_config, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved context configuration to {save_path}")
        except Exception as e:
            logging.error(f"Error saving context configuration: {e}")
    
    return context_config 