"""
Test Case Exporter Module
Handles exporting test cases to CSV and other formats
"""

import csv
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TestCaseExporter:
    """Exports test cases to various formats with configurable output directory."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the exporter.
        
        Args:
            output_dir: Directory where test case files will be saved.
                       If None, reads from OUTPUT_DIR env variable.
                       Defaults to './test_cases_output' if not set.
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        if output_dir is None:
            output_dir = os.getenv('OUTPUT_DIR', './test_cases_output')
        
        self.output_dir = Path(output_dir)
        self.config = self._load_config_from_env()
        self._ensure_output_directory()
        logger.info(f"TestCaseExporter initialized with output directory: {self.output_dir}")
    
    def _load_config_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            'delimiter_map': {
                'comma': ',',
                'semicolon': ';',
                'tab': '\t',
                'pipe': '|'
            },
            'delimiter': os.getenv('CSV_DELIMITER', 'comma'),
            'include_header': os.getenv('CSV_INCLUDE_HEADER', 'true').lower() == 'true',
            'encoding': os.getenv('CSV_ENCODING', 'utf-8-sig'),
        }
    
    def _ensure_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory ensured: {self.output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
            raise
    
    def _extract_filename_from_story(self, user_story: str, max_length: int = 15) -> str:
        """
        Extract a clean filename from user story (first 12-15 chars).
        Prioritizes Jira-like IDs (e.g., MR-2559, PROJ-123).
        
        Args:
            user_story: The user story text
            max_length: Maximum length of extracted filename
            
        Returns:
            Sanitized filename string
        """
        import re
        
        # Try to find Jira-like pattern (e.g., MR-2559, PROJ-123)
        jira_pattern = r'\b([A-Z]+-\d+)\b'
        jira_match = re.search(jira_pattern, user_story)
        
        if jira_match:
            # Found Jira ID, use it as base
            base = jira_match.group(1)
            # Get some additional context (next few words)
            after_jira = user_story[jira_match.end():].strip()
            words = after_jira.split()[:3]  # Take next 3 words
            if words:
                base = f"{base}_{' '.join(words)}"
        else:
            # No Jira ID, use first part of story
            base = user_story.strip()
        
        # Take first max_length characters
        base = base[:max_length]
        
        # Sanitize for filename: keep alphanumeric, hyphens, underscores
        sanitized = re.sub(r'[^\w\s-]', '', base)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        sanitized = sanitized.strip('_')
        
        return sanitized if sanitized else "test_cases"
    
    def _generate_filename(
        self, 
        extension: str = "csv",
        user_story: Optional[str] = None,
        custom_filename: Optional[str] = None
    ) -> str:
        """
        Generate filename from user story or custom name.
        
        Args:
            extension: File extension
            user_story: User story to extract filename from
            custom_filename: Custom filename (overrides extraction)
            
        Returns:
            Generated filename
        """
        if custom_filename:
            # Use custom filename as-is
            if not custom_filename.endswith(f'.{extension}'):
                return f"{custom_filename}.{extension}"
            return custom_filename
        
        if user_story:
            # Extract from user story
            base = self._extract_filename_from_story(user_story)
            return f"{base}.{extension}"
        
        # Fallback to timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"test_cases_{timestamp}.{extension}"
    
    def export_to_csv(
        self, 
        test_cases: List[Dict[str, Any]], 
        filename: Optional[str] = None,
        user_story: Optional[str] = None
    ) -> str:
        """
        Export test cases to CSV file.
        
        Args:
            test_cases: List of test case dictionaries
            filename: Optional custom filename (without path)
            user_story: Full user story text to extract filename from
            
        Returns:
            Full path to the created CSV file as string
            
        Raises:
            ValueError: If no test cases to export
            IOError: If file write fails
        """
        if not test_cases:
            raise ValueError("No test cases to export")
        
        # Generate filename
        csv_filename = self._generate_filename(
            extension="csv",
            user_story=user_story,
            custom_filename=filename
        )
        
        filepath = self.output_dir / csv_filename
        
        # Get delimiter from config
        delimiter_type = self.config.get('delimiter', 'comma')
        delimiter = self.config['delimiter_map'].get(delimiter_type, ',')
        encoding = self.config.get('encoding', 'utf-8-sig')
        include_header = self.config.get('include_header', True)
        
        try:
            # Define CSV columns in order
            fieldnames = [
                "Reference", 
                "Type", 
                "Title", 
                "Precondition", 
                "Steps", 
                "ExpectedResult"
            ]
            
            with open(filepath, 'w', newline='', encoding=encoding) as csvfile:
                writer = csv.DictWriter(
                    csvfile, 
                    fieldnames=fieldnames, 
                    extrasaction='ignore',
                    delimiter=delimiter
                )
                
                if include_header:
                    writer.writeheader()
                
                for test_case in test_cases:
                    # Create a copy to avoid modifying original
                    row = {}
                    
                    for field in fieldnames:
                        value = test_case.get(field, '')
                        
                        # Convert Steps list to pipe-separated string
                        if field == 'Steps' and isinstance(value, list):
                            row[field] = ' | '.join([f"{i+1}. {step}" for i, step in enumerate(value)])
                        else:
                            row[field] = str(value) if value is not None else ''
                    
                    writer.writerow(row)
            
            logger.info(f"Successfully exported {len(test_cases)} test cases to CSV: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            raise IOError(f"CSV export failed: {e}")
    
    def export_to_json(
        self, 
        test_cases: List[Dict[str, Any]], 
        filename: Optional[str] = None,
        user_story: Optional[str] = None,
        include_metadata: bool = True
    ) -> str:
        """
        Export test cases to JSON file.
        
        Args:
            test_cases: List of test case dictionaries
            filename: Optional custom filename
            user_story: Full user story text to extract filename from
            include_metadata: Whether to include export metadata
            
        Returns:
            Full path to the created JSON file as string
        """
        if not test_cases:
            raise ValueError("No test cases to export")
        
        # Generate filename
        json_filename = self._generate_filename(
            extension="json",
            user_story=user_story,
            custom_filename=filename
        )
        
        filepath = self.output_dir / json_filename
        
        try:
            export_data = {
                "test_cases": test_cases
            }
            
            if include_metadata:
                export_data["metadata"] = {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_test_cases": len(test_cases),
                    "test_case_types": self._count_test_types(test_cases)
                }
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully exported {len(test_cases)} test cases to JSON: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            raise IOError(f"JSON export failed: {e}")
    
    def _count_test_types(self, test_cases: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count test cases by type.
        
        Args:
            test_cases: List of test case dictionaries
            
        Returns:
            Dictionary mapping test types to counts
        """
        type_counts = {}
        for test_case in test_cases:
            test_type = test_case.get('Type', 'Unknown')
            type_counts[test_type] = type_counts.get(test_type, 0) + 1
        return type_counts
    
    def export_to_excel(
        self, 
        test_cases: List[Dict[str, Any]], 
        filename: Optional[str] = None,
        user_story: Optional[str] = None
    ) -> str:
        """
        Export test cases to Excel file with formatting.
        
        Args:
            test_cases: List of test case dictionaries
            filename: Optional custom filename
            user_story: Full user story text to extract filename from
            
        Returns:
            Full path to the created Excel file as string
            
        Raises:
            ImportError: If pandas or openpyxl not installed
            ValueError: If no test cases to export
        """
        if not test_cases:
            raise ValueError("No test cases to export")
        
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for Excel export. Install with: pip install pandas openpyxl")
        
        # Generate filename
        excel_filename = self._generate_filename(
            extension="xlsx",
            user_story=user_story,
            custom_filename=filename
        )
        
        filepath = self.output_dir / excel_filename
        
        try:
            # Prepare data for DataFrame
            export_data = []
            for test_case in test_cases:
                row = {
                    'Reference': test_case.get('Reference', ''),
                    'Type': test_case.get('Type', ''),
                    'Title': test_case.get('Title', ''),
                    'Precondition': test_case.get('Precondition', ''),
                    'Steps': '',
                    'ExpectedResult': test_case.get('ExpectedResult', '')
                }
                
                # Format steps
                steps = test_case.get('Steps', [])
                if isinstance(steps, list):
                    row['Steps'] = '\n'.join([f"{i+1}. {step}" for i, step in enumerate(steps)])
                else:
                    row['Steps'] = str(steps)
                
                export_data.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(export_data)
            
            # Export to Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Test Cases')
                
                # Get worksheet for formatting
                worksheet = writer.sheets['Test Cases']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Successfully exported {len(test_cases)} test cases to Excel: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export to Excel: {e}")
            raise IOError(f"Excel export failed: {e}")
    
    def get_latest_export(self, extension: str = "csv") -> Optional[Path]:
        """
        Get the most recently created export file.
        
        Args:
            extension: File extension to search for
            
        Returns:
            Path to latest file or None if no files found
        """
        try:
            files = list(self.output_dir.glob(f"*.{extension}"))
            if not files:
                return None
            return max(files, key=lambda p: p.stat().st_mtime)
        except Exception as e:
            logger.error(f"Failed to get latest export: {e}")
            return None
    
    def list_exports(
        self, 
        extension: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Path]:
        """
        List all exported files, sorted by modification time (newest first).
        
        Args:
            extension: Optional file extension filter
            limit: Optional limit on number of files to return
            
        Returns:
            List of file paths
        """
        try:
            if extension:
                files = list(self.output_dir.glob(f"*.{extension}"))
            else:
                files = [f for f in self.output_dir.iterdir() if f.is_file()]
            
            sorted_files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
            
            if limit:
                return sorted_files[:limit]
            
            return sorted_files
        except Exception as e:
            logger.error(f"Failed to list exports: {e}")
            return []
    
    def get_export_stats(self) -> Dict[str, Any]:
        """
        Get statistics about exported files.
        
        Returns:
            Dictionary with export statistics
        """
        try:
            all_files = list(self.output_dir.iterdir())
            
            stats = {
                "output_directory": str(self.output_dir.absolute()),
                "total_files": len(all_files),
                "csv_files": len(list(self.output_dir.glob("*.csv"))),
                "json_files": len(list(self.output_dir.glob("*.json"))),
                "latest_export": None,
                "oldest_export": None
            }
            
            if all_files:
                sorted_files = sorted(all_files, key=lambda p: p.stat().st_mtime)
                stats["oldest_export"] = {
                    "filename": sorted_files[0].name,
                    "timestamp": datetime.fromtimestamp(sorted_files[0].stat().st_mtime).isoformat()
                }
                stats["latest_export"] = {
                    "filename": sorted_files[-1].name,
                    "timestamp": datetime.fromtimestamp(sorted_files[-1].stat().st_mtime).isoformat()
                }
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get export stats: {e}")
            return {"error": str(e)}
