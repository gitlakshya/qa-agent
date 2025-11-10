"""
Example: Integrating Semantic Chunker with Existing QA Agent Pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.semantic_chunker import SemanticChunker
from data_pipeline.feature_extractor import FeatureExtractor
from llm.connector import azurellm
import logging

logging.basicConfig(level=logging.INFO)


# ============================================================================
# Example 1: Enhanced Feature Extraction with Semantic Chunks
# ============================================================================

def extract_features_with_semantic_chunking(user_story, pdf_path):
    """
    Enhanced version of feature extraction using semantic chunking.
    This provides better context to the LLM by maintaining document structure.
    """
    print("="*70)
    print("Example 1: Feature Extraction with Semantic Chunking")
    print("="*70)
    
    # Use semantic chunking to load the document
    chunker = SemanticChunker(
        min_heading_font_size=12.0,
        font_size_threshold=1.2,
        max_chunk_size=4000
    )
    
    try:
        # Get semantic chunks
        chunks = chunker.chunk_with_fallback(pdf_path)
        print(f"\n✓ Loaded {len(chunks)} semantic chunks")
        
        # Display chunk structure
        print("\nDocument Structure:")
        for i, chunk in enumerate(chunks[:5], 1):
            headings = chunk.metadata.get('headings', [])
            if headings:
                print(f"  {i}. {' > '.join(headings)}")
        
        if len(chunks) > 5:
            print(f"  ... and {len(chunks)-5} more sections")
        
        # Join chunks for feature extraction (or use specific sections)
        product_documentation = "\n\n".join([c.page_content for c in chunks])
        
        # Now use with existing feature extractor
        from llm.prompt import FeatureExtractionChain
        feature_chain = FeatureExtractionChain()
        chain = feature_chain.build_chain(azurellm)
        
        print("\n✓ Extracting features...")
        response = chain.invoke({
            "user_story": user_story,
            "product_documentation": product_documentation
        })
        
        print("\nExtracted Features:")
        print(f"  Primary: {response.get('feature_name', 'N/A')}")
        print(f"  Dependent: {response.get('dependent_features', [])}")
        
        return response
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# Example 2: Selective Context Loading (More Efficient)
# ============================================================================

def extract_features_with_selective_context(user_story, pdf_path, keywords):
    """
    Load only relevant sections of documentation based on keywords.
    This is more efficient and provides focused context to the LLM.
    """
    print("\n" + "="*70)
    print("Example 2: Selective Context Loading")
    print("="*70)
    
    chunker = SemanticChunker()
    
    try:
        chunks = chunker.chunk_with_fallback(pdf_path)
        print(f"\n✓ Loaded {len(chunks)} chunks")
        
        # Filter chunks by keywords
        relevant_chunks = []
        for chunk in chunks:
            # Check if any keyword appears in headings or content
            headings_text = ' '.join(chunk.metadata.get('headings', [])).lower()
            content_text = chunk.page_content.lower()
            
            if any(keyword.lower() in headings_text or 
                   keyword.lower() in content_text for keyword in keywords):
                relevant_chunks.append(chunk)
        
        print(f"✓ Found {len(relevant_chunks)} relevant chunks based on keywords: {keywords}")
        
        if relevant_chunks:
            print("\nRelevant Sections:")
            for chunk in relevant_chunks:
                headings = chunk.metadata.get('headings', ['No heading'])
                print(f"  - {' > '.join(headings)}")
            
            # Use only relevant chunks
            focused_documentation = "\n\n".join([c.page_content for c in relevant_chunks])
            
            from llm.prompt import FeatureExtractionChain
            feature_chain = FeatureExtractionChain()
            chain = feature_chain.build_chain(azurellm)
            
            print("\n✓ Extracting features from relevant sections...")
            response = chain.invoke({
                "user_story": user_story,
                "product_documentation": focused_documentation
            })
            
            print("\nExtracted Features:")
            print(f"  Primary: {response.get('feature_name', 'N/A')}")
            print(f"  Dependent: {response.get('dependent_features', [])}")
            
            return response
        else:
            print("✗ No relevant sections found")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


# ============================================================================
# Example 3: Enhanced Document Loader Class
# ============================================================================

from data_pipeline.document_loader import DocumentLoader

class SemanticDocumentLoader(DocumentLoader):
    """
    Extended DocumentLoader that uses semantic chunking for PDFs.
    Drop-in replacement for the existing DocumentLoader.
    """
    
    def __init__(self, use_semantic_chunking=True, semantic_config=None):
        super().__init__()
        self.use_semantic_chunking = use_semantic_chunking
        
        if use_semantic_chunking:
            config = semantic_config or {}
            self.semantic_chunker = SemanticChunker(
                min_heading_font_size=config.get('min_heading_font_size', 12.0),
                font_size_threshold=config.get('font_size_threshold', 1.2),
                max_chunk_size=config.get('max_chunk_size', 4000),
                include_page_numbers=config.get('include_page_numbers', True)
            )
    
    def load_file(self, file_path: str):
        """Override to use semantic chunking for PDFs."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf' and self.use_semantic_chunking:
            # Use semantic chunking with fallback
            return self.semantic_chunker.chunk_with_fallback(file_path)
        else:
            # Use original method for other files
            return super().load_file(file_path)


