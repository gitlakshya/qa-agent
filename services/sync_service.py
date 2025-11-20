"""
TestRail Synchronization Service
Orchestrates the process of pushing test cases from Excel to TestRail.
"""

import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import time
import gc
from integrations import TestRailClient, TestRailMapper, TestRailConfig

logger = logging.getLogger(__name__)


class TestRailSyncService:
    """
    Manages the synchronization of test cases from Excel files to TestRail.
    Handles section creation, test case creation, and Excel file updates.
    """
    
    def __init__(self, config: Optional[TestRailConfig] = None):
        """
        Initialize the sync service.
        
        Args:
            config: TestRailConfig instance (creates new one if not provided)
        """
        self.config = config or TestRailConfig()
        self.mapper = TestRailMapper()
        logger.info("TestRail Sync Service initialized")
    
    def read_excel_file(self, filepath: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Read Excel file and extract metadata and test cases.
        
        Args:
            filepath: Path to Excel file
            
        Returns:
            Tuple of (metadata_dict, test_cases_list)
            
        Raises:
            ValueError: If Excel file format is invalid
        """
        try:
            # Read both sheets
            excel_file = pd.ExcelFile(filepath)
            
            if 'Metadata' not in excel_file.sheet_names:
                raise ValueError("Excel file missing 'Metadata' sheet")
            if 'Test Cases' not in excel_file.sheet_names:
                raise ValueError("Excel file missing 'Test Cases' sheet")
            
            # Read metadata sheet
            metadata_df = pd.read_excel(filepath, sheet_name='Metadata')
            metadata = {}
            for _, row in metadata_df.iterrows():
                metadata[row['Field']] = row['Value']
            
            # Validate required metadata
            if 'Project_ID' not in metadata:
                raise ValueError("Metadata missing required field: Project_ID")
            if 'Section_Name' not in metadata:
                raise ValueError("Metadata missing required field: Section_Name")
            
            # Read test cases sheet
            test_cases_df = pd.read_excel(filepath, sheet_name='Test Cases')
            
            # Filter out already pushed cases (have TestRail_ID)
            unpushed_cases = test_cases_df[
                test_cases_df['TestRail_ID'].isna() | 
                (test_cases_df['TestRail_ID'] == '')
            ]
            
            # Convert to list of dictionaries
            test_cases = unpushed_cases.to_dict('records')
            
            logger.info(f"Read {len(test_cases)} unpushed test cases from {filepath.name}")
            return metadata, test_cases
            
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            raise
    
    def find_or_create_section(
        self,
        client: TestRailClient,
        project_id: int,
        section_name: str
    ) -> int:
        """
        Find existing section by name or create new one.
        
        Args:
            client: TestRailClient instance
            project_id: TestRail project ID
            section_name: Section name to find or create
            
        Returns:
            Section ID
        """
        try:
            # Get all sections for the project
            sections = client.get_sections(project_id)
            
            # Look for existing section with matching name
            for section in sections:
                if section.get('name') == section_name:
                    logger.info(f"Found existing section: {section_name} (ID: {section['id']})")
                    return section['id']
            
            # Section doesn't exist, create it
            logger.info(f"Section '{section_name}' not found. Creating new section...")
            new_section = client.add_section(
                project_id=project_id,
                name=section_name
            )
            logger.info(f"Created section: {section_name} (ID: {new_section['id']})")
            return new_section['id']
            
        except Exception as e:
            logger.error(f"Failed to find/create section: {e}")
            raise
    
    def push_test_cases(
        self,
        client: TestRailClient,
        section_id: int,
        test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Push test cases to TestRail sequentially.
        
        Args:
            client: TestRailClient instance
            section_id: Section ID to add test cases to
            test_cases: List of test cases from Excel
            
        Returns:
            List of results with status for each test case
        """
        results = []
        total = len(test_cases)
        
        for idx, test_case in enumerate(test_cases, 1):
            result = {
                'row': idx,
                'title': test_case.get('Title', 'Unknown'),
                'status': 'Pending',
                'testrail_id': None,
                'testrail_url': None,
                'error': None
            }
            
            try:
                logger.info(f"[{idx}/{total}] Creating test case: {result['title']}")
                
                # Validate test case
                is_valid, error_msg = self.mapper.validate_excel_test_case(test_case)
                if not is_valid:
                    result['status'] = 'Failed'
                    result['error'] = f"Validation error: {error_msg}"
                    logger.error(result['error'])
                    results.append(result)
                    continue
                
                # Convert to TestRail format
                testrail_case = self.mapper.excel_to_testrail(test_case)
                
                # Create test case in TestRail
                response = client.add_case(section_id=section_id, **testrail_case)
                
                # Extract results
                update_fields = self.mapper.testrail_to_excel_update(
                    response,
                    self.config.url
                )
                
                result['status'] = 'Success'
                result['testrail_id'] = update_fields['TestRail_ID']
                result['testrail_url'] = update_fields['TestRail_URL']
                
                logger.info(f"[{idx}/{total}] ✓ Created case ID: {result['testrail_id']}")
                
            except Exception as e:
                result['status'] = 'Failed'
                result['error'] = str(e)
                logger.error(f"[{idx}/{total}] ✗ Failed: {e}")
            
            results.append(result)
        
        # Summary
        success_count = sum(1 for r in results if r['status'] == 'Success')
        failed_count = sum(1 for r in results if r['status'] == 'Failed')
        logger.info(f"Push complete: {success_count} succeeded, {failed_count} failed")
        
        return results
    
    def update_excel_file(
        self,
        filepath: Path,
        results: List[Dict[str, Any]]
    ):
        """
        Update Excel file with TestRail IDs and push status.
        
        Args:
            filepath: Path to Excel file
            results: List of push results
        """
        try:
            # Read current test cases
            test_cases_df = pd.read_excel(filepath, sheet_name='Test Cases')
            
            # Update rows with results
            for idx, result in enumerate(results):
                if result['status'] == 'Success':
                    test_cases_df.at[idx, 'TestRail_ID'] = result['testrail_id']
                    test_cases_df.at[idx, 'TestRail_URL'] = result['testrail_url']
                    test_cases_df.at[idx, 'Push_Status'] = 'Success'
                    test_cases_df.at[idx, 'Push_Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    test_cases_df.at[idx, 'Error_Message'] = ''
                else:
                    test_cases_df.at[idx, 'Push_Status'] = 'Failed'
                    test_cases_df.at[idx, 'Error_Message'] = result.get('error', 'Unknown error')
            
            # Read metadata sheet (preserve it)
            metadata_df = pd.read_excel(filepath, sheet_name='Metadata')
            
            # Write both sheets back
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                metadata_df.to_excel(writer, index=False, sheet_name='Metadata')
                test_cases_df.to_excel(writer, index=False, sheet_name='Test Cases')
            
            # Force garbage collection to release file handles (Windows file locking issue)
            del metadata_df
            del test_cases_df
            gc.collect()
            
            # Small delay to ensure file handle is released on Windows
            time.sleep(0.5)
            
            logger.info(f"Updated Excel file: {filepath.name}")
            
        except Exception as e:
            logger.error(f"Failed to update Excel file: {e}")
            raise
    
    def sync_file(self, filepath: Path) -> Dict[str, Any]:
        """
        Complete synchronization workflow for a single Excel file.
        
        Args:
            filepath: Path to Excel file (can be string or Path object)
            
        Returns:
            Dictionary with sync results and statistics
        """
        # Convert to Path object if string
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        logger.info(f"Starting sync for: {filepath.name}")
        start_time = datetime.now()
        
        try:
            # Step 1: Read Excel file
            metadata, test_cases = self.read_excel_file(filepath)
            
            if not test_cases:
                logger.info("No unpushed test cases found. Skipping.")
                return {
                    'status': 'success',
                    'message': 'No unpushed test cases (all already synced)',
                    'total': 0,
                    'created': 0,
                    'errors': 0
                }
            
            project_id = int(metadata['Project_ID'])
            section_name = metadata['Section_Name']
            
            # Step 2: Connect to TestRail
            with TestRailClient(self.config) as client:
                # Step 3: Find or create section
                section_id = self.find_or_create_section(
                    client,
                    project_id,
                    section_name
                )
                
                # Step 4: Push test cases
                results = self.push_test_cases(
                    client,
                    section_id,
                    test_cases
                )
            
            # Step 5: Update Excel file
            self.update_excel_file(filepath, results)
            
            # Calculate statistics
            total = len(results)
            succeeded = sum(1 for r in results if r['status'] == 'Success')
            failed = sum(1 for r in results if r['status'] == 'Failed')
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Sync completed in {duration:.1f}s: {succeeded}/{total} succeeded")
            
            return {
                'status': 'success' if failed == 0 else 'partial',
                'message': f'{succeeded} of {total} test cases pushed successfully',
                'total': total,
                'created': succeeded,
                'errors': failed,
                'duration_seconds': duration,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'total': 0,
                'created': 0,
                'errors': 1
            }
