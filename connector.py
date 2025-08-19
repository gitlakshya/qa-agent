import os
from langchain_ollama import OllamaLLM


def _get_base_url() -> str:
    return os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_BASE_URL") or "http://localhost:5050"


# Conservative defaults to avoid hangs and excessive memory use
llm = OllamaLLM(
    model="gpt-oss:20b",
    base_url=_get_base_url(),
    timeout=300,
    num_predict=1024,
    num_ctx=8192
)


def llm_healthcheck() -> bool:
    """Quick probe to ensure the model responds within a short deadline."""
    try:
        _ = llm.invoke("ping")
        print(_)
        return True
    except Exception:
        return False
    
llm_healthcheck()