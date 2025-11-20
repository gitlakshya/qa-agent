import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from data_pipeline.document_loader import DocumentLoader
from data_pipeline.feature_extractor import FeatureExtractor
from llm.connector import azurellm
from llm.prompt import testGenerationChain
from app.test_case_exporter import TestCaseExporter

logger = logging.getLogger(__name__)


class FeatureDocumentationLoader:
    """Handles loading and processing of feature documentation."""
    
    def __init__(self, feature_docs_dir: str = "Related_docs"):
        """
        Initialize the feature documentation loader.
        
        Args:
            feature_docs_dir: Directory containing feature documentation PDFs
        """
        self.feature_docs_dir = feature_docs_dir
        self.doc_loader = DocumentLoader()
    
    def get_available_features(self) -> List[str]:
        """
        Get list of available feature document names (without .pdf extension).
        
        Returns:
            List of feature document filenames without extension
        """
        try:
            docs_path = Path(self.feature_docs_dir)
            if not docs_path.exists():
                logger.warning(f"Feature docs directory does not exist: {self.feature_docs_dir}")
                return []
            
            # Get all PDF files (excluding subdirectories)
            pdf_files = [f.stem for f in docs_path.glob("*.pdf")]
            logger.info(f"Found {len(pdf_files)} feature documents in {self.feature_docs_dir}")
            
            return sorted(pdf_files)
        except Exception as e:
            logger.error(f"Error scanning feature docs directory: {e}")
            return []
    
    def load_feature_documentation(self, feature_name: str) -> str:
        """
        Load documentation for a specific feature.
        
        Args:
            feature_name: Name of the feature (should match PDF filename without extension)
            
        Returns:
            Documentation content as string
        """
        try:
            file_path = f"{self.feature_docs_dir}/{feature_name}.pdf"
            chunks = self.doc_loader.load_file(file_path)
            documentation = self.doc_loader.join_docs_content(chunks)
            logger.info(f"Loaded documentation for feature: {feature_name}")
            return documentation
        except Exception as e:
            logger.error(f"Failed to load documentation for {feature_name}: {e}")
            raise
    
    def load_multiple_features(self, feature_names: List[str]) -> str:
        """
        Load documentation for multiple features and combine them.
        
        Args:
            feature_names: List of feature names
            
        Returns:
            str: Combined documentation for all features
        """
        if not feature_names:
            return ""
        
        documentations = []
        for feature_name in feature_names:
            try:
                doc = self.load_feature_documentation(feature_name)
                documentations.append(doc)
            except Exception as e:
                logger.warning(f"Skipping {feature_name} due to error: {e}")
                continue
        
        combined_docs = "\n\n---\n\n".join(documentations)
        logger.info(f"Loaded {len(documentations)} feature documentations")
        return combined_docs


class FeatureExtractionService:
    """Handles feature extraction from user stories."""
    
    DEFAULT_PRODUCT_DOC = "Related_docs/Requests_Module_Documentation_v13.0.0.0.pdf"
    
    def __init__(self, product_doc_path: str = None, llm=None, available_features: List[str] = None):
        """
        Initialize the feature extraction service.
        
        Args:
            product_doc_path: Path to the main product documentation
            llm: Language model to use (defaults to azurellm)
            available_features: List of available feature document names
        """
        self.product_doc_path = product_doc_path or self.DEFAULT_PRODUCT_DOC
        self.llm = llm or azurellm
        self.available_features = available_features or []
        self.feature_extractor = FeatureExtractor()
    
    def extract_features(self, user_story: str) -> Dict[str, Any]:
        """
        Extract primary and dependent features from a user story.
        
        Args:
            user_story: The user story text
            
        Returns:
            Dict containing 'feature_name' and 'dependent_features'
            
        Raises:
            ValueError: If extraction fails or returns invalid data
        """
        try:
            logger.info("Extracting features from user story...")
            logger.info(f"Available features: {len(self.available_features)} documents")
            
            response = self.feature_extractor.extract_features(
                user_story, 
                self.product_doc_path, 
                self.llm,
                self.available_features
            )
            
            # Debug: Log the raw response
            logger.info(f"Raw LLM response type: {type(response)}")
            logger.info(f"Raw LLM response: {response}")
            
            if isinstance(response, str):
                extracted_data = json.loads(response)
            else:
                extracted_data = response
            
            # Validate response structure
            if 'feature_name' not in extracted_data:
                raise ValueError("Response missing 'feature_name' field")
            
            logger.info(
                f"Extracted primary feature: {extracted_data['feature_name']}, "
                f"dependent features: {len(extracted_data.get('dependent_features', []))}"
            )
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse feature extraction response: {e}")
            logger.error(f"Response content: {response}")
            
            # Try to extract JSON from the response if it's wrapped in markdown or text
            if isinstance(response, str):
                import re
                # Try to find JSON object in the response
                json_match = re.search(r'\{[^{}]*"feature_name"[^{}]*\}', response, re.DOTALL)
                if json_match:
                    try:
                        extracted_data = json.loads(json_match.group(0))
                        logger.info("Successfully extracted JSON from wrapped response")
                        return extracted_data
                    except:
                        pass
            
            raise ValueError(f"Invalid JSON response from feature extraction: {e}")
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            raise
    
    def get_feature_names(self, user_story: str) -> Tuple[str, List[str]]:
        """
        Extract and return feature names in a convenient format.
        
        Args:
            user_story: The user story text
            
        Returns:
            Tuple of (primary_feature, dependent_features_list)
        """
        extracted_data = self.extract_features(user_story)
        primary_feature = extracted_data['feature_name']
        dependent_features = extracted_data.get('dependent_features', [])
        return primary_feature, dependent_features


