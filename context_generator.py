"""
Module for dynamically generating context configurations based on project descriptions.
Uses LLM to create specialized prompt templates for the translation pipeline.
"""

import json
import logging
from typing import Dict, Any, Optional
from config import API_CONFIG, DEFAULT_PROJECT_DESCRIPTION, load_prompt_templates, save_prompt_templates
from util_call import call_openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_context_configuration(
        project_description: Optional[str] = None,
        model: Optional[str] = None,
        save_to_file: bool = True
) -> Dict[str, Any]:
    """
    Generate specialized context configuration based on a project description.
    
    Args:
        project_description: Description of the project and its translation requirements
                           (optional, defaults to generic description)
        model: LLM model to use (optional, defaults to config)
        save_to_file: Whether to save the generated configuration to disk
    
    Returns:
        Dictionary containing generated context configuration
    """
    # Use default description if none provided
    description = project_description or DEFAULT_PROJECT_DESCRIPTION
    
    # Get model from config if not provided
    if model is None:
        model = API_CONFIG.get("openai", {}).get("defaults", {}).get("context_generator_model", "gpt-4o")
    
    # Load current templates to see structure
    current_templates = load_prompt_templates()
    
    # Create the system prompt
    system_prompt = (
        "You are an expert in creating context and prompts for machine translation systems. "
        "Your task is to generate specialized context and prompts for a translation project based on the description provided."
    )
    
    # Create the user message with project description and expected output format
    user_message = (
        f"I need to create a context configuration for a translation project with the following description:\n\n"
        f"{description}\n\n"
        "Please generate a comprehensive set of prompts and instructions for each stage of the translation pipeline:\n"
        "1. generate_options: For generating multiple translation options for each string\n"
        "2. select_translations: For selecting the best translation from options\n"
        "3. refine_translations: For refining and improving selected translations\n"
        "4. validate_translations: For validating the quality of translations\n\n"
        "Each stage needs a description and detailed instructions that will guide the translation process.\n"
        "Include domain-specific terminology, tone, and style requirements derived from the project description.\n\n"
        "Respond with a JSON object with this structure:\n"
        "{\n"
        '  "base_system_prompt_template": "Template with placeholders for {task_description}, {project_context}, and {additional_instructions}",\n'
        '  "tasks": {\n'
        '    "generate_options": {\n'
        '      "description": "Task description with {language} placeholder",\n'
        '      "instructions": "Detailed instructions with {language} and {options_count} placeholders"\n'
        '    },\n'
        '    ...\n'
        '  },\n'
        '  "default_project_context": "Detailed project context based on the provided description"\n'
        "}\n\n"
        "Make sure to include the keyword 'JSON' in all instruction strings that require a JSON response format."
    )
    
    # Call the LLM with structured prompt
    prompt = {
        "system": system_prompt,
        "user": user_message,
        "response_format": {"type": "json_object"}
    }
    
    try:
        logger.info("Generating context configuration...")
        response_text = call_openai(prompt=prompt, model=model)
        
        # Parse the response
        try:
            config = json.loads(response_text)
            
            # Validate the configuration
            required_keys = ["base_system_prompt_template", "tasks", "default_project_context"]
            required_tasks = ["generate_options", "select_translations", "refine_translations", "validate_translations"]
            
            for key in required_keys:
                if key not in config:
                    config[key] = current_templates.get(key, "")
                    logger.warning(f"Generated config missing '{key}', using default")
            
            for task in required_tasks:
                if task not in config["tasks"]:
                    config["tasks"][task] = current_templates.get("tasks", {}).get(task, {})
                    logger.warning(f"Generated config missing task '{task}', using default")
                else:
                    task_keys = ["description", "instructions"]
                    for task_key in task_keys:
                        if task_key not in config["tasks"][task]:
                            default_value = current_templates.get("tasks", {}).get(task, {}).get(task_key, "")
                            config["tasks"][task][task_key] = default_value
                            logger.warning(f"Generated task '{task}' missing '{task_key}', using default")
            
            # Save to file if requested
            if save_to_file:
                save_prompt_templates(config)
                logger.info("Context configuration saved to file")
            
            return config
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response_text}")
            return current_templates or {}
        
    except Exception as e:
        logger.error(f"Error generating context configuration: {e}")
        return current_templates or {}


if __name__ == "__main__":
    # Example usage
    project_desc = """
    Medical fertility application for tracking and explaining IVF treatments.
    The application contains medical terminology related to fertility treatments,
    and needs to be translated with clinical precision while maintaining empathy.
    The target audience is both medical professionals and patients.
    """
    
    config = generate_context_configuration(project_desc)
    print(json.dumps(config, indent=2)) 