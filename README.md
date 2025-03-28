# JSON Translator

A powerful tool for automatically translating JSON localization files to multiple languages using Large Language Models (LLMs).

## Project Overview

JSON Translator is designed to help developers, content creators, and localization teams quickly translate UI strings and other content stored in JSON format. The tool uses OpenAI's API to produce high-quality translations that maintain proper context, formatting, and consistency.

## Features

- **JSON Structure Preservation**: Maintains your original JSON structure while replacing the content with translations
- **Multiple Language Support**: Translate to any language supported by the underlying LLM
- **Batch Processing**: Efficiently processes multiple files and languages
- **Mock Mode**: Test the pipeline without making API calls
- **Detailed Logging**: Track progress and identify issues
- **Flexible Configuration**: Customize the translation process based on your needs
- **Multiple Translation Options**: Generate multiple translation options for better accuracy
- **Background Processing**: Run translations in the background for large files

## Project Structure

```
json-translator/
├── core/                     # Core functionality modules
│   ├── extraction/           # JSON extraction functionality
│   │   └── json_extractor.py # Extract translatable strings from JSON
│   ├── generation/           # JSON generation functionality
│   │   └── json_generator.py # Generate translated JSON files
│   ├── refinement/           # Translation refinement
│   ├── translation/          # Translation logic
│   └── validation/           # Validation logic
├── data/                     # Data files
│   ├── languages.json        # Language code mappings
│   ├── templates/            # Template files
│   └── translations/         # Generated translations output
├── examples/                 # Example files
│   ├── en/                   # Source English JSON files
│   │   ├── homepage.json     # Simple homepage translations
│   │   └── dashboard.json    # More complex nested translations
│   └── output/               # Generated output files
├── prompts/                  # LLM prompt templates
├── tests/                    # Unit and integration tests
│   ├── data/                 # Test data files
│   ├── test_imports.py      # Import validation tests
│   ├── test_main.py         # Main functionality tests
│   ├── test_refiner.py      # Translation refinement tests
│   ├── test_setup.py        # Setup validation tests
│   ├── test_translations.py  # Translation tests
│   └── test_translation_pipeline.py # Pipeline tests
├── utils/                    # Utility functions
│   ├── logging/             # Logging utilities
│   └── validation/          # Validation utilities
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── CODE_OF_CONDUCT.md       # Code of conduct for contributors
├── CONTRIBUTING.md          # Guidelines for contributors
├── LICENSE                  # Project license
├── json_translator_main.py  # Legacy main script
├── run_translation_pipeline.py # Main translation pipeline script
└── requirements.txt         # Python dependencies
```

## Overview

The JSON Translator is organized into logical modules that handle different aspects of the translation pipeline:

1. **Extraction**: Extract translatable strings from JSON files
2. **Translation**: Translate the extracted strings using LLMs
3. **Refinement**: Refine and improve the translations
4. **Validation**: Validate the translations for correctness
5. **Generation**: Generate the final translated JSON files

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your environment variables in `.env` (see `.env.example`)
4. Run the translation pipeline:

```bash
# Basic usage
python run_translation_pipeline.py --source examples/en --languages Spanish,French --output data/translations

# Advanced usage with options
python run_translation_pipeline.py \
    --source examples/en \
    --languages Spanish,French,German \
    --output data/translations \
    --options-count 3 \
    --batch-size 10 \
    --project-description "E-commerce website localization" \
    --debug
```

## Command Line Options

The `run_translation_pipeline.py` script supports the following options:

- `--source`: Directory containing source JSON files (required)
- `--languages`: Comma-separated list of target languages (required)
- `--output`: Output directory for translated files (required)
- `--options-count`: Number of translation options to generate (default: 3)
- `--batch-size`: Number of strings to translate in each batch (default: 20)
- `--project-description`: Description of the project for context generation
- `--regenerate-context`: Regenerate context even if project description is not provided
- `--prompt-config-path`: Path to prompt configuration file
- `--debug`: Enable debug logging
- `--mock`: Run in mock mode without making real API calls

### Model Options

You can specify different models for different parts of the pipeline:

- `--options-model`: Model for generating translation options
- `--selection-model`: Model for selecting the best translations
- `--refinement-model`: Model for refining translations
- `--validation-model`: Model for validating translations
- `--context-model`: Model for generating context

