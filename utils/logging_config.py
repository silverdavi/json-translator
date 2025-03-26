import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs"
) -> None:
    """
    Set up logging configuration with both console and file handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional specific log file name
        log_dir: Directory to store log files
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Generate log filename if not provided
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"translation_pipeline_{timestamp}.log"
    
    log_file_path = log_path / log_file
    
    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    logging.info(f"Logging initialized. Log file: {log_file_path}")

class ModelUsageTracker:
    """Track word counts and usage for different models."""
    
    def __init__(self):
        self._counts = {}
        self._lock = None  # For thread safety if needed
    
    def add_words(self, model: str, word_count: int) -> None:
        """Add word count for a specific model."""
        if model not in self._counts:
            self._counts[model] = 0
        self._counts[model] += word_count
    
    def get_count(self, model: str) -> int:
        """Get word count for a specific model."""
        return self._counts.get(model, 0)
    
    def get_total_count(self) -> int:
        """Get total word count across all models."""
        return sum(self._counts.values())
    
    def reset(self) -> None:
        """Reset all counters."""
        self._counts.clear()
    
    def print_summary(self) -> None:
        """Print summary of model usage."""
        logging.info("Model Usage Summary:")
        for model, count in self._counts.items():
            logging.info(f"  {model}: {count:,} words")
        logging.info(f"Total words processed: {self.get_total_count():,}")

# Global instance for tracking model usage
model_usage = ModelUsageTracker() 