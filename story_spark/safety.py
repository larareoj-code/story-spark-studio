from __future__ import annotations

import re

from .models import StoryRequest, StoryResult


BLOCKED_PATTERNS = {
    "trademarked character": r"\b(mickey|elsa|spider[- ]?man|harry potter|pokemon|bluey|barbie|batman|superman)\b",
    "personal contact information": r"\b(?:\d{3}[-. ]?\d{3}[-. ]?\d{4}|\S+@\S+\.\S+)\b",
    "professional health advice": r"\b(diagnos(?:e|is)|prescription|dosage|therapy advice|medical advice)\b",
    "unsafe child scenario": r"\b(meet a stranger|leave home alone|run away|weapon|kidnap|suicide|self[- ]harm)\b",
}


def validate_request_safety(request: StoryRequest) -> None:
    combined = " ".join((request.child_name, request.characters, request.lesson, request.exclusions)).lower()
    for label, pattern in BLOCKED_PATTERNS.items():
        if re.search(pattern, combined, re.IGNORECASE):
            raise ValueError(f"Please remove the {label} reference and use an original, family-safe idea.")


def validate_result_safety(result: StoryResult) -> None:
    combined = " ".join([result.title, result.subtitle, result.ending, result.narration_script, *[page.text for page in result.pages]])
    for label, pattern in BLOCKED_PATTERNS.items():
        if re.search(pattern, combined, re.IGNORECASE):
            raise ValueError(f"Generated story failed the {label} safety check.")

    if any(term in combined.lower() for term in ("graphic blood", "terrifying scream", "real gun")):
        raise ValueError("Generated story was too frightening for the selected audience.")

