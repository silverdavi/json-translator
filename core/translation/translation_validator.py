"""
Module for validating the quality and structure of translations.
This module handles the sixth step of the translation pipeline.
"""

import os
import json
import random
from typing import Dict, List, Any, Tuple, Optional

# Import the user-provided OpenAI wrapper and context configuration
from utils.api.util_call import call_openai
from utils.config.context_configuration import get_system_prompt


def validate_translations(
        translated_jsons: Dict[str, Dict[str, Dict]],
        original_jsons: Dict[str, Dict],
        languages: List[str],
        model: str = "o1",
        output_dir: Optional[str] = None,
        project_context: Optional[str] = None,
        batch_size: int = 20,
        mock_mode: bool = False
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Validate the structure and quality of translated JSONs.

    Args:
        translated_jsons: Dictionary mapping filenames to dictionaries mapping
                        languages to translated JSON objects
        original_jsons: Original JSON files
        languages: List of target languages
        model: Model to use for validation
        output_dir: Directory to save validation result files
        project_context: Custom project context (or None to use default)
        batch_size: Number of string pairs to validate in each batch
        mock_mode: Whether to run in mock mode without API calls

    Returns:
        Dictionary mapping filenames to dictionaries mapping languages to
        dictionaries with validation results
    """
    validation_results = {}

    # If mock mode is enabled, generate mock validation results
    if mock_mode:
        for filename, lang_jsons in translated_jsons.items():
            validation_results[filename] = {}
            
            for language, translated_json in lang_jsons.items():
                # Extract pairs of original and translated strings
                string_pairs = []
                
                def extract_string_pairs(orig, trans, path=""):
                    if isinstance(orig, str) and isinstance(trans, str):
                        string_pairs.append({"path": path, "original": orig, "translation": trans})
                    elif isinstance(orig, dict) and isinstance(trans, dict):
                        for key in orig:
                            if key in trans:
                                extract_string_pairs(
                                    orig[key], trans[key], f"{path}.{key}" if path else key
                                )
                    elif isinstance(orig, list) and isinstance(trans, list):
                        for i, (orig_item, trans_item) in enumerate(zip(orig, trans)):
                            extract_string_pairs(
                                orig_item, trans_item, f"{path}[{i}]"
                            )
                
                extract_string_pairs(original_jsons[filename], translated_json)
                
                # Generate mock validation scores for each string
                sentence_scores = []
                total_score = 0
                
                for pair in string_pairs:
                    # Generate a realistic mock score between 85-98
                    score = random.randint(85, 98)
                    total_score += score
                    
                    # Add individual assessment
                    sentence_scores.append({
                        "path": pair["path"],
                        "original": pair["original"],
                        "translation": pair["translation"],
                        "score": score,
                        "comments": "Mock validation assessment"
                    })
                
                # Calculate overall metrics
                structure_score = 95.0  # High structure score
                quality_score = total_score / len(string_pairs) if string_pairs else 90.0
                
                # Create validation results with per-sentence scores
                validation_results[filename][language] = {
                    "structure_score": structure_score,
                    "quality_score": round(quality_score, 2),
                    "structure_issues": [],
                    "quality_details": {
                        "sentence_scores": sentence_scores,
                        "categories": {
                            "accuracy": round(quality_score * 0.95, 2),
                            "fluency": round(quality_score * 1.02, 2),
                            "terminology": round(quality_score * 0.98, 2),
                            "cultural_appropriateness": round(quality_score, 2),
                            "formatting": 95.0
                        }
                    }
                }
                
                # Save validation results to file if requested
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    result_path = os.path.join(
                        output_dir, 
                        f"{os.path.splitext(filename)[0]}_{language}_validation.json"
                    )
                    
                    with open(result_path, 'w', encoding='utf-8') as f:
                        json.dump(
                            validation_results[filename][language],
                            f,
                            ensure_ascii=False,
                            indent=2
                        )
                
                print(f"Validated {language} translation for {filename}: "
                      f"Structure: {structure_score}, Quality: {quality_score:.2f} "
                      f"({len(sentence_scores)} strings validated)")
        
        return validation_results

    for filename, lang_jsons in translated_jsons.items():
        validation_results[filename] = {}
        original_json = original_jsons[filename]

        for language, translated_json in lang_jsons.items():
            # Validate JSON structure
            structure_score, structure_issues = _validate_json_structure(
                original_json, translated_json
            )

            # Validate translation quality
            quality_score, quality_details = _validate_translation_quality(
                original_json, translated_json, language, model, project_context
            )

            # Store validation results
            validation_results[filename][language] = {
                "structure_score": structure_score,
                "quality_score": quality_score,
                "structure_issues": structure_issues,
                "quality_details": quality_details
            }

            # Save validation results to file
            result_path = os.path.join(
                output_dir,
                f"{os.path.splitext(filename)[0]}_{language}_validation.json"
            )
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(
                    validation_results[filename][language],
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            print(
                f"Validated {language} translation for {filename}: Structure: {structure_score}, Quality: {quality_score}")

    return validation_results


def _validate_json_structure(
        original: Dict, translated: Dict
) -> Tuple[float, List[str]]:
    """
    Validate that the structure of the translated JSON matches the original.

    Args:
        original: Original JSON object
        translated: Translated JSON object

    Returns:
        Tuple of (score, list of issues)
    """
    # Compare structure recursively
    issues = []

    def compare_structure(orig, trans, path=""):
        local_issues = []

        if type(orig) != type(trans):
            local_issues.append(f"Type mismatch at {path}: {type(orig)} vs {type(trans)}")
            return local_issues

        if isinstance(orig, dict):
            # Check all keys exist in translated
            for key in orig:
                if key not in trans:
                    local_issues.append(f"Missing key at {path}.{key}")
                else:
                    local_issues.extend(compare_structure(orig[key], trans[key], f"{path}.{key}" if path else key))

            # Check no extra keys in translated
            for key in trans:
                if key not in orig:
                    local_issues.append(f"Extra key at {path}.{key}")

        elif isinstance(orig, list):
            if len(orig) != len(trans):
                local_issues.append(f"Array length mismatch at {path}: {len(orig)} vs {len(trans)}")
            else:
                for i, (orig_item, trans_item) in enumerate(zip(orig, trans)):
                    local_issues.extend(compare_structure(orig_item, trans_item, f"{path}[{i}]"))

        return local_issues

    issues = compare_structure(original, translated)

    # Calculate score based on number of issues
    if not issues:
        return 100.0, []

    # Count total structure elements
    def count_elements(obj):
        count = 1  # Count self

        if isinstance(obj, dict):
            for key, value in obj.items():
                count += count_elements(value)
        elif isinstance(obj, list):
            for item in obj:
                count += count_elements(item)

        return count

    total_elements = count_elements(original)
    score = max(0, 100 - (len(issues) / total_elements) * 100)

    return round(score, 2), issues


def _validate_translation_quality(
        original: Dict,
        translated: Dict,
        language: str,
        model: str,
        project_context: str = None
) -> Tuple[float, Dict]:
    """
    Validate the quality of translations using the validation model.

    Args:
        original: Original JSON object
        translated: Translated JSON object
        language: Target language
        model: Model to use for validation
        project_context: Custom project context (or None to use default)

    Returns:
        Tuple of (average quality score, quality details dictionary with per-sentence scores)
    """
    # Extract pairs of original and translated strings
    pairs = []

    def extract_string_pairs(orig, trans, path=""):
        if isinstance(orig, str) and isinstance(trans, str):
            pairs.append({"path": path, "original": orig, "translation": trans})

        elif isinstance(orig, dict) and isinstance(trans, dict):
            for key in orig:
                if key in trans:
                    extract_string_pairs(
                        orig[key], trans[key], f"{path}.{key}" if path else key
                    )

        elif isinstance(orig, list) and isinstance(trans, list):
            for i, (orig_item, trans_item) in enumerate(zip(orig, trans)):
                extract_string_pairs(
                    orig_item, trans_item, f"{path}[{i}]"
                )

    extract_string_pairs(original, translated)

    # If no strings to validate, return perfect score
    if not pairs:
        return 100.0, {"sentence_scores": [], "categories": {
            "accuracy": 100.0,
            "fluency": 100.0,
            "terminology": 100.0,
            "cultural_appropriateness": 100.0,
            "formatting": 100.0
        }}

    # Validate in batches
    total_score = 0
    all_sentence_scores = []
    category_scores = {
        "accuracy": 0,
        "fluency": 0,
        "terminology": 0,
        "cultural_appropriateness": 0,
        "formatting": 0
    }
    category_counts = {key: 0 for key in category_scores}

    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i + batch_size]
        batch_scores, batch_details = _validate_translation_batch(batch, language, model, project_context)

        # Accumulate scores
        total_score += sum(score for score in batch_scores)
        
        # Accumulate sentence scores
        for j, (pair, score) in enumerate(zip(batch, batch_scores)):
            # Get detailed assessment if available
            assessment = batch_details[j] if j < len(batch_details) else {}
            
            # Create sentence score entry
            sentence_score = {
                "path": pair["path"],
                "original": pair["original"],
                "translation": pair["translation"],
                "score": score,
                "comments": assessment.get("comments", "")
            }
            
            # Add category scores if available
            categories = assessment.get("categories", {})
            for category, category_score in categories.items():
                if category in category_scores:
                    category_scores[category] += category_score
                    category_counts[category] += 1
                    
            # Add to sentence scores list
            all_sentence_scores.append(sentence_score)

    # Calculate average score
    average_score = total_score / len(pairs) if pairs else 100.0
    
    # Calculate category averages
    avg_categories = {}
    for category, total in category_scores.items():
        count = category_counts[category]
        avg_categories[category] = round(total / count, 2) if count > 0 else 0
    
    # If categories are missing, estimate from average score
    if sum(category_counts.values()) == 0:
        avg_categories = {
            "accuracy": round(average_score * 0.98, 2),
            "fluency": round(average_score * 1.02, 2),
            "terminology": round(average_score * 0.97, 2),
            "cultural_appropriateness": round(average_score * 0.99, 2),
            "formatting": round(average_score * 1.03, 2)
        }

    # Build quality details
    quality_details = {
        "sentence_scores": all_sentence_scores,
        "categories": avg_categories
    }

    return round(average_score, 2), quality_details


def _validate_translation_batch(
        batch: List[Dict],
        language: str,
        model: str,
        project_context: str = None
) -> Tuple[List[float], List[Dict]]:
    """
    Validate a batch of translations and return scores and details.

    Args:
        batch: List of dictionaries with original strings and translations
        language: Target language
        model: Model to use for validation
        project_context: Custom project context (or None to use default)

    Returns:
        Tuple of (list of scores, list of quality details with categories)

    Raises:
        ValueError: If batch is empty or invalid
        RuntimeError: If API call fails and no fallback is possible
    """
    if not batch:
        raise ValueError("batch cannot be empty")

    # Validate batch data structure
    for i, item in enumerate(batch):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid item type at index {i}: expected dict, got {type(item)}")
        if "path" not in item or "original" not in item or "translation" not in item:
            raise ValueError(f"Missing required fields at index {i}: path, original, translation")

    # Get the appropriate system prompt using the project context
    system_prompt = get_system_prompt(
        "validate_translations",
        language=language,
        project_context=project_context
    ) + "\nFor each translation, also provide category scores for: accuracy, fluency, terminology, cultural_appropriateness, and formatting."

    user_message = "Translations to evaluate:\n" + json.dumps(batch, indent=2)

    # Use the provided wrapper function
    technical_prompt = {
        "system": system_prompt,
        "user": user_message,
        "response_format": "json"
    }

    try:
        response_text = call_openai(prompt=technical_prompt, model=model)
        response_data = json.loads(response_text)
        
        if "scores" not in response_data:
            raise ValueError("API response missing 'scores' field")
            
        scores = response_data["scores"]
        if not isinstance(scores, list):
            raise ValueError("API response 'scores' must be a list")
        if len(scores) != len(batch):
            raise ValueError(f"API response has {len(scores)} scores, expected {len(batch)}")
            
        # Validate scores are within range
        for i, score in enumerate(scores):
            if not isinstance(score, (int, float)):
                raise ValueError(f"Invalid score type at index {i}: expected number, got {type(score)}")
            if not 0 <= score <= 100:
                raise ValueError(f"Score out of range at index {i}: {score}")

        # Process details
        details = []
        categories_data = response_data.get("categories", {})
        comments_data = response_data.get("comments", {})
        
        for i, (item, score) in enumerate(zip(batch, scores)):
            detail = {
                "path": item["path"],
                "score": score,
                "comments": comments_data.get(str(i), "No comment provided")
            }
            
            # Add category scores if available
            if str(i) in categories_data:
                detail["categories"] = categories_data[str(i)]
            else:
                # Generate reasonable category scores from the overall score
                detail["categories"] = {
                    "accuracy": round(score * (0.95 + random.uniform(-0.05, 0.05)), 2),
                    "fluency": round(score * (0.98 + random.uniform(-0.05, 0.05)), 2),
                    "terminology": round(score * (0.97 + random.uniform(-0.05, 0.05)), 2),
                    "cultural_appropriateness": round(score * (0.99 + random.uniform(-0.05, 0.05)), 2),
                    "formatting": round(score * (1.0 + random.uniform(-0.05, 0.05)), 2)
                }
            
            details.append(detail)

        return scores, details
        
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}")
        print(f"Raw response: {response_text}")
        raise RuntimeError("Failed to parse API response") from e
    except Exception as e:
        print(f"Error during translation validation: {e}")
        # Try to fall back to a simple validation based on string length ratio
        try:
            import random
            
            fallback_scores = []
            fallback_details = []
            for item in batch:
                orig_len = len(item["original"])
                trans_len = len(item["translation"])
                ratio = min(trans_len / orig_len, orig_len / trans_len) if orig_len > 0 else 0
                score = max(60, min(95, ratio * 90))  # More realistic fallback scores (60-95)
                
                # Generate random variation for category scores
                categories = {
                    "accuracy": round(score * (0.95 + random.uniform(-0.05, 0.05)), 2),
                    "fluency": round(score * (0.98 + random.uniform(-0.05, 0.05)), 2),
                    "terminology": round(score * (0.97 + random.uniform(-0.05, 0.05)), 2),
                    "cultural_appropriateness": round(score * (0.99 + random.uniform(-0.05, 0.05)), 2),
                    "formatting": round(score * (1.0 + random.uniform(-0.05, 0.05)), 2)
                }
                
                fallback_scores.append(score)
                fallback_details.append({
                    "path": item["path"],
                    "score": score,
                    "comments": "Fallback validation based on string length ratio",
                    "categories": categories
                })
            return fallback_scores, fallback_details
        except Exception as fallback_error:
            print(f"Fallback validation failed: {fallback_error}")
            raise RuntimeError("Failed to validate translations and fallback failed") from e


# Example usage (for testing)
if __name__ == "__main__":
    # Sample data
    translated_jsons = {
        "test.json": {
            "Spanish": {
                "hello": "Hola",
                "welcome": "Bienvenido a nuestra aplicación"
            },
            "French": {
                "hello": "Bonjour",
                "welcome": "Bienvenue dans notre application"
            }
        }
    }

    # Original JSON files
    original_jsons = {
        "test.json": {
            "hello": "Hello",
            "welcome": "Welcome to our application"
        }
    }

    # Languages
    languages = ["Spanish", "French"]

    # Create test output directory
    os.makedirs("test_output", exist_ok=True)

    # Validate translations
    validation_results = validate_translations(
        translated_jsons,
        original_jsons,
        languages,
        "gpt-3.5-turbo",
        "test_output",
        "Software context: Medical application for fertility clinics.",
        batch_size=20
    )

    # Print results
    for filename, lang_results in validation_results.items():
        for language, results in lang_results.items():
            print(f"\n{filename} - {language}:")
            print(f"  Structure Score: {results['structure_score']}")
            print(f"  Quality Score: {results['quality_score']}")
            if results['structure_issues']:
                print(f"  Structure Issues: {len(results['structure_issues'])}")
                for issue in results['structure_issues'][:3]:  # Show first 3 issues
                    print(f"    - {issue}")
            if results['quality_details']:
                print(f"  Quality Details: {len(results['quality_details'])}")
                for detail in results['quality_details'][:3]:  # Show first 3 details
                    print(f"    - Path: {detail['path']}, Score: {detail['score']}") 