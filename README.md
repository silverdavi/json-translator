# JSON Translation Pipeline

A powerful tool for translating JSON files into multiple languages using Large Language Models. The pipeline automatically extracts strings, generates translation options, selects the best translations, refines them, and validates the results.

## Features

- **Automatic Context Generation**: Provide a description of your project, and the system will generate specialized translation prompts.
- **Multiple Languages**: Translate to any language supported by the underlying LLM.
- **Translation Options**: Generate multiple translation options for each string and select the best one.
- **Quality Refinement**: Refine translations to improve quality and consistency.
- **Validation**: Automated validation of translation quality with scoring.
- **Comprehensive Reports**: Generate detailed reports of the translation process.
- **Configurable**: Customize models, batch sizes, and other parameters.

## Model Selection

The pipeline uses a combination of specialized models for different tasks:

- **Options Generation (o1)**: Uses a chain-of-thought model to generate multiple translation options. This model excels at creative thinking and generating diverse alternatives.
- **Selection & Validation (gpt-4o)**: Uses a strong non-chain-of-thought model for critical evaluation tasks. This model is better at direct decision-making and quality assessment.

This combination leverages the strengths of each model type:
- Chain-of-thought models (o1) are better at generating creative solutions and exploring multiple possibilities
- Non-chain-of-thought models (gpt-4o) are more efficient at making direct decisions and evaluating quality

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/json-translation-pipeline.git
   cd json-translation-pipeline
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file by copying the example:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file to add your API keys and customize settings.

## Usage

### Basic Usage

Translate JSON files to multiple languages:

```bash
python json_translator_main.py --input-dir "examples/" --output-dir "output/" --languages "Thai,Malay,Simplified Chinese,Traditional Chinese,Hebrew,Korean,Burmese" --options-model "o1" --selection-model "gpt-4o" --refinement-model "o1" --validation-model "gpt-4o" --options-count 4
```

### Advanced Usage

Generate specialized context for your project:

```bash
python json_translator_main.py --languages "Spanish,French,German" --project-description "E-commerce website with product descriptions and user interface elements"
```

Customize models and options:

```bash
python json_translator_main.py --languages "Spanish,French,German" --options-count 5
```

Force regeneration of context configuration:

```bash
python json_translator_main.py --languages "Spanish,French,German" --regenerate-context
```

### Example

Input JSON:
```json
{
  "welcome": "Welcome to our application",
  "buttons": {
    "save": "Save",
    "cancel": "Cancel"
  }
}
```

Output JSON (Spanish):
```json
{
  "welcome": "Bienvenido a nuestra aplicación",
  "buttons": {
    "save": "Guardar",
    "cancel": "Cancelar"
  }
}
```

## Pipeline Steps

1. **String Extraction**: Extract translatable strings from JSON files.
2. **Option Generation**: Generate multiple translation options for each string using chain-of-thought model.
3. **Selection**: Select the best translation from the options using non-chain-of-thought model.
4. **Refinement**: Refine and improve the selected translations using chain-of-thought model.
5. **JSON Generation**: Generate translated JSON files.
6. **Validation**: Validate the quality of translations using non-chain-of-thought model.
7. **Reporting**: Generate summary reports with quality metrics.

## Configuration

Configuration is managed through:

1. The `.env` file for API keys and default settings
2. Command-line arguments for runtime settings
3. JSON prompt templates in `prompts/default_prompts.json`

## Development

### Testing

Run the test suite:

```bash
python -m unittest discover tests
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Add tests for your changes
5. Submit a pull request

## Requirements

- Python 3.8+
- OpenAI API key or compatible LLM API

## Repository Structure

The repository is organized as follows:

- **examples/**: Sample JSON files for testing and demonstrating the pipeline
  - **simple/**: Basic flat JSON structure
  - **nested/**: Hierarchical JSON structure
  - **complex/**: Advanced JSON with arrays and placeholders
- **prompts/**: Configuration files for translation prompts
- **tests/**: Unit and integration tests
- **utils/**: Utility modules for logging, validation, etc.

See the [examples README](examples/README.md) for more information about using the sample files.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for providing the underlying language models
- Contributors who have improved this tool 