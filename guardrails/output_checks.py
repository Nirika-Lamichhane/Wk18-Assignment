import json
import re
from typing import Dict, Any, Tuple

# Predefined valid response schema structure
REQUIRED_FIELDS = {
    "destination": str,
    "country": str,
    "recommended_attractions": list,
    "safety_note": str
}

def validate_schema(response: Any) -> Tuple[bool, str]:
    """Ensures response is valid JSON and matches field types."""
    # Check if raw string needs JSON parsing
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            return False, "Output failed JSON decoding."

    if not isinstance(response, dict):
        return False, "Output is not a valid JSON object/dictionary."

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in response:
            return False, f"Missing required field: '{field}'"
        if not isinstance(response[field], expected_type):
            return False, f"Invalid type for field '{field}': expected {expected_type.__name__}, got {type(response[field]).__name__}"
            
    return True, "Schema valid"

def validate_groundedness(response_data: Dict[str, Any], reference_db: Dict[str, Any]) -> Tuple[bool, str]:
    """Evaluates whether destination and attractions are supported by reference data."""
    destinations = reference_db.get("destinations", {})
    dest_name = response_data.get("destination")

    if dest_name not in destinations:
        return False, f"Destination '{dest_name}' is not grounded in the reference database."

    valid_attractions = destinations[dest_name].get("attractions", [])
    for attraction in response_data.get("recommended_attractions", []):
        if attraction not in valid_attractions:
            return False, f"Attraction '{attraction}' is not supported by reference records."

    return True, "Output claims are fully grounded."

def sanitize_output_sensitive_info(text: str) -> str:
    """Checks and redacts PII or sensitive leakage before sending to user."""
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    sanitized = re.sub(email_pattern, "[REDACTED_EMAIL]", text)
    sanitized = re.sub(phone_pattern, "[REDACTED_PHONE]", sanitized)
    return sanitized

def apply_output_guardrails(raw_output: Any, reference_db: Dict[str, Any]) -> Dict[str, Any]:
    """Enforces all output guardrails with a safe fallback mechanism."""
    # 1. Schema Validation
    is_valid_schema, schema_msg = validate_schema(raw_output)
    if not is_valid_schema:
        return {
            "status": "error",
            "fallback": True,
            "message": "Safe Fallback: Generated response violated structural schema.",
            "details": schema_msg
        }

    data = json.loads(raw_output) if isinstance(raw_output, str) else raw_output

    # 2. Groundedness Validation
    is_grounded, ground_msg = validate_groundedness(data, reference_db)
    if not is_grounded:
        return {
            "status": "error",
            "fallback": True,
            "message": "Safe Fallback: Response contained unverified claims.",
            "details": ground_msg
        }

    # 3. Sensitive Information Detection / Redaction
    data["safety_note"] = sanitize_output_sensitive_info(data.get("safety_note", ""))
    return {
        "status": "success",
        "fallback": False,
        "data": data
    }