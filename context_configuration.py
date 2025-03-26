"""
Configuration module for project context and prompts.
Provides consistent context about the project across the translation pipeline.
"""

import logging
from typing import Dict, Any, Optional
from config import load_prompt_templates, DEFAULT_PROJECT_DESCRIPTION

# Configure logging
logger = logging.getLogger(__name__)

# Load prompt templates from file
_TEMPLATES = load_prompt_templates()

# Default project context (can be overridden via command line)
DEFAULT_PROJECT_CONTEXT = _TEMPLATES.get("default_project_context", DEFAULT_PROJECT_DESCRIPTION)

# Base system prompt template
BASE_SYSTEM_PROMPT_TEMPLATE = _TEMPLATES.get("base_system_prompt_template", 
    "You are a professional translator specializing in software localization. "
    "Your current task is to {task_description}.\n\n"
    "{project_context}\n\n"
    "{additional_instructions}"
)

# Task definitions with defaults if not found in templates
TASKS = _TEMPLATES.get("tasks", {})

# Define defaults for required tasks if they're missing
REQUIRED_TASKS = ["generate_options", "select_translations", "refine_translations", "validate_translations"]
DEFAULT_TASKS = {
    "generate_options": {
        "description": "generate multiple translation options for each string in {language}",
        "instructions": "For each string, provide {options_count} different translation options. "
                      "You must respond with a JSON object containing a \"translations\" array."
    },
    "select_translations": {
        "description": "select the best translation option for each string in {language}",
        "instructions": "Review the translation options and select the best one for each string. "
                      "You must respond with a JSON object containing a \"selections\" array."
    },
    "refine_translations": {
        "description": "refine and improve the selected translations to {language}",
        "instructions": "Improve each translation to make it more natural and accurate. "
                      "You must respond with a JSON object containing a \"refined_translations\" array."
    },
    "validate_translations": {
        "description": "evaluate the quality of the final translations to {language}",
        "instructions": "Rate each translation on a scale from 0 to 100. "
                      "You must respond with a JSON object containing a \"scores\" array."
    }
}

# Ensure all required tasks have appropriate configuration
for task in REQUIRED_TASKS:
    if task not in TASKS:
        TASKS[task] = DEFAULT_TASKS[task]
        logger.warning(f"Task '{task}' not found in templates, using default")
    else:
        # Ensure all required fields exist
        for field in ["description", "instructions"]:
            if field not in TASKS[task]:
                TASKS[task][field] = DEFAULT_TASKS[task][field]
                logger.warning(f"Field '{field}' not found in task '{task}', using default")


def get_system_prompt(task_key: str, language: Optional[str] = None, 
                     options_count: Optional[int] = None, 
                     project_context: Optional[str] = None) -> str:
    """
    Generate a system prompt for a specific task and language.

    Args:
        task_key: The task identifier (generate_options, select_best, etc.)
        language: Target language (if applicable)
        options_count: Number of options to generate (if applicable)
        project_context: Custom project context (or None to use default)

    Returns:
        Formatted system prompt string
    """
    if task_key not in TASKS:
        logger.error(f"Task '{task_key}' not found in TASKS dictionary")
        raise ValueError(f"Invalid task key: {task_key}")

    task = TASKS[task_key]

    # Use custom project context if provided, otherwise use default
    context = project_context if project_context is not None else DEFAULT_PROJECT_CONTEXT

    # Update task description to include language
    task_description = task["description"]
    if language and "{language}" in task_description:
        task_description = task_description.format(language=language)

    # Format task-specific instructions
    instructions = task["instructions"]
    format_params = {}
    
    if language:
        format_params["language"] = language
    if options_count:
        format_params["options_count"] = options_count
        
    try:
        instructions = instructions.format(**format_params)
    except KeyError as e:
        logger.warning(f"Missing parameter for instructions formatting: {e}")
        # Continue with unformatted instructions

    # Build the complete prompt
    system_prompt = BASE_SYSTEM_PROMPT_TEMPLATE.format(
        project_context=context,
        task_description=task_description,
        additional_instructions=instructions
    )

    return system_prompt


# Debug function to verify prompt generation
def debug_prompt(task_key: str, language: Optional[str] = None, 
                options_count: Optional[int] = None, 
                project_context: Optional[str] = None) -> str:
    """Generate and print a prompt for debugging purposes"""
    prompt = get_system_prompt(task_key, language, options_count, project_context)
    print(f"\nDEBUG - Generated prompt for task '{task_key}', language '{language}':")
    print("="*80)
    print(prompt)
    print("="*80)
    return prompt