from langchain_ollama import OllamaLLM

# Test with the smaller llama model
llm = OllamaLLM(
    model="llama3.1:latest",
    base_url="http://localhost:5050",
    timeout=30
)

print("Testing with llama3.1...")
try:
    response = llm.invoke("Say hello")
    print(f"Success! Response: {response}")
except Exception as e:
    print(f"Error: {e}")