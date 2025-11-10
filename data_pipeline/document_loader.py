"""Document loader for processing multiple directories."""

import os
import logging
from typing import List
from langchain_community.document_loaders import PyPDFLoader, UnstructuredHTMLLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


from .exceptions import DocumentDirectoryNotFoundError, NoDocumentsFoundError

logger = logging.getLogger(__name__)


class DocumentLoader:
    
    def __init__(self):
        pass

    def load_from_directories(self, directories: List[str]) -> List[Document]:
        """Load and chunk documents from multiple directories."""
        all_chunks = []
        
        for directory in directories:
            if not os.path.exists(directory):
                raise DocumentDirectoryNotFoundError(f"Directory not found: {directory}")
            
            try:
                chunks = self._load_directory(directory)
                all_chunks.extend(chunks)
                logger.info(f"Loaded {len(chunks)} chunks from {directory}")
            except Exception as e:
                logger.error(f"Failed to load from {directory}: {e}")
                continue
        
        if not all_chunks:
            raise NoDocumentsFoundError("No valid documents found in any directory")
        
        logger.info(f"Total chunks loaded: {len(all_chunks)}")
        return all_chunks
    
    def _load_directory(self, directory: str) -> List[Document]:
        """Load all supported files from a directory."""
        chunks = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_chunks = self._load_file(file_path)
                    chunks.extend(file_chunks)
                except Exception as e:
                    logger.warning(f"Skipping {file_path}: {e}")
                    continue
        
        return chunks
    
    def load_file(self, file_path: str) -> List[Document]:
        """Load and chunk a single file based on extension."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif file_ext in ['.html', '.htm']:
            loader = UnstructuredHTMLLoader(file_path)
        elif file_ext in ['.txt', '.md']:
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        docs = loader.load()

        return docs
    
    def load_any(self, file_path: str) -> List[Document]:
        return self._load_file(file_path)
    
    def join_docs_content(self, docs: List[Document]) -> str:
        return "\n".join([d.page_content for d in docs])
    
    def truncate_text(self, text: str, max_chars: int) -> str: 
        """Utility function to truncate text."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars-3] + "..."