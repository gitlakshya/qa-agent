"""
TestRail Configuration Loader
Loads and validates TestRail connection settings from environment variables.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class TestRailConfig:
    """Manages TestRail configuration from environment variables."""
    
    def __init__(self):
        """Initialize configuration from .env file."""
        load_dotenv()
        self._config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load TestRail configuration from environment variables.
        
        Returns:
            Dictionary with configuration values
        """
        config = {
            'url': os.getenv('TESTRAIL_URL', '').rstrip('/'),
            'username': os.getenv('TESTRAIL_USERNAME', ''),
            'api_key': os.getenv('TESTRAIL_API_KEY', ''),
            'timeout': int(os.getenv('TESTRAIL_TIMEOUT', '30')),
            'retry_attempts': int(os.getenv('TESTRAIL_RETRY_ATTEMPTS', '3')),
            'retry_delay': float(os.getenv('TESTRAIL_RETRY_DELAY', '1.0')),
            'rate_limit_delay': float(os.getenv('TESTRAIL_RATE_LIMIT_DELAY', '0.4'))
        }
        
        logger.info(f"Loaded TestRail configuration for: {config['url']}")
        return config
    
    def _validate_config(self):
        """
        Validate required configuration values.
        
        Raises:
            ValueError: If required configuration is missing
        """
        required_fields = ['url', 'username', 'api_key']
        missing_fields = [field for field in required_fields if not self._config.get(field)]
        
        if missing_fields:
            raise ValueError(
                f"Missing required TestRail configuration: {', '.join(missing_fields)}. "
                f"Please check your .env file."
            )
        
        if not self._config['url'].startswith('https://'):
            raise ValueError(f"Invalid TestRail URL: {self._config['url']}. Must start with https://")
        
        logger.info("TestRail configuration validated successfully")
    
    @property
    def url(self) -> str:
        """Get TestRail base URL."""
        return self._config['url']
    
    @property
    def username(self) -> str:
        """Get TestRail username."""
        return self._config['username']
    
    @property
    def api_key(self) -> str:
        """Get TestRail API key."""
        return self._config['api_key']
    
    @property
    def timeout(self) -> int:
        """Get request timeout in seconds."""
        return self._config['timeout']
    
    @property
    def retry_attempts(self) -> int:
        """Get number of retry attempts for failed requests."""
        return self._config['retry_attempts']
    
    @property
    def retry_delay(self) -> float:
        """Get delay between retries in seconds."""
        return self._config['retry_delay']
    
    @property
    def rate_limit_delay(self) -> float:
        """Get delay between requests to avoid rate limiting (seconds)."""
        return self._config['rate_limit_delay']
    
    def get_auth(self) -> tuple:
        """
        Get authentication credentials for requests.
        
        Returns:
            Tuple of (username, api_key) for Basic Auth
        """
        return (self.username, self.api_key)
    
    def __repr__(self) -> str:
        """String representation (excluding sensitive data)."""
        return f"TestRailConfig(url={self.url}, username={self.username})"
