from .visualization import ValidationVisualizer

class TranslationPipeline:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.visualizer = ValidationVisualizer(config.output_dir)

    def _validate_translations(self, file_path: str, language: str) -> Dict[str, float]:
        """Validate translations and generate visualization reports."""
        validation_result = self._perform_validation(file_path, language)
        
        # Generate visualization report
        validation_file = os.path.join(self.config.output_dir, "validated", f"{os.path.splitext(os.path.basename(file_path))[0]}_{language}_validation.json")
        self.visualizer.generate_report([validation_file], language)
        
        return validation_result

    def run(self):
        """Run the translation pipeline with visualization."""
        # Generate overall report if multiple languages
        if len(self.config.languages) > 1:
            validation_files = []
            for file_path in self.config.source_files:
                for language in self.config.languages:
                    validation_file = os.path.join(self.config.output_dir, "validated", 
                        f"{os.path.splitext(os.path.basename(file_path))[0]}_{language}_validation.json")
                    if os.path.exists(validation_file):
                        validation_files.append(validation_file)
            
            if validation_files:
                self.visualizer.generate_report(validation_files) 