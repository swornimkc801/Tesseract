import os
from dotenv import load_dotenv
from huggingface_hub import HfApi, InferenceClient

load_dotenv()
token = os.getenv("HF_TOKEN")

# Test basic API connection
try:
    api = HfApi()
    user_info = api.whoami(token=token)
    print(f"✅ Basic connection success! User: {user_info['name']}")
    
    # Test inference endpoint
    client = InferenceClient(token=token)
    test_response = client.text_generation("Explain software engineering in 1 sentence", max_new_tokens=50)
    print(f"✅ Inference test success! Response: {test_response}")
    
except Exception as e:
    print(f"❌ Failed: {str(e)}")