"""
Test and demonstration of the semantic chunker module.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.semantic_chunker import SemanticChunker, HeadingBasedChunker
import logging

logging.basicConfig(level=logging.INFO)

def test_semantic_chunking():
    """Test semantic chunking on a PDF file."""
    
    # Initialize the chunker
    chunker = SemanticChunker(
        min_heading_font_size=12.0,
        font_size_threshold=1.2,
        max_chunk_size=4000,
        include_page_numbers=True
    )
    
    # Path to a PDF file
    file_path = r'MR-releaseNotes\ManageRequests-ReleaseNotes_Q1-2024.pdf'
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    try:
        # Chunk the PDF
        print(f"\n{'='*60}")
        print(f"Testing Semantic Chunking on: {file_path}")
        print(f"{'='*60}\n")
        
        chunks = chunker.chunk_pdf(file_path)
        
        print(f"Total chunks created: {len(chunks)}\n")
        
        # Display first few chunks
        for i, chunk in enumerate(chunks[:5]):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Headings: {chunk.metadata.get('headings', [])}")
            print(f"Heading Level: {chunk.metadata.get('heading_level', 'N/A')}")
            print(f"Pages: {chunk.metadata.get('pages', [])}")
            print(f"Content Length: {len(chunk.page_content)} characters")
            print(f"Content Preview (first 200 chars):")
            print(chunk.page_content[:200])
            print("...")
        
        if len(chunks) > 5:
            print(f"\n... and {len(chunks) - 5} more chunks")
        
        return chunks
        
    except Exception as e:
        print(f"Error during semantic chunking: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_toc_chunking():
    """Test TOC-based chunking on a PDF with table of contents."""
    
    chunker = HeadingBasedChunker(max_chunk_size=4000)
    
    file_path = r'MR-releaseNotes\ManageRequests-ReleaseNotes_Q1-2024.pdf'
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    try:
        print(f"\n{'='*60}")
        print(f"Testing TOC-based Chunking on: {file_path}")
        print(f"{'='*60}\n")
        
        chunks = chunker.chunk_pdf_by_toc(file_path)
        
        print(f"Total chunks created: {len(chunks)}\n")
        
        # Display all TOC entries
        for i, chunk in enumerate(chunks):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Heading: {chunk.metadata.get('heading', 'N/A')}")
            print(f"Level: {chunk.metadata.get('heading_level', 'N/A')}")
            print(f"Pages: {chunk.metadata.get('page_range', 'N/A')}")
            print(f"Content Length: {len(chunk.page_content)} characters")
        
        return chunks
        
    except ValueError as e:
        print(f"TOC not available: {e}")
        return None
    except Exception as e:
        print(f"Error during TOC chunking: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_fallback_chunking():
    """Test fallback mechanism when semantic chunking fails."""
    
    chunker = SemanticChunker()
    
    file_path = r'MR-releaseNotes\ManageRequests-ReleaseNotes_Q1-2024.pdf'
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    try:
        print(f"\n{'='*60}")
        print(f"Testing Fallback Chunking on: {file_path}")
        print(f"{'='*60}\n")
        
        chunks = chunker.chunk_with_fallback(
            file_path,
            fallback_chunk_size=1000,
            fallback_chunk_overlap=200
        )
        
        print(f"Total chunks created: {len(chunks)}")
        print(f"Chunk type: {chunks[0].metadata.get('chunk_type', 'unknown')}\n")
        
        # Display first chunk
        print("--- First Chunk ---")
        print(f"Content Length: {len(chunks[0].page_content)} characters")
        print(f"Metadata: {chunks[0].metadata}")
        
        return chunks
        
    except Exception as e:
        print(f"Error during fallback chunking: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_chunking_methods():
    """Compare different chunking methods."""
    
    file_path = r'MR-releaseNotes\ManageRequests-ReleaseNotes_Q1-2024.pdf'
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"Comparing Chunking Methods")
    print(f"{'='*60}\n")
    
    # Method 1: Semantic chunking
    try:
        chunker1 = SemanticChunker()
        chunks1 = chunker1.chunk_pdf(file_path)
        print(f"Semantic Chunking: {len(chunks1)} chunks")
    except Exception as e:
        print(f"Semantic Chunking failed: {e}")
        chunks1 = []
    
    # Method 2: TOC-based chunking
    try:
        chunker2 = HeadingBasedChunker()
        chunks2 = chunker2.chunk_pdf_by_toc(file_path)
        print(f"TOC-based Chunking: {len(chunks2)} chunks")
    except Exception as e:
        print(f"TOC-based Chunking failed: {e}")
        chunks2 = []
    
    # Method 3: Traditional character-based
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks3 = splitter.split_documents(docs)
        print(f"Character-based Chunking: {len(chunks3)} chunks")
    except Exception as e:
        print(f"Character-based Chunking failed: {e}")
        chunks3 = []
    
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Semantic: {len(chunks1)} chunks (structure-aware)")
    print(f"  TOC-based: {len(chunks2)} chunks (uses document outline)")
    print(f"  Character-based: {len(chunks3)} chunks (fixed-size)")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("\nSemantic Chunker Test Suite")
    print("=" * 60)
    
    # Check if PyMuPDF is installed
    try:
        import fitz
        print("✓ PyMuPDF (fitz) is installed\n")
    except ImportError:
        print("✗ PyMuPDF is NOT installed")
        print("  Install with: pip install PyMuPDF\n")
        sys.exit(1)
    
    # Run tests
    print("\n1. Testing Semantic Chunking")
    print("-" * 60)
    semantic_chunks = test_semantic_chunking()
    
    print("\n\n2. Testing TOC-based Chunking")
    print("-" * 60)
    toc_chunks = test_toc_chunking()
    
    print("\n\n3. Testing Fallback Mechanism")
    print("-" * 60)
    fallback_chunks = test_fallback_chunking()
    
    print("\n\n4. Comparing Methods")
    print("-" * 60)
    compare_chunking_methods()
    
    print("\n\nAll tests completed!")