def test_enhanced_document_loader():
    """Test the enhanced document loader."""
    print("\n" + "="*70)
    print("Example 3: Enhanced Document Loader")
    print("="*70)
    
    # Create loader with semantic chunking
    loader = SemanticDocumentLoader(
        use_semantic_chunking=True,
        semantic_config={
            'min_heading_font_size': 11.0,
            'font_size_threshold': 1.3,
            'max_chunk_size': 3000
        }
    )
    
    # Load a PDF (automatically uses semantic chunking)
    pdf_path = r'Related_docs\Feature_Request_Creation.pdf'
    
    if os.path.exists(pdf_path):
        chunks = loader.load_file(pdf_path)
        print(f"\n✓ Loaded {len(chunks)} chunks")
        
        # Check chunk type
        chunk_type = chunks[0].metadata.get('chunk_type', 'unknown')
        print(f"✓ Chunk type: {chunk_type}")
        
        # Show structure
        print("\nDocument Structure (first 5):")
        for i, chunk in enumerate(chunks[:5], 1):
            headings = chunk.metadata.get('headings', ['No heading'])
            level = chunk.metadata.get('heading_level', 'N/A')
            print(f"  {i}. [L{level}] {' > '.join(headings)}")
        
        return chunks
    else:
        print(f"✗ File not found: {pdf_path}")
        return None


# ============================================================================
# Example 4: Building a Vector Store with Semantic Chunks
# ============================================================================

def build_vectorstore_with_semantic_chunks():
    """
    Build a vector store using semantic chunks for better retrieval.
    """
    print("\n" + "="*70)
    print("Example 4: Vector Store with Semantic Chunks")
    print("="*70)
    
    try:
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import OpenAIEmbeddings
    except ImportError:
        print("✗ Need chromadb and openai packages")
        return None
    
    # Load documents with semantic chunking
    chunker = SemanticChunker()
    
    # Load multiple documents
    doc_paths = [
        r'Related_docs\Feature_Request_Creation.pdf',
        r'Related_docs\Feature_Dashboards_All_Requests_and_My_Requests.pdf',
    ]
    
    all_chunks = []
    for doc_path in doc_paths:
        if os.path.exists(doc_path):
            print(f"\n✓ Processing: {os.path.basename(doc_path)}")
            try:
                chunks = chunker.chunk_with_fallback(doc_path)
                all_chunks.extend(chunks)
                print(f"  Added {len(chunks)} chunks")
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    if all_chunks:
        print(f"\n✓ Total chunks: {len(all_chunks)}")
        print("\nChunk Statistics:")
        print(f"  Semantic: {sum(1 for c in all_chunks if c.metadata.get('chunk_type') == 'semantic')}")
        print(f"  Fallback: {sum(1 for c in all_chunks if 'fallback' in c.metadata.get('chunk_type', ''))}")
        
        # Note: Uncomment below to actually create vectorstore
        # vectorstore = Chroma.from_documents(
        #     documents=all_chunks,
        #     embedding=OpenAIEmbeddings(),
        #     collection_name="semantic_features"
        # )
        # print("\n✓ Vector store created!")
        
        return all_chunks
    else:
        print("✗ No chunks loaded")
        return None


# ============================================================================
# Main Test Runner
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Semantic Chunker Integration Examples")
    print("="*70)
    
    # Test data
    user_story = """MR-2559

Comments - Add title for each thread

Description

User story

As a lawyer, I want to add a title for each conversation so that I can easily 
organise comments around a common topic/subject and find them.

Acceptance Criteria:

When I'm creating a new thread, I should have an option to add

Title: This is an optional field (Max limit of title is 2k chars)

Description: Text field with upto 63k char limit"""
    
    pdf_path = r'Related_docs\Feature_Request_Creation.pdf'
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"\n✗ Error: File not found: {pdf_path}")
        print("Please update the pdf_path variable with a valid PDF file.")
        sys.exit(1)
    
    # Run examples
    print("\nRunning examples...\n")
    
    # Example 1: Basic integration
    # result1 = extract_features_with_semantic_chunking(user_story, pdf_path)
    
    # Example 2: Selective context
    keywords = ["comment", "thread", "conversation", "dashboard"]
    # result2 = extract_features_with_selective_context(user_story, pdf_path, keywords)
    
    # Example 3: Enhanced loader
    result3 = test_enhanced_document_loader()
    
    # Example 4: Vector store
    # result4 = build_vectorstore_with_semantic_chunks()
    
    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)
    print("\nNote: Some examples are commented out to avoid requiring")
    print("Azure OpenAI credentials. Uncomment them to test fully.")
