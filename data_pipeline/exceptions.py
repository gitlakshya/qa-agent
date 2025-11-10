"""Custom exceptions for the QA Agent data pipeline."""


class VectorStoreNotFoundError(Exception):
    """Raised when vector store is not found and is required."""
    pass


class VectorStoreCorruptedError(Exception):
    """Raised when vector store exists but is corrupted."""
    pass


class DocumentDirectoryNotFoundError(Exception):
    """Raised when configured document directory doesn't exist."""
    pass


class NoDocumentsFoundError(Exception):
    """Raised when no valid documents found in directories."""
    pass


class EmbeddingModelError(Exception):
    """Raised when embedding model fails to load or process."""
    pass


class SyncError(Exception):
    """Raised when sync operation fails."""
    pass