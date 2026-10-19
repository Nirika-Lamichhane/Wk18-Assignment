import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

print("Fetching available models from Groq...")
try:
    models = client.models.list()
    print("\n--- AVAILABLE MODELS ---")
    for model in models.data:
        print(model.id)
    print("------------------------\n")
except Exception as e:
    print(f"Error: {e}")