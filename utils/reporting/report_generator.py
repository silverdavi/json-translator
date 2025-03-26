"""
Module for generating summary reports of the translation process.
Provides detailed metrics and quality assessments for each language and file.
"""

import os
import json
import csv
import datetime
from typing import Dict, List, Any, Optional

def generate_summary_report(
        validation_results: Dict[str, Dict[str, Dict[str, Any]]],
        input_dir: str,
        output_dir: str,
        languages: List[str],
        files: List[str],
        models: Dict[str, str],
        log_dir: str
) -> str:
    """
    Generate a summary report of the translation process and quality.
    
    Args:
        validation_results: Results from the validation step
        input_dir: Input directory containing original files
        output_dir: Output directory containing translated files
        languages: List of target languages
        files: List of processed files
        models: Dictionary mapping steps to model names
        log_dir: Directory to save report files
        
    Returns:
        Path to the generated report file
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate timestamp for report
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"translation_report_{timestamp}.json"
    report_path = os.path.join(log_dir, report_filename)
    
    # CSV report for easier viewing
    csv_report_path = os.path.join(log_dir, f"translation_report_{timestamp}.csv")
    
    # Generate report data
    report_data = {
        "timestamp": timestamp,
        "input_directory": input_dir,
        "output_directory": output_dir,
        "languages": languages,
        "files": files,
        "models_used": models,
        "summary": {
            "total_files": len(files),
            "total_languages": len(languages),
            "average_quality_scores": {},
            "average_structure_scores": {}
        },
        "language_results": {},
        "file_results": {}
    }
    
    # Calculate summary metrics
    all_quality_scores = []
    all_structure_scores = []
    language_quality_scores = {lang: [] for lang in languages}
    language_structure_scores = {lang: [] for lang in languages}
    file_quality_scores = {file: [] for file in files}
    file_structure_scores = {file: [] for file in files}
    
    # Process validation results
    for filename, lang_results in validation_results.items():
        for language, results in lang_results.items():
            quality_score = results.get("quality_score", 0)
            structure_score = results.get("structure_score", 0)
            
            # Add to overall metrics
            all_quality_scores.append(quality_score)
            all_structure_scores.append(structure_score)
            
            # Add to language-specific metrics
            if language in language_quality_scores:
                language_quality_scores[language].append(quality_score)
                language_structure_scores[language].append(structure_score)
            
            # Add to file-specific metrics
            if filename in file_quality_scores:
                file_quality_scores[filename].append(quality_score)
                file_structure_scores[filename].append(structure_score)
    
    # Calculate averages
    report_data["summary"]["average_quality_score"] = _calculate_average(all_quality_scores)
    report_data["summary"]["average_structure_score"] = _calculate_average(all_structure_scores)
    
    # Calculate language-specific averages
    for language in languages:
        report_data["language_results"][language] = {
            "average_quality_score": _calculate_average(language_quality_scores[language]),
            "average_structure_score": _calculate_average(language_structure_scores[language])
        }
    
    # Calculate file-specific averages
    for filename in files:
        report_data["file_results"][filename] = {
            "average_quality_score": _calculate_average(file_quality_scores[filename]),
            "average_structure_score": _calculate_average(file_structure_scores[filename])
        }
    
    # Save full report as JSON
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    # Generate CSV summary report
    with open(csv_report_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(["Category", "Item", "Quality Score", "Structure Score"])
        
        # Write overall summary
        writer.writerow([
            "Overall", 
            "Average", 
            f"{report_data['summary']['average_quality_score']:.2f}",
            f"{report_data['summary']['average_structure_score']:.2f}"
        ])
        writer.writerow([])
        
        # Write language summaries
        writer.writerow(["Languages", "", "", ""])
        for language in languages:
            lang_results = report_data["language_results"][language]
            writer.writerow([
                "Language",
                language,
                f"{lang_results['average_quality_score']:.2f}",
                f"{lang_results['average_structure_score']:.2f}"
            ])
        writer.writerow([])
        
        # Write file summaries
        writer.writerow(["Files", "", "", ""])
        for filename in files:
            file_results = report_data["file_results"][filename]
            writer.writerow([
                "File",
                filename,
                f"{file_results['average_quality_score']:.2f}",
                f"{file_results['average_structure_score']:.2f}"
            ])
    
    print(f"Generated summary report at {report_path}")
    print(f"Generated CSV report at {csv_report_path}")
    
    return report_path

def _calculate_average(values: List) -> float:
    """Calculate average of a list of values, handling empty lists."""
    if not values:
        return 0.0
    return sum(values) / len(values) 