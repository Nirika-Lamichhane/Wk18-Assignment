import json
from pathlib import Path
from guardrails.input_checks import detect_and_mask_pii, detect_prompt_injection, classify_sensitive_topic
from guardrails.output_checks import apply_output_guardrails

# Load reference knowledge base
BASE_DIR = Path(__file__).parent
with open(BASE_DIR / "data" / "reference_info.json", "r") as f:
    REFERENCE_DATA = json.load(f)

def mock_llm_generate(user_prompt: str) -> str:
    """Simulates an LLM response based on the sanitized prompt."""
    prompt_lower = user_prompt.lower()
    
    if "pokhara" in prompt_lower:
        return json.dumps({
            "destination": "Pokhara",
            "country": "Nepal",
            "recommended_attractions": ["Phewa Lake", "Sarangkot"],
            "safety_note": "Generally safe. Beware of monsoon weather from June to August."
        })
    elif "kyoto" in prompt_lower:
        return json.dumps({
            "destination": "Kyoto",
            "country": "Japan",
            "recommended_attractions": ["Fushimi Inari Taisha", "Kinkaku-ji"],
            "safety_note": "Very safe. Respect local customs."
        })
    elif "hallucinate" in prompt_lower:
        # Deliberately ungrounded output for testing
        return json.dumps({
            "destination": "Atlantis",
            "country": "Ocean",
            "recommended_attractions": ["Sunken Temple"],
            "safety_note": "Bring oxygen."
        })
    elif "bad_schema" in prompt_lower:
        # Deliberately broken schema for testing
        return "I am unable to output JSON, but Pokhara is great!"
    else:
        return json.dumps({
            "destination": "Unknown",
            "country": "Unknown",
            "recommended_attractions": [],
            "safety_note": "No info."
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
    raw_response = mock_llm_generate(sanitized_input)

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