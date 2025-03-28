"""
Logging configuration for the JSON translation pipeline.
Centralizes logging setup and model usage tracking.
"""

import os
import logging
import datetime
from typing import Dict, Optional
import json

# Define model usage tracker for analytics
class ModelUsage:
    """Track and log model usage statistics."""
    
    def __init__(self):
        self.usage = {}
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def add_words(self, model: str, count: int):
        """Add word count for a model."""
        if model not in self.usage:
            self.usage[model] = 0
        self.usage[model] += count
    
    def print_summary(self):
        """Print summary of model usage."""
        if not self.usage:
            return
            
        print("\nModel Usage Summary:")
        print("-" * 50)
        total_words = 0
        for model, words in self.usage.items():
            print(f"{model}: {words:,} words")
            total_words += words
        print("-" * 50)
        print(f"Total: {total_words:,} words")
        
        # Save usage to file
        usage_dir = os.path.join("logs", "model_usage")
        os.makedirs(usage_dir, exist_ok=True)
        usage_file = os.path.join(usage_dir, f"usage_{self.timestamp}.json")
        
        with open(usage_file, 'w') as f:
            json.dump({
                "timestamp": self.timestamp,
                "usage": self.usage,
                "total_words": total_words
            }, f, indent=2)
        
        print(f"\nUsage details saved to {usage_file}")

# Create global instance
model_usage = ModelUsage()

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