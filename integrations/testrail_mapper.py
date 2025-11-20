"""
TestRail Data Mapper
Converts between Excel format and TestRail API format.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TestRailMapper:
    """
    Maps data between Excel test case format and TestRail API format.
    Handles field name conversions and data transformations.
    """
    
    # Field mapping: Excel column -> TestRail API field
    FIELD_MAPPING = {
        'Title': 'title',
        'Precondition': 'custom_preconds',
        'Steps': 'custom_steps',
        'ExpectedResult': 'custom_expected',
        'Reference': 'refs',
        'Type': 'type_name'  # Will be converted to type_id
    }
    
    # TestRail case type name to ID mapping (standard types)
    TYPE_MAPPING = {
        'Acceptance': 1,
        'Accessability': 2,
        'Automated': 3,
        'Compatibility': 4,
        'Destructive': 5,
        'Functional': 6,
        'Other': 7,
        'Performance': 8,
        'Regression': 9,
        'Security': 10,
        'Smoke & Sanity': 11,
        'Usability': 12
    }
    
    @staticmethod
    def excel_to_testrail(test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Excel test case format to TestRail API format.
        
        Args:
            test_case: Test case dictionary from Excel
                Expected keys: Title, Precondition, Steps, ExpectedResult, Type, Reference
                
        Returns:
            Dictionary formatted for TestRail add_case API
            
        Example:
            Input:
                {
                    'Title': 'Test login',
                    'Precondition': 'User on login page',
                    'Steps': 'Enter credentials\nClick login',
                    'ExpectedResult': 'User logged in',
                    'Type': 'Functional',
                    'Reference': 'REQ-123'
                }
            Output:
                {
                    'title': 'Test login',
                    'custom_preconds': 'User on login page',
                    'custom_steps': 'Enter credentials\nClick login',
                    'custom_expected': 'User logged in',
                    'type_id': 1,
                    'refs': 'REQ-123'
                }
        """
        testrail_case = {}
        
        # Map title (required)
        if 'Title' in test_case and test_case['Title']:
            testrail_case['title'] = str(test_case['Title']).strip()
        else:
            raise ValueError("Test case missing required field: Title")
        
        # Map preconditions
        if 'Precondition' in test_case and test_case['Precondition']:
            testrail_case['custom_preconds'] = str(test_case['Precondition']).strip()
        
        # Map steps
        if 'Steps' in test_case and test_case['Steps']:
            steps = test_case['Steps']
            # Handle both string and list formats
            if isinstance(steps, list):
                testrail_case['custom_steps'] = '\n'.join(str(step).strip() for step in steps if step)
            else:
                testrail_case['custom_steps'] = str(steps).strip()
        
        # Map expected result
        if 'ExpectedResult' in test_case and test_case['ExpectedResult']:
            testrail_case['custom_expected'] = str(test_case['ExpectedResult']).strip()
        
        # Map test type
        if 'Type' in test_case and test_case['Type']:
            type_name = str(test_case['Type']).strip()
            type_id = TestRailMapper.TYPE_MAPPING.get(type_name)
            if type_id:
                testrail_case['type_id'] = type_id
            else:
                logger.warning(f"Unknown test case type: {type_name}. Using default.")
                testrail_case['type_id'] = 6  # Default to Functional
        
        # Map reference
        if 'Reference' in test_case and test_case['Reference']:
            testrail_case['refs'] = str(test_case['Reference']).strip()
        
        logger.debug(f"Mapped Excel case to TestRail: {testrail_case.get('title', 'Unknown')}")
        return testrail_case
    
    @staticmethod
    def testrail_to_excel_update(testrail_response: Dict[str, Any], base_url: str) -> Dict[str, Any]:
        """
        Convert TestRail API response to Excel update fields.
        Extracts TestRail ID and URL from the response to update Excel.
        
        Args:
            testrail_response: Response from add_case API call
            base_url: TestRail base URL (e.g., https://elevate.testrail.com)
            
        Returns:
            Dictionary with Excel update fields:
                - TestRail_ID
                - TestRail_URL
                - Push_Status
                
        Example:
            Input:
                {
                    'id': 12345,
                    'title': 'Test login',
                    ...
                }
            Output:
                {
                    'TestRail_ID': 12345,
                    'TestRail_URL': 'https://elevate.testrail.com/index.php?/cases/view/12345',
                    'Push_Status': 'Success'
                }
        """
        case_id = testrail_response.get('id')
        if not case_id:
            raise ValueError("TestRail response missing 'id' field")
        
        return {
            'TestRail_ID': case_id,
            'TestRail_URL': f"{base_url}/index.php?/cases/view/{case_id}",
            'Push_Status': 'Success'
        }
    
    @staticmethod
    def batch_excel_to_testrail(test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert multiple Excel test cases to TestRail format.
        
        Args:
            test_cases: List of test case dictionaries from Excel
            
        Returns:
            List of test cases formatted for TestRail API
        """
        testrail_cases = []
        errors = []
        
        for idx, test_case in enumerate(test_cases):
            try:
                testrail_case = TestRailMapper.excel_to_testrail(test_case)
                testrail_cases.append(testrail_case)
            except Exception as e:
                error_msg = f"Row {idx + 2}: {str(e)}"  # +2 for header row and 0-index
                errors.append(error_msg)
                logger.error(error_msg)
        
        if errors:
            logger.warning(f"Mapped {len(testrail_cases)} cases with {len(errors)} errors")
        else:
            logger.info(f"Successfully mapped {len(testrail_cases)} test cases")
        
        return testrail_cases
    
    @staticmethod
    def validate_excel_test_case(test_case: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate an Excel test case has required fields.
        
        Args:
            test_case: Test case dictionary from Excel
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for required fields
        if 'Title' not in test_case or not test_case['Title']:
            return False, "Missing required field: Title"
        
        # Check title is not empty after stripping
        if not str(test_case['Title']).strip():
            return False, "Title cannot be empty"
        
        # Warn if missing recommended fields (not errors)
        warnings = []
        if 'Steps' not in test_case or not test_case['Steps']:
            warnings.append("Missing recommended field: Steps")
        if 'ExpectedResult' not in test_case or not test_case['ExpectedResult']:
            warnings.append("Missing recommended field: ExpectedResult")
        
        if warnings:
            logger.warning(f"Test case '{test_case['Title']}': {'; '.join(warnings)}")
        
        return True, None
    
    @staticmethod
    def get_section_name_from_filename(filename: str) -> str:
        """
        Extract section name from Excel filename.
        Removes .xlsx extension.
        
        Args:
            filename: Excel filename (e.g., "MR_2559_Verify_document.xlsx")
            
        Returns:
            Section name (e.g., "MR_2559_Verify_document")
        """
        return filename.replace('.xlsx', '').replace('.xls', '')
