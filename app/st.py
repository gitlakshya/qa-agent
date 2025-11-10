import streamlit as st
import json
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.generate import TestCaseGenerator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def display_test_cases(test_cases, export_paths=None):
    """
    Display test cases in a formatted manner.
    
    Args:
        test_cases: List of test case dictionaries
        export_paths: Dictionary with 'csv' and 'excel' export paths
    """
    if not test_cases:
        st.warning("No test cases were generated.")
        return
    
    st.success(f"Generated {len(test_cases)} test cases successfully")
    
    # Display export information
    if export_paths:
        st.info("**Exported Files:**")
        col1, col2 = st.columns(2)
        with col1:
            if 'excel' in export_paths:
                st.code(f"Excel: {export_paths['excel']}", language=None)
        with col2:
            if 'csv' in export_paths:
                st.code(f"CSV: {export_paths['csv']}", language=None)
    
    # Display formatted JSON
    st.json(test_cases)



def main():
    """Main application function."""
    
    # Page configuration
    st.set_page_config(
        page_title="Test Case Generator",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("Test Case Generator")
    st.markdown("Generate comprehensive test cases from user stories using AI-powered analysis")
    
    # Sidebar - Document Configuration
    with st.sidebar:
        st.header("Document Configuration")
        
        # Product documentation path
        product_doc_default = "Related_docs/Requests_Module_Documentation_v13.0.0.0.pdf"
        product_doc_path = st.text_input(
            "Product Documentation Path",
            value=product_doc_default,
            help="Path to main product documentation file"
        )
        
        # Feature documentation directory
        feature_docs_default = "Related_docs"
        feature_docs_dir = st.text_input(
            "Feature Documentation Directory",
            value=feature_docs_default,
            help="Directory containing feature-specific documentation"
        )
        
        # Output directory
        output_dir_default = "./test_cases_output"
        output_dir = st.text_input(
            "Output Directory",
            value=output_dir_default,
            help="Directory where test cases will be exported"
        )
        
        # Store in session state
        if 'config' not in st.session_state:
            st.session_state['config'] = {}
        
        st.session_state['config']['product_doc_path'] = product_doc_path
        st.session_state['config']['feature_docs_dir'] = feature_docs_dir
        st.session_state['config']['output_dir'] = output_dir
        
        st.markdown("---")
        st.subheader("Instructions")
        st.markdown("""
        1. Configure document paths above
        2. Enter user story with Jira ID
        3. Click Generate
        4. Test cases auto-export to Excel and CSV
        """)
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            show_logs = st.checkbox("Enable detailed logging", value=False)
            if show_logs:
                logging.getLogger().setLevel(logging.DEBUG)
            else:
                logging.getLogger().setLevel(logging.INFO)
    
    # Main content area
    st.header("User Story Input")
    
    # Instructional placeholder
    placeholder_text = """Example format:

JIRA-ID - [Summary]
[Description
    This is a user story description]"""
    
    # Text area for user story
    story = st.text_area(
        "Enter your user story (include Jira ID for better file naming):",
        height=300,
        placeholder=placeholder_text,
        help="Include Jira ID (e.g., MR-2559) at the beginning for automatic file naming"
    )
    
    # Generate button
    col1, col2, col3 = st.columns([2, 6, 2])
    
    with col1:
        generate_button = st.button("Generate Test Cases", type="primary", use_container_width=True)
    
    # Generate test cases
    if generate_button:
        if not story.strip():
            st.warning("Please enter a user story before generating test cases")
            return
        
        try:
            # Show progress
            with st.spinner("Analyzing user story and generating test cases..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Extracting features...")
                progress_bar.progress(25)
                
                # Initialize generator with auto-export and paths from config
                config = st.session_state.get('config', {})
                generator = TestCaseGenerator(
                    auto_export=True,
                    product_doc_path=config.get('product_doc_path'),
                    feature_docs_dir=config.get('feature_docs_dir', 'Related_docs/MR_features')
                )
                
                status_text.text("Loading documentation...")
                progress_bar.progress(50)
                
                status_text.text("Generating test cases...")
                progress_bar.progress(75)
                
                # Generate test cases (auto-exports)
                result = generator.generate_test_cases(story)
                
                status_text.text("Exporting results...")
                progress_bar.progress(100)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
            
            # Display results with export paths
            if result:
                export_paths = getattr(generator, 'last_export_paths', {})
                display_test_cases(result, export_paths=export_paths)
            else:
                st.warning("No test cases were generated")
                
        except FileNotFoundError as e:
            st.error(f"Documentation Error: {str(e)}")
            st.info("Please verify the document paths in the sidebar configuration")
            logger.error(f"File not found: {e}")
            
        except ValueError as e:
            st.error(f"Validation Error: {str(e)}")
            logger.error(f"Validation error: {e}")
            
        except Exception as e:
            st.error(f"Generation Failed: {str(e)}")
            
            with st.expander("Error Details"):
                st.code(str(e))
                import traceback
                st.code(traceback.format_exc())
            
            logger.error(f"Generation failed: {e}", exc_info=True)
    
    # Footer


if __name__ == "__main__":
    main()
