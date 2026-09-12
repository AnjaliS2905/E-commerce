import re

PHONE = re.compile(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)")
CARD4 = re.compile(r"(?i)\b(?:card|payment card|last[- ]?4)\D{0,12}(\d{4})\b")
INJECTION = re.compile(r"(?i)(ignore\s+(all|any|previous)\s+instructions|reveal\s+(the|your)\s+(system|developer)\s+prompt|disable\s+(guardrails|safety))")

def mask_pii(text):
    text = PHONE.sub("[PHONE_MASKED]", text)
    text = CARD4.sub(lambda m: m.group(0)[:m.group(0).rfind(m.group(1))] + "[CARD4_MASKED]", text)
    return text

def detect_prompt_injection(text):
    return bool(INJECTION.search(text))

def input_guard(text):
    masked = mask_pii(text)
    if detect_prompt_injection(masked):
        return masked, False, "Prompt injection detected."
    return masked, True, None
