import re

def detect_and_mask_pii(text: str) -> str:
    """Masks standard email addresses and phone numbers."""
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    text = re.sub(email_pattern, "[EMAIL REDACTED]", text)
    text = re.sub(phone_pattern, "[PHONE REDACTED]", text)
    return text

def detect_prompt_injection(text: str) -> bool:
    """Returns True if malicious instructions are detected."""
    injection_keywords = ["ignore previous instructions", "system prompt", "bypass", "jailbreak", "override"]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in injection_keywords)

def classify_sensitive_topic(text: str) -> str:
    """Classifies the prompt to determine if it requires special handling."""
    text_lower = text.lower()
    if any(word in text_lower for word in ["smuggle", "illegal", "drugs", "bribe"]):
        return "blocked"
    if any(word in text_lower for word in ["danger", "war", "crime rate", "unsafe"]):
        return "requires_advisory"
    return "safe"