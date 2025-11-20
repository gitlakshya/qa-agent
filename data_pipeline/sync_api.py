"""API for manual sync operations."""

import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

from .vectorstore_manager import VectorStoreManager

load_dotenv()
logger = logging.getLogger(__name__)


class SyncAPI:
    """API for manual synchronization operations."""
    
    def __init__(self):
        self.manager = VectorStoreManager()
        self.default_directories = self._get_default_directories()
    
    def _get_default_directories(self) -> List[str]:
        """Get default directories from environment variables."""
        directories = []
        
        # Get directories from environment
        pdf_dir = os.getenv("PDF_DIR")
        if pdf_dir and pdf_dir != "none":
            directories.append(pdf_dir)
        
        # Add other configured directories
        extra_dirs = os.getenv("EXTRA_DIRS", "").split(",")
        for dir_path in extra_dirs:
            if dir_path.strip():
                directories.append(dir_path.strip())
        
        # Default fallback directories
        if not directories:
            directories = ["Related_docs"]
        
        return directories
    
    def sync(self, directories: List[str] = None) -> Dict[str, Any]:
        """Manually trigger sync operation."""
        if directories is None:
            directories = self.default_directories
        
        try:
            logger.info(f"Starting sync for directories: {directories}")
            self.manager.rebuild_vectorstore(directories)
            
            return {
                "status": "success",
                "message": "Vector store rebuilt successfully",
                "directories": directories,
                "vectorstore_path": self.manager.persist_directory
            }
        
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "directories": directories
            }
    
    def status(self) -> Dict[str, Any]:
        """Get current vector store status."""
        try:
            exists = self.manager.validate_vectorstore()
            if exists:
                vectorstore = self.manager.get_vectorstore()
                count = vectorstore._collection.count()
                return {
                    "status": "ready",
                    "vectorstore_exists": True,
                    "document_count": count,
                    "path": self.manager.persist_directory
                }
            else:
                return {
                    "status": "missing",
                    "vectorstore_exists": False,
                    "message": "Vector store not found. Run sync first.",
                    "path": self.manager.persist_directory
                }
        except Exception as e:
            return {
                "status": "error",
                "vectorstore_exists": False,
                "message": str(e),
                "path": self.manager.persist_directory
            }


# Global sync API instance
sync_api = SyncAPI()