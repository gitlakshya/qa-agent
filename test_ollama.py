from connector import llm

print("Testing Ollama connection...")
try:
    response = llm.invoke("Hello, can you respond?")
    print(f"Success! Response: {response}")
except Exception as e:
    print(f"Error: {e}")