import os
from dotenv import load_dotenv
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_openai import AzureChatOpenAI

load_dotenv()

deployment = os.getenv("AZURE_DEPLOYMENT_NAME") or os.getenv("AZURE_MODEL_NAME")
endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
api_version = os.getenv("AZURE_API_VERSION")
api_key = os.getenv("AZURE_INFERENCE_CREDENTIAL")

print("Testing Azure OpenAI Configuration:")
print(f"Endpoint: {endpoint}")
print(f"Deployment (preferred) or Model: {deployment}")
print(f"API Version: {api_version}")
print(f"API Key: {'***' + api_key[-4:] if api_key else 'Not set'}")

try:
    # Prefer passing an Azure deployment name; falling back to model env may 404
    # if it's not an actual deployment name in your Azure resource.
    model = AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        azure_deployment=deployment,  # alias of deployment_name
        api_version=api_version,
    )
    
    response = model.invoke("Hello, this is a test.")
    print("✅ Success! Azure OpenAI is working.")
    print(f"Response: {response}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTroubleshooting tips:")
    print("1. Set AZURE_DEPLOYMENT_NAME to your Azure deployment name (not the model ID).")
    print("2. Verify your API key is valid")
    print("3. Ensure your endpoint URL is correct")
    print("4. Try a supported API version like '2024-06-01' or '2024-10-01-preview'")