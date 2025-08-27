import logging
from langchain_ollama import OllamaLLM

# Test with the smaller llama model
llm = OllamaLLM(
    model="llama3.1:latest",
    base_url="http://localhost:5050",
    timeout=30
)

logger = logging.getLogger(__name__)
logger.info("Testing with llama3.1...")
try:
    response = llm.invoke("Say hello")
    logger.info("Success! Response: %s", response)
except Exception as e:
    logger.error("Error: %s", e)