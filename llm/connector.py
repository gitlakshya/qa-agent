import os
import ssl
import logging
from langchain_ollama import OllamaLLM
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

# Disable SSL verification globally
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()

def _get_base_url(service) -> str:
    if service == "Azure":
        return os.getenv("AZURE_INFERENCE_ENDPOINT")
    else:
        return os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"

def _get_model_name() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.1:latest")

logger = logging.getLogger(__name__)


azurellm = AzureChatOpenAI(
    azure_endpoint=_get_base_url("Azure"),
    api_key=os.getenv("AZURE_INFERENCE_CREDENTIAL"),
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME") or os.getenv("AZURE_MODEL_NAME"),
    api_version=os.getenv("AZURE_API_VERSION") or "2024-10-01-preview",
    #temperature=0.3,
    #timeout=300
)



llm = OllamaLLM(
    model=_get_model_name(),
    base_url=_get_base_url(service="Ollama"),
    timeout=300,
    num_predict=4096,
    num_ctx=32784,
)

def llm_healthcheck() -> bool:
    """Quick probe to ensure the model responds within a short deadline."""
    try:
        _ = llm.invoke("ping")
        logger.debug("LLM ping response: %s", _)
        return True
    except Exception as e:
        logger.warning("LLM healthcheck failed: %s", e)
        return False