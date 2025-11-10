import logging
from llm.connector import llm

logger = logging.getLogger(__name__)

logger.info("Testing Ollama connection...")
try:
    response = llm.invoke("Hello, can you respond?")
    logger.info("Success! Response: %s", response)
except Exception as e:
    logger.error("Error: %s", e)