import os
import logging
from dotenv import load_dotenv

from data_pipeline.vectorstore_manager import VectorStoreManager
from data_pipeline import VectorStoreNotFoundError, VectorStoreCorruptedError

load_dotenv()
logger = logging.getLogger(__name__)


def get_vectorstore_manager():
    persist_directory = os.getenv("DB_DIR", "chroma-db")
    return VectorStoreManager(persist_directory)


def get_vectorstore():
    manager = get_vectorstore_manager()
    try:
        return manager.get_vectorstore()
    except VectorStoreNotFoundError:
        logger.warning("Vector store not found. Use sync API to create it.")
        raise
    except VectorStoreCorruptedError:
        logger.error("Vector store is corrupted. Use sync API to rebuild it.")
        raise


vectorstore = None

def load_vectorstore_if_needed():
    global vectorstore
    if vectorstore is None:
        try:
            vectorstore = get_vectorstore()
            logger.info("Vector store loaded successfully")
        except (VectorStoreNotFoundError, VectorStoreCorruptedError) as e:
            logger.warning(f"Vector store not available: {e}")
            raise
    return vectorstore