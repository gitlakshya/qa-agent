"""Semantic chunker for PDF documents based on headings and subheadings."""

import os
import logging
from typing import List, Dict
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Chunks PDF documents based on document structure (headings/subheadings).
    Uses font size, style, and formatting to identify hierarchical structure.
    """
    
    def __init__(
        self, 
        min_heading_font_size: float = 12.0,
        font_size_threshold: float = 1.5,
        max_chunk_size: int = 4000,
        include_page_numbers: bool = True
    ):
        """
        Initialize the semantic chunker.
        
        Args:
            min_heading_font_size: Minimum font size to consider as heading
            font_size_threshold: Multiplier to determine heading vs body text
            max_chunk_size: Maximum characters per chunk (will split if exceeded)
            include_page_numbers: Whether to include page numbers in metadata
        """
        self.min_heading_font_size = min_heading_font_size
        self.font_size_threshold = font_size_threshold
        self.max_chunk_size = max_chunk_size
        self.include_page_numbers = include_page_numbers
        
        try:
            import fitz  # PyMuPDF
            self.fitz = fitz
            self.available = True
        except ImportError:
            logger.warning(
                "PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF"
            )
            self.available = False
    
    def chunk_pdf(self, file_path: str) -> List[Document]:
        """
        Chunk a PDF document based on its heading structure.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of Document objects with semantic chunks
            
        Raises:
            ImportError: If PyMuPDF is not installed
            FileNotFoundError: If file doesn't exist
        """
        if not self.available:
            raise ImportError(
                "PyMuPDF is required for semantic chunking. "
                "Install with: pip install PyMuPDF"
            )
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            doc = self.fitz.open(file_path)
            blocks = self._extract_text_blocks(doc)
            heading_hierarchy = self._identify_headings(blocks)
            chunks = self._create_chunks(heading_hierarchy, file_path)
            doc.close()
            
            logger.info(
                f"Created {len(chunks)} semantic chunks from {file_path}"
            )
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking PDF {file_path}: {e}")
            raise
    
    def _extract_text_blocks(self, doc) -> List[Dict]:
        """
        Extract text blocks from PDF with formatting information.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of dictionaries containing text blocks with metadata
        """
        blocks = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get text blocks with format information
            text_dict = page.get_text("dict")
            
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                blocks.append({
                                    "text": text,
                                    "font_size": span.get("size", 0),
                                    "font_name": span.get("font", ""),
                                    "flags": span.get("flags", 0),  # Bold, italic, etc.
                                    "page": page_num + 1,
                                    "bbox": span.get("bbox", None)
                                })
        
        return blocks
    
    def _identify_headings(self, blocks: List[Dict]) -> List[Dict]:
        """
        Identify headings and create hierarchical structure.
        
        Args:
            blocks: List of text blocks with formatting info
            
        Returns:
            List of blocks with heading levels identified
        """
        if not blocks:
            return []
        
        # Calculate average font size for body text
        font_sizes = [b["font_size"] for b in blocks]
        avg_font_size = sum(font_sizes) / len(font_sizes)
        
        # Identify unique heading font sizes
        heading_sizes = set()
        for block in blocks:
            if (block["font_size"] >= self.min_heading_font_size and 
                block["font_size"] > avg_font_size * self.font_size_threshold):
                heading_sizes.add(block["font_size"])
        
        # Sort heading sizes to create hierarchy (larger = higher level)
        sorted_heading_sizes = sorted(heading_sizes, reverse=True)
        
        # Assign heading levels
        for block in blocks:
            block["is_heading"] = False
            block["heading_level"] = None
            
            if block["font_size"] in heading_sizes:
                block["is_heading"] = True
                block["heading_level"] = sorted_heading_sizes.index(
                    block["font_size"]
                ) + 1
                
                # Additional heuristics for heading detection
                if block["flags"] & 2**4:  # Bold flag
                    block["is_heading"] = True
                    if block["heading_level"] is None:
                        block["heading_level"] = len(sorted_heading_sizes) + 1
        
        return blocks
    
    def _create_chunks(
        self, 
        blocks: List[Dict], 
        file_path: str
    ) -> List[Document]:
        """
        Create document chunks based on heading hierarchy.
        
        Args:
            blocks: List of text blocks with heading information
            file_path: Source file path for metadata
            
        Returns:
            List of Document objects
        """
        chunks = []
        current_chunk = {
            "content": [],
            "headings": [],
            "pages": set(),
            "start_page": None
        }
        
        for block in blocks:
            # Start new chunk on heading
            if block["is_heading"]:
                # Save previous chunk if it has content
                if current_chunk["content"]:
                    chunks.append(self._finalize_chunk(
                        current_chunk, 
                        file_path
                    ))
                
                # Start new chunk
                current_chunk = {
                    "content": [],
                    "headings": [block["text"]],
                    "pages": {block["page"]},
                    "start_page": block["page"],
                    "heading_level": block["heading_level"]
                }
            else:
                # Add content to current chunk
                current_chunk["content"].append(block["text"])
                current_chunk["pages"].add(block["page"])
                if current_chunk["start_page"] is None:
                    current_chunk["start_page"] = block["page"]
            
            # Split chunk if it exceeds max size
            current_text = " ".join(current_chunk["content"])
            if len(current_text) > self.max_chunk_size:
                chunks.append(self._finalize_chunk(current_chunk, file_path))
                current_chunk = {
                    "content": [],
                    "headings": current_chunk["headings"],
                    "pages": {block["page"]},
                    "start_page": block["page"],
                    "heading_level": current_chunk.get("heading_level")
                }
        
        # Add final chunk
        if current_chunk["content"]:
            chunks.append(self._finalize_chunk(current_chunk, file_path))
        
        return chunks
    
    def _finalize_chunk(
        self, 
        chunk_data: Dict, 
        file_path: str
    ) -> Document:
        """
        Convert chunk data to Document object.
        
        Args:
            chunk_data: Dictionary containing chunk information
            file_path: Source file path
            
        Returns:
            Document object with content and metadata
        """
        # Build content with heading
        content_parts = []
        if chunk_data["headings"]:
            content_parts.append("# " + " > ".join(chunk_data["headings"]))
            content_parts.append("")
        
        content_parts.append(" ".join(chunk_data["content"]))
        content = "\n".join(content_parts)
        
        # Build metadata
        metadata = {
            "source": file_path,
            "file_name": os.path.basename(file_path),
            "chunk_type": "semantic",
            "headings": chunk_data["headings"],
            "heading_level": chunk_data.get("heading_level"),
        }
        
        if self.include_page_numbers:
            pages = sorted(chunk_data["pages"])
            metadata["pages"] = pages
            metadata["page"] = chunk_data["start_page"]
            if len(pages) > 1:
                metadata["page_range"] = f"{pages[0]}-{pages[-1]}"
        
        return Document(page_content=content, metadata=metadata)
    
    def chunk_with_fallback(
        self, 
        file_path: str,
        fallback_chunk_size: int = 1000,
        fallback_chunk_overlap: int = 200
    ) -> List[Document]:
        """
        Attempt semantic chunking, fall back to character-based splitting if needed.
        
        Args:
            file_path: Path to PDF file
            fallback_chunk_size: Chunk size for fallback method
            fallback_chunk_overlap: Overlap for fallback method
            
        Returns:
            List of Document objects
        """
        try:
            return self.chunk_pdf(file_path)
        except Exception as e:
            logger.warning(
                f"Semantic chunking failed for {file_path}, "
                f"falling back to character-based: {e}"
            )
            
            # Fallback to simple PDF loading
            from langchain_community.document_loaders import PyPDFLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=fallback_chunk_size,
                chunk_overlap=fallback_chunk_overlap
            )
            chunks = splitter.split_documents(docs)
            
            # Mark as fallback chunks
            for chunk in chunks:
                chunk.metadata["chunk_type"] = "character_based_fallback"
            
            return chunks


class HeadingBasedChunker:
    """
    Alternative implementation using PDF table of contents (TOC) if available.
    This is faster but only works if PDF has embedded TOC/outline.
    """
    
    def __init__(self, max_chunk_size: int = 4000):
        """
        Initialize TOC-based chunker.
        
        Args:
            max_chunk_size: Maximum characters per chunk
        """
        self.max_chunk_size = max_chunk_size
        
        try:
            import fitz
            self.fitz = fitz
            self.available = True
        except ImportError:
            logger.warning("PyMuPDF not installed")
            self.available = False
    
    def chunk_pdf_by_toc(self, file_path: str) -> List[Document]:
        """
        Chunk PDF using its table of contents.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of Document objects
            
        Raises:
            ValueError: If PDF has no TOC
        """
        if not self.available:
            raise ImportError("PyMuPDF is required")
        
        doc = self.fitz.open(file_path)
        toc = doc.get_toc()
        
        if not toc:
            doc.close()
            raise ValueError(f"No table of contents found in {file_path}")
        
        chunks = []
        
        for i, entry in enumerate(toc):
            level, title, page_num = entry
            
            # Determine end page (next TOC entry or last page)
            if i + 1 < len(toc):
                end_page = toc[i + 1][2] - 1
            else:
                end_page = len(doc)
            
            # Extract text from page range
            content = []
            for page_idx in range(page_num - 1, min(end_page, len(doc))):
                page = doc[page_idx]
                content.append(page.get_text())
            
            full_content = "\n".join(content)
            
            # Create document
            metadata = {
                "source": file_path,
                "file_name": os.path.basename(file_path),
                "chunk_type": "toc_based",
                "heading": title,
                "heading_level": level,
                "page": page_num,
                "page_range": f"{page_num}-{end_page}"
            }
            
            doc_chunk = Document(
                page_content=f"# {title}\n\n{full_content}",
                metadata=metadata
            )
            chunks.append(doc_chunk)
        
        doc.close()
        logger.info(
            f"Created {len(chunks)} TOC-based chunks from {file_path}"
        )
        return chunks
