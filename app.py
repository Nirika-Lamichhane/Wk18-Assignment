import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from guardrails.input_checks import detect_and_mask_pii, detect_prompt_injection, classify_sensitive_topic
from guardrails.output_checks import apply_output_guardrails

# Load environment variables
load_dotenv()

# Point the client to Groq instead of OpenAI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

# Load reference knowledge base
BASE_DIR = Path(__file__).parent
with open(BASE_DIR / "data" / "reference_info.json", "r") as f:
    REFERENCE_DATA = json.load(f)

def generate_dynamic_response(user_prompt: str, reference_db: dict) -> str:
    """Calls Groq API to generate a dynamic, structured JSON response."""
    
    system_instruction = f"""
    You are a secure travel recommendation assistant. 
    You must ONLY recommend destinations and attractions explicitly listed in this database:
    {json.dumps(reference_db)}
    
    If the user asks for a destination not in the database, do your best to explain it is unsupported, but YOU MUST STILL OUTPUT STRICT JSON.
    
    Respond EXACTLY with this JSON schema:
    {{
        "destination": "String (Name of the city)",
        "country": "String (Name of the country)",
        "recommended_attractions": ["List", "of", "Strings"],
        "safety_note": "String (Brief safety advisory)"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",  # Using Groq's stable Mixtral model            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        # Added debug print to reveal the exact API failure reason
        print(f"\n--- API CONNECTION ERROR ---\n{str(e)}\n----------------------------\n")
        return json.dumps({
            "destination": "Error",
            "country": "Error",
            "recommended_attractions": [],
            "safety_note": f"API Error: {str(e)}"
        })

def process_pipeline(user_input: str) -> dict:
    """Main guardrail execution pipeline."""
    # --- INPUT GUARDRAILS ---
    # 1. Prompt Injection Detection
    if detect_prompt_injection(user_input):
        return {
            "status": "blocked",
            "reason": "Prompt injection detected. Request rejected.",
            "data": None
        }

    # 2. Sensitive Topic Classification
    topic_status = classify_sensitive_topic(user_input)
    if topic_status == "blocked":
        return {
            "status": "blocked",
            "reason": "Request involves restricted/illegal activities.",
            "data": None
        }

    # 3. PII Masking
    sanitized_input = detect_and_mask_pii(user_input)

    # --- MODEL INFERENCE ---
    raw_response = generate_dynamic_response(sanitized_input, REFERENCE_DATA)

    # --- OUTPUT GUARDRAILS ---
    final_output = apply_output_guardrails(raw_response, REFERENCE_DATA)
    
    if topic_status == "requires_advisory" and final_output.get("status") == "success":
        final_output["data"]["safety_note"] += " [SYSTEM ADVISORY: Review local travel advisories.]"

    return final_output

if __name__ == "__main__":
    test_query = "Can you plan a trip to Pokhara? Contact me at test@example.com"
    print("Testing Pipeline:")
    print("User Query:", test_query)
    result = process_pipeline(test_query)
    print("Result:", json.dumps(result, indent=2))