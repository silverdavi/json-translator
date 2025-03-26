"""
Wrapper module for LLM API calls with rate limiting and retry functionality.
Supports OpenAI's Chat Completions API.
"""

import time
import logging
from openai import OpenAI
from typing import List, Dict, Any, Optional, Union
from config import API_CONFIG

# Configure logging
logger = logging.getLogger(__name__)


class LLMApi:
    """Wrapper for OpenAI API with rate limiting and retry logic"""

    def __init__(
            self,
            api_key: Optional[str] = None,
            model: Optional[str] = None,
            min_delay: Optional[float] = None,
            max_retries: Optional[int] = None,
            retry_delay: Optional[int] = None
    ):
        """
        Initialize LLM API wrapper with configurable settings.

        Args:
            api_key: OpenAI API key (optional, defaults to config)
            model: Model to use for completions (optional, defaults to config)
            min_delay: Minimum delay between API calls (optional, defaults to config)
            max_retries: Maximum number of retry attempts (optional, defaults to config)
            retry_delay: Base delay between retries (optional, defaults to config)
        """
        # Get values from config if not provided
        config = API_CONFIG.get("openai", {})
        defaults = config.get("defaults", {})
        
        self.api_key = api_key or config.get("api_key", "")
        if not self.api_key:
            logger.warning("No API key provided! Set OPENAI_API_KEY in your .env file or pass it explicitly.")
            
        self.client = OpenAI(api_key=self.api_key)
        self.model = model or defaults.get("options_model", "o1")
        self.min_delay = min_delay or defaults.get("min_delay", 0.5)
        self.max_retries = max_retries or defaults.get("max_retries", 3)
        self.retry_delay = retry_delay or defaults.get("retry_delay", 1)

        self.last_call_time = 0
        self.call_count = 0
        self.last_response = ""

    def call_model(self, prompt: str) -> str:
        """
        Make API call with a simple string prompt.

        Args:
            prompt: Input prompt for the model as a string

        Returns:
            Model's response text

        Raises:
            Exception: If all retry attempts fail
        """
        messages = [{"role": "user", "content": prompt}]
        return self._make_api_call(messages)

    def call_structured_model(
            self,
            messages: List[Dict[str, str]],
            response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Make API call with structured messages and optional response format.

        Args:
            messages: List of message objects with role and content
            response_format: Optional response format specification (e.g., {"type": "json_object"})

        Returns:
            Model's response text

        Raises:
            Exception: If all retry attempts fail
        """
        return self._make_api_call(messages, response_format)

    def _make_api_call(
            self,
            messages: List[Dict[str, str]],
            response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Internal method to make OpenAI API calls with retry logic and rate limiting.

        Args:
            messages: List of message objects with role and content
            response_format: Optional response format specification

        Returns:
            Model's response text

        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                current_time = time.time()
                if current_time - self.last_call_time < self.min_delay:
                    time.sleep(self.min_delay - (current_time - self.last_call_time))

                self.last_call_time = time.time()
                self.call_count += 1

                # Build the API request arguments
                api_args = {
                    "model": self.model,
                    "messages": messages
                }

                # Add response_format if specified
                if response_format:
                    api_args["response_format"] = response_format

                # Make the API call
                response = self.client.chat.completions.create(**api_args)

                self.last_response = response.choices[0].message.content.strip()
                return self.last_response

            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    error_msg = f"All retry attempts failed: {str(e)}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

    def get_usage_stats(self) -> dict:
        """Return current usage statistics"""
        return {
            "total_calls": self.call_count,
            "last_call_time": self.last_call_time,
            "last_response_length": len(self.last_response)
        }