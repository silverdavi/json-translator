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
│   └── templates/            # Template files
├── examples/                 # Example files
│   ├── en/                   # Source English JSON files
│   │   ├── homepage.json     # Simple homepage translations
│   │   └── dashboard.json    # More complex nested translations
│   └── output/               # Generated output files
├── prompts/                  # LLM prompt templates
├── tests/                    # Unit and integration tests
├── utils/                    # Utility functions
│   ├── logging/              # Logging utilities
│   └── validation/           # Validation utilities
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
├── CODE_OF_CONDUCT.md        # Code of conduct for contributors
├── CONTRIBUTING.md           # Guidelines for contributors
├── LICENSE                   # Project license
└── requirements.txt          # Python dependencies
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

```python
python json_translator_main.py --source examples/en --languages Spanish,French,German --output examples/output
```

## Examples

The `examples` directory contains sample JSON files for testing:

- `en/homepage.json`: Simple flat JSON with basic UI strings
- `en/dashboard.json`: Nested JSON with more complex structure

## Languages

Supported languages are defined in `data/languages.json`. You can add additional languages by updating this file.

## Configuration

Configuration options are available in `config.py`. You can customize:

- LLM settings
- Translation options
- Output formats
- And more

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the terms of the LICENSE file included in this repository. 