## Examples

The `examples` directory contains sample JSON files for testing:

- `en/homepage.json`: Simple flat JSON with basic UI strings
- `en/dashboard.json`: Nested JSON with more complex structure

Example output will be generated in the specified output directory with the following structure:
```
data/translations/
├── es/                 # Spanish translations
│   ├── homepage.json
│   └── dashboard.json
├── fr/                 # French translations
│   ├── homepage.json
│   └── dashboard.json
└── de/                 # German translations
    ├── homepage.json
    └── dashboard.json
```

## Languages

Supported languages are defined in `data/languages.json`. The system will attempt to match language codes and common aliases (e.g., "chinese" → "Simplified Chinese", "zh-cn" → "Simplified Chinese").

### Special Field Handling

Certain fields in JSON files are treated specially during translation:

- **Version Numbers**: Version strings (e.g., "1.0.0") are preserved exactly as they are in the source
- **Technical Identifiers**: Any field names or values that are technical identifiers should not be translated
- **Format Strings**: Strings containing placeholders (e.g., "%s", "{0}") maintain their format while translating the surrounding text

## Configuration

Configuration options are available through:
1. Command line arguments (highest priority)
2. Environment variables (via `.env` file)
3. Default configuration in the code (lowest priority)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the terms of the LICENSE file included in this repository.

## Output Structure

The translation pipeline generates the following output structure:

```
output_dir/
├── intermediate/                 # All intermediate files
│   ├── extraction/              # String extraction
│   │   └── {filename}_extracted.json
│   ├── options/                 # Translation options
│   │   └── {filename}_options.json
│   ├── selection/               # Selected translations
│   │   └── {filename}_{lang}_selected.csv
│   ├── refinement/              # Refined translations
│   │   └── {filename}_{lang}_refined.csv
│   └── validation/              # Validation results
│       └── {filename}_{lang}_validation.json
├── logs/                        # Logs and reports
│   ├── reports/                 # Translation reports
│   │   └── translation_report_{timestamp}.json
│   └── model_usage/            # Model usage statistics
│       └── usage_{timestamp}.json
└── translations/                # Final translated files
    └── {language_code}/         # Organized by language
        └── {filename}.json
```

### Directory Descriptions

- **intermediate/**: Contains all intermediate files generated during the translation process
  - **extraction/**: Raw extracted strings from source files
  - **options/**: Multiple translation options for each string
  - **selection/**: Selected best translations
  - **refinement/**: Refined translations after selection
  - **validation/**: Validation results for each translation

- **logs/**: Contains all logging and reporting information
  - **reports/**: Detailed translation reports with quality metrics
  - **model_usage/**: Statistics about model usage and costs

- **translations/**: Contains the final translated files
  - Organized by language code (e.g., es/, fr/, de/)
  - Each language directory contains the translated JSON files

This structure provides:
1. Clear separation between intermediate files and final translations
2. Easy cleanup of intermediate files without affecting final translations
3. Better organization of files by pipeline stage
4. Improved logging and reporting capabilities
5. Clear language-specific organization of final translations

## Running the Visualization Tool Separately

If you want to generate visualization reports from existing validation files without running the full translation pipeline, you can use the visualization script:

```bash
python run_visualization.py
```

This will:
1. Look for validation files in the `data/translations/validated/` directory
2. Generate comprehensive reports in `data/translations/reports/report_{timestamp}/`
3. Create visualizations for each language and an overall summary

You can also modify the script to specify custom input and output directories.

## Interpreting the Reports

### Score Categories
Translations are grouped into the following score categories:
- **Perfect (100)**: Flawless translations
- **Excellent (95-99)**: High-quality translations with minor issues
- **Good (90-94)**: Good translations with some room for improvement
- **Fair (80-89)**: Acceptable translations that may need revision
- **Poor (<80)**: Problematic translations that require significant improvement

### Quality Categories
The radar chart visualizes scores across five quality dimensions:
- **Accuracy**: How accurately the translation conveys the original meaning
- **Fluency**: How natural and fluent the translation sounds
- **Terminology**: How consistent and appropriate the terminology is
- **Cultural Appropriateness**: How well the translation fits the target culture
- **Formatting**: How well the translation maintains proper formatting

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the terms of the LICENSE file included in this repository. 