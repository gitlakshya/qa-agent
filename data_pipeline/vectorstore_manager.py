import os
import shutil
import logging
import time
import gc
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import ssl

from .exceptions import EmbeddingModelError, SyncError, VectorStoreCorruptedError
from .document_loader import DocumentLoader

logger = logging.getLogger(__name__)

ssl._create_default_https_context = ssl._create_unverified_context
class VectorStoreManager:
    
    def __init__(self, persist_directory: str = "chroma-db"):
        self.persist_directory = persist_directory
        try:
            
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        except Exception as e:
            raise EmbeddingModelError(f"Failed to load embedding model: {e}")
    
    def rebuild_vectorstore(self, directories: List[str]) -> None:
        
        try:
            loader = DocumentLoader()
            documents = loader.load_from_directories(directories)
            
            self._cleanup_connections()
            
            self._safe_remove_directory(self.persist_directory)
            
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            logger.info(f"Vector store rebuilt with {len(documents)} documents at {self.persist_directory}")
            
        except Exception as e:
            raise SyncError(f"Failed to rebuild vector store: {e}")
    
    def _cleanup_connections(self):
        try:
            # Force garbage collection
            gc.collect()
            # Small delay to allow cleanup
            time.sleep(0.5)
        except Exception:
            pass
    
    def _safe_remove_directory(self, directory: str, max_retries: int = 3):
        if not os.path.exists(directory):
            return
        
        for attempt in range(max_retries):
            try:
                shutil.rmtree(directory)
                logger.info(f"Removed existing vector store at {directory}")
                return
            except PermissionError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed to remove {directory}: {e}. Retrying...")
                    time.sleep(1)
                    continue
                else:
                    raise SyncError(f"Cannot remove vector store directory after {max_retries} attempts. "
                                  f"Please close all applications using the vector store and try again. Error: {e}")
            except Exception as e:
                raise SyncError(f"Failed to remove vector store directory: {e}")
    
    def validate_vectorstore(self) -> bool:
        if not os.path.exists(self.persist_directory):
            return False
        
        try:
            # Try to load the vector store
            vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            # Test basic functionality
            vectorstore._collection.count()
            # Clean up the test connection
            del vectorstore
            gc.collect()
            return True
        except Exception as e:
            raise VectorStoreCorruptedError(f"Vector store is corrupted: {e}")
    
    def get_vectorstore(self) -> Chroma:
        """Get the vector store instance."""
        if not self.validate_vectorstore():
            from .exceptions import VectorStoreNotFoundError
            raise VectorStoreNotFoundError(f"Vector store not found at {self.persist_directory}")
        
        try:
            return Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        except Exception as e:
            raise VectorStoreCorruptedError(f"Failed to load vector store: {e}")