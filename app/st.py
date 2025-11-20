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


def load_active_projects():
    """
    Load active TestRail projects from projects.json.
    Filters out completed projects and sorts by name.
    
    Returns:
        List of active project dictionaries
    """
    try:
        projects_file = Path(__file__).parent.parent / 'projects.json'
        
        if not projects_file.exists():
            logger.warning(f"projects.json not found at {projects_file}")
            return []
        
        with open(projects_file, 'r') as f:
            data = json.load(f)
        
        # Filter out completed projects
        active_projects = [
            p for p in data.get('projects', []) 
            if not p.get('is_completed', False)
        ]
        
        # Sort by name for easier selection
        active_projects.sort(key=lambda x: x.get('name', ''))
        
        logger.info(f"Loaded {len(active_projects)} active projects")
        return active_projects
        
    except Exception as e:
        logger.error(f"Failed to load projects.json: {e}")
        return []


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
    
    # ===== TestRail Project Selection =====
    st.header("TestRail Project Selection")
    
    # Load projects
    projects = load_active_projects()
    
    if not projects:
        st.error("Unable to load TestRail projects. Please ensure projects.json exists.")
        st.info("Expected location: `projects.json` in the root directory")
        return
    
    # Project selection dropdown
    project_names = [p['name'] for p in projects]
    
    selected_project_name = st.selectbox(
        "Select target TestRail project:",
        options=project_names,
        help="Test cases will be pushed to this project after review"
    )
    
    # Get selected project details
    selected_project = next((p for p in projects if p['name'] == selected_project_name), None)
    
    if selected_project:
        project_id = selected_project['id']
        project_url = selected_project.get('url', '')
        
        # Display project info in an info box
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**Project ID:** `{project_id}` | **Suite Mode:** Single Suite (auto-detected)")
        with col2:
            if project_url:
                st.markdown(f"[View in TestRail ↗]({project_url})")
        
        # Store selected project in session state
        if 'selected_project' not in st.session_state:
            st.session_state['selected_project'] = {}
        
        st.session_state['selected_project']['id'] = project_id
        st.session_state['selected_project']['name'] = selected_project_name
    
    st.markdown("---")
    
    # ===== User Story Input =====
    st.header("User Story Input")
    
    # Instructional placeholder
    placeholder_text = """Example format:

MR-2559 - Verify document management features
As a user, I want to upload and manage documents
so that I can organize my files efficiently.

Acceptance Criteria:
- User can upload documents
- User can view document list
- User can delete documents"""
    
    # Text area for user story
    story = st.text_area(
        "Enter your user story (include Jira ID at the beginning):",
        height=300,
        placeholder=placeholder_text,
        help="Include Jira ID (e.g., MR-2559) at the beginning for section naming and file organization"
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
        
        # Validate project selection
        selected_proj = st.session_state.get('selected_project', {})
        if not selected_proj.get('id'):
            st.error("Please select a TestRail project before generating test cases")
            return
        
        try:
            with st.spinner("Analyzing user story and generating test cases..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Extracting features...")
                progress_bar.progress(25)
                
                # Initialize generator with auto-export, project info, and paths from config
                config = st.session_state.get('config', {})
                generator = TestCaseGenerator(
                    auto_export=True,
                    product_doc_path=config.get('product_doc_path'),
                    feature_docs_dir=config.get('feature_docs_dir', 'Related_docs'),
                    project_id=selected_proj['id']
                )
                
                status_text.text("Loading documentation...")
                progress_bar.progress(50)
                
                status_text.text("Generating test cases...")
                progress_bar.progress(75)
                
                # Generate test cases (auto-exports with project metadata)
                result = generator.generate_test_cases(story)
                
                status_text.text("Exporting to Excel with TestRail metadata...")
                progress_bar.progress(100)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
            
            # Display results with export paths
            if result:
                export_paths = getattr(generator, 'last_export_paths', {})
                
                # Show success message with project info
                st.success(f"Generated {len(result)} test cases for project: **{selected_proj['name']}** (ID: {selected_proj['id']})")
                
                display_test_cases(result, export_paths=export_paths)
                
                # Show next steps
                st.info("""
                **Next Steps:**
                1. Review and edit test cases in the exported Excel file
                2. Move the Excel file to `test_cases_output/reviewed/` folder
                3. Test cases will be automatically pushed to TestRail
                """)
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
