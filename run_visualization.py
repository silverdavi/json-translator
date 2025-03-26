import os
from json_translator.visualization import ValidationVisualizer

def main():
    # Get the validation files directory
    validated_dir = "data/translations/validated"
    
    # Get all validation files
    validation_files = [
        os.path.join(validated_dir, f) 
        for f in os.listdir(validated_dir) 
        if f.endswith('_validation.json')
    ]
    
    if not validation_files:
        print("No validation files found in", validated_dir)
        return
    
    # Initialize visualizer
    visualizer = ValidationVisualizer("data/translations")
    
    # Group files by language
    files_by_lang = {}
    for file in validation_files:
        # Extract language from filename (e.g., dashboard_he_validation.json -> he)
        lang = file.split('_')[-2]
        if lang not in files_by_lang:
            files_by_lang[lang] = []
        files_by_lang[lang].append(file)
    
    # Generate reports for each language
    for lang, files in files_by_lang.items():
        print(f"Generating report for language: {lang}")
        visualizer.generate_report(files, lang)
    
    # Generate overall report
    print("Generating overall report")
    visualizer.generate_report(validation_files)
    
    print("Visualization complete! Check the reports directory for results.")

if __name__ == "__main__":
    main() 