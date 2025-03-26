"""
Module for generating summary reports of the translation process.
This module handles the final step of the translation pipeline.
"""

import os
import json
import csv
import datetime
from typing import Dict, List, Any


def generate_summary_report(
        validation_results: Dict[str, Dict[str, Dict[str, Any]]],
        input_dir: str,
        output_dir: str,
        languages: List[str],
        files_processed: List[str],
        models_used: Dict[str, str],
        logs_dir: str
) -> None:
    """
    Generate a summary report of the translation process.

    Args:
        validation_results: Results from the validation step
        input_dir: Input directory containing original files
        output_dir: Output directory for translated files
        languages: List of target languages
        files_processed: List of processed filenames
        models_used: Dictionary mapping pipeline steps to model names
        logs_dir: Directory to save report files
    """
    # Create detailed report data
    report = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_directory": input_dir,
        "output_directory": output_dir,
        "languages": list(languages),
        "files_processed": list(files_processed),
        "models_used": dict(models_used),
        "validation_results": validation_results
    }

    # Calculate overall statistics
    statistics = _calculate_statistics(validation_results, languages)
    
    # Convert any dict_keys to lists in statistics
    statistics["by_language"] = dict(statistics["by_language"])
    statistics["by_file"] = dict(statistics["by_file"])
    
    report["statistics"] = statistics

    # Save the detailed JSON report
    report_path = os.path.join(logs_dir, "translation_summary_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Create a CSV summary of scores
    _generate_scores_csv(validation_results, logs_dir)

    # Create a CSV summary of statistics
    _generate_statistics_csv(statistics, logs_dir)

    # Generate a markdown report for easy reading
    _generate_markdown_report(report, logs_dir)

    print(f"Summary report generated: {report_path}")


def _calculate_statistics(
        validation_results: Dict[str, Dict[str, Dict[str, Any]]],
        languages: List[str]
) -> Dict[str, Any]:
    """
    Calculate overall statistics from validation results.

    Args:
        validation_results: Results from the validation step
        languages: List of target languages

    Returns:
        Dictionary with statistics
    """
    statistics = {
        "overall": {
            "structure_score": 0,
            "quality_score": 0,
            "total_files": 0,
            "total_languages": len(languages)
        },
        "by_language": {},
        "by_file": {}
    }

    # Initialize language statistics
    for language in languages:
        statistics["by_language"][language] = {
            "structure_score": 0,
            "quality_score": 0,
            "file_count": 0
        }

    # Calculate statistics
    total_evaluations = 0

    for filename, lang_results in validation_results.items():
        # Initialize file statistics
        statistics["by_file"][filename] = {
            "structure_score": 0,
            "quality_score": 0,
            "language_count": 0
        }

        file_total_evaluations = 0

        for language, results in lang_results.items():
            # Add to overall statistics
            statistics["overall"]["structure_score"] += results["structure_score"]
            statistics["overall"]["quality_score"] += results["quality_score"]

            # Add to language statistics
            statistics["by_language"][language]["structure_score"] += results["structure_score"]
            statistics["by_language"][language]["quality_score"] += results["quality_score"]
            statistics["by_language"][language]["file_count"] += 1

            # Add to file statistics
            statistics["by_file"][filename]["structure_score"] += results["structure_score"]
            statistics["by_file"][filename]["quality_score"] += results["quality_score"]
            statistics["by_file"][filename]["language_count"] += 1

            total_evaluations += 1
            file_total_evaluations += 1

        # Calculate averages for this file
        if file_total_evaluations > 0:
            statistics["by_file"][filename]["structure_score"] /= file_total_evaluations
            statistics["by_file"][filename]["quality_score"] /= file_total_evaluations
            statistics["by_file"][filename]["structure_score"] = round(
                statistics["by_file"][filename]["structure_score"], 2)
            statistics["by_file"][filename]["quality_score"] = round(statistics["by_file"][filename]["quality_score"],
                                                                     2)

    # Calculate averages
    statistics["overall"]["total_files"] = len(validation_results)

    if total_evaluations > 0:
        statistics["overall"]["structure_score"] /= total_evaluations
        statistics["overall"]["quality_score"] /= total_evaluations
        statistics["overall"]["structure_score"] = round(statistics["overall"]["structure_score"], 2)
        statistics["overall"]["quality_score"] = round(statistics["overall"]["quality_score"], 2)

    # Calculate averages for each language
    for language in languages:
        lang_stats = statistics["by_language"][language]
        if lang_stats["file_count"] > 0:
            lang_stats["structure_score"] /= lang_stats["file_count"]
            lang_stats["quality_score"] /= lang_stats["file_count"]
            lang_stats["structure_score"] = round(lang_stats["structure_score"], 2)
            lang_stats["quality_score"] = round(lang_stats["quality_score"], 2)

    return statistics


def _generate_scores_csv(
        validation_results: Dict[str, Dict[str, Dict[str, Any]]],
        logs_dir: str
) -> None:
    """
    Generate a CSV file with all validation scores.

    Args:
        validation_results: Results from the validation step
        logs_dir: Directory to save the CSV file
    """
    csv_path = os.path.join(logs_dir, "translation_scores.csv")

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Filename", "Language", "Structure Score", "Quality Score"])

        for filename, lang_results in validation_results.items():
            for language, results in lang_results.items():
                writer.writerow([
                    filename,
                    language,
                    results["structure_score"],
                    results["quality_score"]
                ])


def _generate_statistics_csv(
        statistics: Dict[str, Any],
        logs_dir: str
) -> None:
    """
    Generate a CSV file with summary statistics.

    Args:
        statistics: Dictionary with calculated statistics
        logs_dir: Directory to save the CSV file
    """
    # Generate language statistics CSV
    lang_csv_path = os.path.join(logs_dir, "language_statistics.csv")

    with open(lang_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Language", "Structure Score", "Quality Score", "File Count"])

        for language, stats in statistics["by_language"].items():
            writer.writerow([
                language,
                stats["structure_score"],
                stats["quality_score"],
                stats["file_count"]
            ])

    # Generate file statistics CSV
    file_csv_path = os.path.join(logs_dir, "file_statistics.csv")

    with open(file_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Filename", "Structure Score", "Quality Score", "Language Count"])

        for filename, stats in statistics["by_file"].items():
            writer.writerow([
                filename,
                stats["structure_score"],
                stats["quality_score"],
                stats["language_count"]
            ])


def _generate_markdown_report(
        report: Dict[str, Any],
        logs_dir: str
) -> None:
    """
    Generate a markdown report for easy reading.

    Args:
        report: Dictionary with report data
        logs_dir: Directory to save the markdown file
    """
    md_path = os.path.join(logs_dir, "translation_report.md")

    with open(md_path, 'w', encoding='utf-8') as f:
        # Title and summary
        f.write("# JSON Translation Pipeline Report\n\n")
        f.write(f"**Generated:** {report['timestamp']}\n\n")

        # Overall statistics
        stats = report["statistics"]["overall"]
        f.write("## Overall Statistics\n\n")
        f.write(f"- **Structure Score:** {stats['structure_score']}/100\n")
        f.write(f"- **Quality Score:** {stats['quality_score']}/100\n")
        f.write(f"- **Total Files:** {stats['total_files']}\n")
        f.write(f"- **Total Languages:** {stats['total_languages']}\n\n")

        # Models used
        f.write("## Models Used\n\n")
        for step, model in report["models_used"].items():
            f.write(f"- **{step.replace('_', ' ').title()}:** {model}\n")
        f.write("\n")

        # Language statistics
        f.write("## Language Statistics\n\n")
        f.write("| Language | Structure Score | Quality Score | File Count |\n")
        f.write("|----------|----------------|--------------|------------|\n")

        for language, stats in report["statistics"]["by_language"].items():
            f.write(f"| {language} | {stats['structure_score']} | {stats['quality_score']} | {stats['file_count']} |\n")
        f.write("\n")

        # File statistics
        f.write("## File Statistics\n\n")
        f.write("| Filename | Structure Score | Quality Score | Language Count |\n")
        f.write("|----------|----------------|--------------|---------------|\n")

        for filename, stats in report["statistics"]["by_file"].items():
            f.write(
                f"| {filename} | {stats['structure_score']} | {stats['quality_score']} | {stats['language_count']} |\n")
        f.write("\n")

        # Files processed
        f.write("## Files Processed\n\n")
        for filename in report["files_processed"]:
            f.write(f"- {filename}\n")
        f.write("\n")

        # Languages processed
        f.write("## Languages\n\n")
        for language in report["languages"]:
            f.write(f"- {language}\n")
        f.write("\n")

        # Paths
        f.write("## Directories\n\n")
        f.write(f"- **Input Directory:** {report['input_directory']}\n")
        f.write(f"- **Output Directory:** {report['output_directory']}\n")


# Example usage (for testing)
if __name__ == "__main__":
    # Sample validation results
    validation_results = {
        "dashboard.json": {
            "Spanish": {
                "structure_score": 100.0,
                "quality_score": 92.5,
                "structure_issues": [],
                "quality_details": []
            },
            "French": {
                "structure_score": 100.0,
                "quality_score": 94.8,
                "structure_issues": [],
                "quality_details": []
            }
        },
        "settings.json": {
            "Spanish": {
                "structure_score": 98.5,
                "quality_score": 90.2,
                "structure_issues": ["Missing key at settings.advanced"],
                "quality_details": []
            },
            "French": {
                "structure_score": 99.0,
                "quality_score": 91.5,
                "structure_issues": [],
                "quality_details": []
            }
        }
    }

    # Create test output directory
    logs_dir = "test_output/logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Generate summary report
    generate_summary_report(
        validation_results,
        "input_dir",
        "output_dir",
        ["Spanish", "French"],
        ["dashboard.json", "settings.json"],
        {
            "options_generation": "gpt-4o",
            "selection": "gpt-4o-mini",
            "refinement": "gpt-4o",
            "validation": "gpt-3.5-turbo"
        },
        logs_dir
    )

    print(f"Test report generated in {logs_dir}")