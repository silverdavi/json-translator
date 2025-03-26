"""
Logging configuration for the JSON translation pipeline.
Centralizes logging setup and model usage tracking.
"""

import os
import logging
import datetime
from typing import Dict, Optional

# Define model usage tracker for analytics
class ModelUsageTracker:
    """Track usage of different models throughout the pipeline."""
    
    def __init__(self):
        """Initialize the usage tracker."""
        self.model_usage = {}
        self.start_time = datetime.datetime.now()
    
    def add_calls(self, model: str, calls: int = 1):
        """Add API calls to the usage tracker."""
        if model not in self.model_usage:
            self.model_usage[model] = {'calls': 0, 'tokens': 0, 'words': 0}
        self.model_usage[model]['calls'] += calls
    
    def add_tokens(self, model: str, tokens: int):
        """Add token usage to the tracker."""
        if model not in self.model_usage:
            self.model_usage[model] = {'calls': 0, 'tokens': 0, 'words': 0}
        self.model_usage[model]['tokens'] += tokens
    
    def add_words(self, model: str, words: int):
        """Add word count as a proxy for token usage."""
        if model not in self.model_usage:
            self.model_usage[model] = {'calls': 0, 'tokens': 0, 'words': 0}
        self.model_usage[model]['words'] += words
        # Roughly estimate tokens as 1.3 * words
        self.model_usage[model]['tokens'] += int(words * 1.3)
        # Also count as a call
        self.model_usage[model]['calls'] += 1
    
    def get_usage(self, model: Optional[str] = None) -> Dict:
        """Get usage statistics for all models or a specific model."""
        if model:
            return self.model_usage.get(model, {'calls': 0, 'tokens': 0, 'words': 0})
        return self.model_usage
    
    def print_summary(self):
        """Print a summary of model usage."""
        total_duration = datetime.datetime.now() - self.start_time
        
        logging.info(f"===== Model Usage Summary =====")
        logging.info(f"Total duration: {total_duration}")
        
        total_calls = sum(stats['calls'] for stats in self.model_usage.values())
        total_tokens = sum(stats['tokens'] for stats in self.model_usage.values())
        
        logging.info(f"Total API calls: {total_calls}")
        logging.info(f"Estimated total tokens: {total_tokens}")
        
        logging.info(f"Breakdown by model:")
        for model, stats in self.model_usage.items():
            logging.info(f"  - {model}: {stats['calls']} calls, ~{stats['tokens']} tokens")
        
        print(f"\n===== Model Usage Summary =====")
        print(f"Total duration: {total_duration}")
        print(f"Total API calls: {total_calls}")
        print(f"Estimated total tokens: {total_tokens}")
        
        print(f"\nBreakdown by model:")
        for model, stats in self.model_usage.items():
            print(f"  - {model}: {stats['calls']} calls, ~{stats['tokens']} tokens")

# Global model usage tracker
model_usage = ModelUsageTracker()

def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO"):
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to log file (optional)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Add file handler if log file is specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logging.getLogger().addHandler(file_handler)
    
    # Adjust other loggers
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    logging.info(f"Logging initialized at level {log_level}")
    
    return logging.getLogger(__name__) 