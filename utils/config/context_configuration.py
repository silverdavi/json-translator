"""
Module for generating and managing context configurations.
Provides specialized translation prompts with context.
"""

import os
import json
from typing import Dict, Any, Optional

# Default path for the prompt configuration
DEFAULT_PROMPT_CONFIG_PATH = "prompts/default_prompts.json"

# Default context for general translation tasks
DEFAULT_CONTEXT = "Translation of user interface elements and general web content."

# Default project description for general purpose translations
DEFAULT_PROJECT_DESCRIPTION = """
This is a general-purpose user interface translation project. The text includes
UI elements like buttons, labels, messages, and general content from a web application.
Translations should maintain the original meaning while being natural and idiomatic
in the target language.
"""

def get_system_prompt(
    prompt_type: str,
    language: Optional[str] = None,
    options_count: Optional[int] = None,
    project_context: Optional[str] = None
) -> str:
    """
    Get a system prompt for a specific task with optional context.
    
    Args:
        prompt_type: Type of prompt to retrieve (e.g., 'generate_options', 'select_translations')
        language: Target language (optional)
        options_count: Number of translation options to generate (optional)
        project_context: Custom project context (optional)
        
    Returns:
        System prompt with appropriate context
    """
    # Load default prompts
    try:
        with open(DEFAULT_PROMPT_CONFIG_PATH, "r", encoding="utf-8") as f:
            prompt_templates = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file not found or invalid, use minimal default prompts
        prompt_templates = _get_minimal_prompt_templates()
    
    # Get the base prompt template
    if prompt_type not in prompt_templates:
        raise ValueError(f"Invalid prompt type: {prompt_type}")
    
    base_prompt = prompt_templates[prompt_type]
    
    # Format with variables if provided
    context = project_context or DEFAULT_CONTEXT
    format_vars = {
        "language": language or "the target language",
        "options_count": options_count or 3,
        "project_context": context
    }
    
    return base_prompt.format(**format_vars)

def _get_minimal_prompt_templates() -> Dict[str, str]:
    """
    Get minimal default prompt templates as a fallback.
    
    Returns:
        Dictionary of minimal prompt templates
    """
    return {
        "generate_options": """
            You are a professional translator specializing in {language}.
            
            Project Context: {project_context}
            
            Generate {options_count} different translations for each of the following English strings.
            Each translation should be accurate but may use different wording or phrasing.
            
            Respond with a JSON object with a 'translations' array containing arrays of options.
        """,
        "select_translations": """
            You are a translation expert for {language}.
            
            Project Context: {project_context}
            
            For each string below, select the BEST translation option from the provided choices.
            Consider accuracy, naturalness, and cultural appropriateness.
        """,
        "refine_translations": """
            You are a professional translator and language consultant for {language}.
            
            Project Context: {project_context}
            
            Refine the following translations to improve their quality. 
            Fix any errors, improve naturalness, and ensure consistency of terminology.
        """,
        "validate_translations": """
            You are a translation quality assessor specializing in {language}.
            
            Project Context: {project_context}
            
            Evaluate the quality of each translation below on a scale of 0-100:
            - 90-100: Perfect or near-perfect translation
            - 70-89: Good translation with minor issues
            - 50-69: Acceptable translation with some issues
            - 30-49: Poor translation with significant issues
            - 0-29: Incorrect or unintelligible translation
            
            Respond with a JSON object containing a 'scores' array with a score for each translation.
        """
    } 