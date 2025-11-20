"""
TestRail API Client
Handles all HTTP interactions with TestRail API v2.
"""

import requests
import logging
import time
from typing import Dict, Any, Optional, List
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class TestRailAPIException(Exception):
    """Exception raised for TestRail API errors."""
    pass


class TestRailRateLimitException(Exception):
    """Exception raised when hitting TestRail API rate limits."""
    pass


class TestRailClient:
    """
    TestRail API v2 client with retry logic and rate limit handling.
    Supports sequential test case creation with proper error handling.
    """
    
    def __init__(self, config):
        """
        Initialize TestRail client.
        
        Args:
            config: TestRailConfig instance with connection settings
        """
        self.config = config
        self.base_url = f"{config.url}/index.php?/api/v2"
        self.auth = HTTPBasicAuth(config.username, config.api_key)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({'Content-Type': 'application/json'})
        
        logger.info(f"TestRail client initialized for: {config.url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to TestRail API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: JSON payload for POST requests
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            TestRailAPIException: For API errors
            TestRailRateLimitException: For rate limit errors (429)
        """
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.config.retry_attempts):
            try:
                logger.debug(f"API Request: {method} {endpoint} (attempt {attempt + 1})")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=self.config.timeout
                )
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit hit (429). Retrying after {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Handle success (200-299)
                if 200 <= response.status_code < 300:
                    # Add small delay to avoid rate limiting
                    time.sleep(self.config.rate_limit_delay)
                    return response.json() if response.content else {}
                
                # Handle client/server errors
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                
                # Don't retry on client errors (400-499 except 429)
                if 400 <= response.status_code < 500:
                    raise TestRailAPIException(error_msg)
                
                # Retry on server errors (500+)
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise TestRailAPIException(error_msg)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise TestRailAPIException(f"Request failed after {self.config.retry_attempts} attempts: {e}")
        
        raise TestRailAPIException("Maximum retry attempts reached")
    
    def get_project(self, project_id: int) -> Dict[str, Any]:
        """
        Get project details.
        
        Args:
            project_id: TestRail project ID
            
        Returns:
            Project details dictionary
        """
        logger.info(f"Fetching project: {project_id}")
        return self._make_request('GET', f'get_project/{project_id}')
    
    def get_sections(self, project_id: int, suite_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get sections for a project.
        
        Args:
            project_id: TestRail project ID
            suite_id: Optional suite ID (for multi-suite projects)
            
        Returns:
            List of section dictionaries
        """
        endpoint = f'get_sections/{project_id}'
        params = {'suite_id': suite_id} if suite_id else None
        
        logger.info(f"Fetching sections for project {project_id}")
        response = self._make_request('GET', endpoint, params=params)
        
        # Response can be a dict with 'sections' key or direct list
        if isinstance(response, dict) and 'sections' in response:
            return response['sections']
        return response if isinstance(response, list) else []
    
    def add_section(self, project_id: int, name: str, suite_id: Optional[int] = None, 
                   parent_id: Optional[int] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new section.
        
        Args:
            project_id: TestRail project ID
            name: Section name
            suite_id: Optional suite ID (required for multi-suite projects)
            parent_id: Optional parent section ID (for nested sections)
            description: Optional section description
            
        Returns:
            Created section details
        """
        data = {'name': name}
        if suite_id:
            data['suite_id'] = suite_id
        if parent_id:
            data['parent_id'] = parent_id
        if description:
            data['description'] = description
        
        logger.info(f"Creating section '{name}' in project {project_id}")
        return self._make_request('POST', f'add_section/{project_id}', data=data)
    
    def add_case(self, section_id: int, title: str, 
                custom_preconds: Optional[str] = None,
                custom_steps: Optional[str] = None,
                custom_expected: Optional[str] = None,
                type_id: Optional[int] = None,
                priority_id: Optional[int] = None,
                refs: Optional[str] = None,
                **custom_fields) -> Dict[str, Any]:
        """
        Create a new test case.
        
        Args:
            section_id: Section ID where test case will be created
            title: Test case title
            custom_preconds: Preconditions (maps to custom_preconds field)
            custom_steps: Test steps (maps to custom_steps field)
            custom_expected: Expected result (maps to custom_expected field)
            type_id: Test case type ID (optional)
            priority_id: Priority ID (optional)
            refs: References/requirements (optional)
            **custom_fields: Additional custom fields
            
        Returns:
            Created test case details including case ID
        """
        data = {'title': title}
        
        # Add custom fields
        if custom_preconds:
            data['custom_preconds'] = custom_preconds
        if custom_steps:
            data['custom_steps'] = custom_steps
        if custom_expected:
            data['custom_expected'] = custom_expected
        if type_id:
            data['type_id'] = type_id
        if priority_id:
            data['priority_id'] = priority_id
        if refs:
            data['refs'] = refs
        
        # Add any additional custom fields
        data.update(custom_fields)
        
        logger.info(f"Creating test case '{title}' in section {section_id}")
        return self._make_request('POST', f'add_case/{section_id}', data=data)
    
    def get_case(self, case_id: int) -> Dict[str, Any]:
        """
        Get test case details.
        
        Args:
            case_id: Test case ID
            
        Returns:
            Test case details
        """
        logger.info(f"Fetching test case: {case_id}")
        return self._make_request('GET', f'get_case/{case_id}')
    
    def update_case(self, case_id: int, **fields) -> Dict[str, Any]:
        """
        Update an existing test case.
        
        Args:
            case_id: Test case ID to update
            **fields: Fields to update (title, custom_preconds, etc.)
            
        Returns:
            Updated test case details
        """
        logger.info(f"Updating test case: {case_id}")
        return self._make_request('POST', f'update_case/{case_id}', data=fields)
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.info("TestRail client session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