class TestCaseGenerator:
    """Generates comprehensive test cases from user stories."""
    
    def __init__(self, llm=None, auto_export: bool = True, 
                 product_doc_path: str = None, feature_docs_dir: str = "Related_docs",
                 project_id: int = None):
        """
        Initialize the test case generator.
        
        Args:
            llm: Language model to use (defaults to azurellm)
            auto_export: If True, automatically export test cases to Excel after generation
            product_doc_path: Path to product documentation
            feature_docs_dir: Directory containing feature documentation PDFs
            project_id: TestRail project ID for metadata
        """
        self.llm = llm or azurellm
        self.doc_loader = FeatureDocumentationLoader(feature_docs_dir)
        
        self.available_features = self.doc_loader.get_available_features()
        logger.info(f"Initialized with {len(self.available_features)} available features")
        
        # Initialize feature extraction service with available features
        self.feature_extraction_service = FeatureExtractionService(
            product_doc_path=product_doc_path,
            llm=self.llm,
            available_features=self.available_features
        )
        
        # Store TestRail project information
        self.project_id = project_id
        
        self.exporter = TestCaseExporter()
        self.auto_export = auto_export
        self.last_export_paths = {}  # Store paths of last exports
    
    def generate_test_cases(
        self, 
        user_story: str,
        auto_export: bool = None
    ) -> List[Dict[str, Any]]:
        """
        Generate comprehensive test cases for a user story.
        
        This method:
        1. Extracts primary and dependent features from the user story
        2. Loads documentation for all identified features
        3. Generates test cases using LLM with full context
        4. Automatically exports to CSV and Excel files
        
        Args:
            user_story: The user story text (should include Jira ID for better filename)
            auto_export: If True, export to CSV and Excel. If None, uses instance setting
            
        Returns:
            List of test case dictionaries with structure:
            {
                "Reference": "TC-001",
                "Type": "Functional|Integration|Negative|...",
                "Title": "Test case title",
                "Precondition": "Preconditions",
                "Steps": ["Step 1", "Step 2", ...],
                "ExpectedResult": "Expected result"
            }
            
        Raises:
            Exception: If test case generation fails
        """
        try:
            logger.info("Starting test case generation process...")
            
            # Step 1: Extract features
            primary_feature, dependent_features = self.feature_extraction_service.get_feature_names(
                user_story
            )
            logger.info(
                f"Identified features - Primary: {primary_feature}, "
                f"Dependent: {dependent_features}"
            )
            
            # Step 2: Load primary feature documentation
            primary_feature_doc = self._load_primary_feature_doc(primary_feature)
            
            # Step 3: Load dependent features documentation
            impacted_features_doc = self._load_impacted_features_doc(dependent_features)
            
            # Step 4: Generate test cases
            test_cases = self._generate_with_llm(
                user_story,
                primary_feature_doc,
                impacted_features_doc
            )
            
            logger.info(f"Successfully generated {len(test_cases)} test cases")
            
            # Step 5: Auto-export to Excel
            should_export = auto_export if auto_export is not None else self.auto_export
            if should_export:
                self.last_export_paths = {}
                
                # Export to Excel with TestRail metadata
                excel_path = self.export_test_cases_to_excel(
                    test_cases,
                    user_story=user_story,
                    project_id=self.project_id
                )
                self.last_export_paths['excel'] = excel_path
                logger.info(f"Excel with metadata exported to: {excel_path}")
            
            return test_cases
            
        except Exception as e:
            logger.error(f"Test case generation failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def _load_primary_feature_doc(self, feature_name: str) -> str:
        """Load documentation for the primary feature."""
        try:
            return self.doc_loader.load_feature_documentation(feature_name)
        except Exception as e:
            logger.error(f"Failed to load primary feature doc: {e}")
            return f"[Documentation for {feature_name} not available]"
    
    def _load_impacted_features_doc(self, feature_names: List[str]) -> str:
        """Load documentation for impacted/dependent features."""
        if not feature_names:
            logger.info("No dependent features identified")
            return "[No dependent features]"
        
        try:
            return self.doc_loader.load_multiple_features(feature_names)
        except Exception as e:
            logger.error(f"Failed to load impacted features docs: {e}")
            return "[Dependent feature documentation not available]"
    
    def _generate_with_llm(
        self,
        user_story: str,
        primary_feature_doc: str,
        impacted_features_doc: str
    ) -> List[Dict[str, Any]]:
        
        try:
            logger.info("Invoking LLM for test case generation...")
            
            # Build the chain
            chain_builder = testGenerationChain()
            chain = chain_builder.build_chain(self.llm)
            
            # Invoke with context
            response = chain.invoke({
                "user_story": user_story,
                "primary_feature_doc": primary_feature_doc,
                "impacted_features_doc": impacted_features_doc
            })
            
            logger.info("Successfully received test cases from LLM")
            
            # Validate response
            if not isinstance(response, list):
                raise ValueError(f"Expected list of test cases, got {type(response)}")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise
    
    def export_test_cases_to_csv(
        self,
        test_cases: List[Dict[str, Any]],
        filename: Optional[str] = None,
        user_story: Optional[str] = None
    ) -> str:
        """
        Export test cases to CSV file.
        
        Args:
            test_cases: List of test case dictionaries
            filename: Custom filename (optional, auto-generated from user story if not provided)
            user_story: Full user story to extract filename from
            
        Returns:
            str: Path to the exported CSV file
            
        Raises:
            Exception: If export fails
        """
        try:
            csv_path = self.exporter.export_to_csv(
                test_cases,
                filename=filename,
                user_story=user_story
            )
            logger.info(f"Exported {len(test_cases)} test cases to {csv_path}")
            return csv_path
        except Exception as e:
            logger.error(f"Failed to export test cases to CSV: {e}")
            raise
    
    def export_test_cases_to_json(
        self,
        test_cases: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Export test cases to JSON file.
        
        Args:
            test_cases: List of test case dictionaries
            filename: Custom filename (optional)
            
        Returns:
            str: Path to the exported JSON file
            
        Raises:
            Exception: If export fails
        """
        try:
            json_path = self.exporter.export_to_json(test_cases, filename=filename)
            logger.info(f"Exported {len(test_cases)} test cases to {json_path}")
            return json_path
        except Exception as e:
            logger.error(f"Failed to export test cases to JSON: {e}")
            raise
    
    def export_test_cases_to_excel(
        self,
        test_cases: List[Dict[str, Any]],
        filename: Optional[str] = None,
        user_story: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> str:
        """
        Export test cases to Excel file with TestRail metadata.
        
        Args:
            test_cases: List of test case dictionaries
            filename: Custom filename (optional, auto-generated from user story if not provided)
            user_story: Full user story to extract filename and section name from
            project_id: TestRail project ID for metadata
            
        Returns:
            str: Path to the exported Excel file
            
        Raises:
            Exception: If export fails
        """
        try:
            # Use new export method with metadata if project info available
            if project_id and user_story:
                excel_path = self.exporter.export_to_excel_with_metadata(
                    test_cases,
                    project_id=project_id,
                    user_story=user_story,
                    filename=filename
                )
            else:
                # Fallback to standard export
                excel_path = self.exporter.export_to_excel(
                    test_cases,
                    filename=filename,
                    user_story=user_story
                )
            
            logger.info(f"Exported {len(test_cases)} test cases to {excel_path}")
            return excel_path
        except Exception as e:
            logger.error(f"Failed to export test cases to Excel: {e}")
            raise


# Backward compatibility aliases (deprecated)
class GenerateTests(TestCaseGenerator):
    """
    Deprecated: Use TestCaseGenerator instead.
    Kept for backward compatibility.
    """
    
    def __init__(self):
        logger.warning(
            "GenerateTests is deprecated. Use TestCaseGenerator instead."
        )
        super().__init__()