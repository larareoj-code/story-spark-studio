from __future__ import annotations

import os
import hashlib

from .models import StoryRequest, StoryResult
from .safety import validate_request_safety, validate_result_safety


SYSTEM_PROMPT = """You write warm, original, parent-friendly stories for children.
Follow the supplied age band and exclusions. Never use copyrighted or trademarked characters,
real contact details, professional medical advice, graphic danger, strangers inviting children away,
weapons, self-harm, or frightening content. Give the story a complete emotional arc. For adventure
mode include exactly two meaningful choices; other modes may have no choices. Keep all settings and
characters original. The narration script must contain the entire story in read-aloud form."""


def generate_ai_story(request: StoryRequest) -> StoryResult:
    validate_request_safety(request)
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    moderation_text = " ".join((request.child_name, request.characters, request.lesson, request.exclusions))
    moderation = client.moderations.create(model="omni-moderation-latest", input=moderation_text or "family story")
    if moderation.results[0].flagged:
        raise ValueError("That request needs a safer, more family-friendly direction.")

    response = client.responses.parse(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.model_dump_json()},
        ],
        text_format=StoryResult,
    )
    result = response.output_parsed
    if result is None:
        raise RuntimeError("The story response was incomplete.")
    result.id = hashlib.sha1(response.id.encode()).hexdigest()[:12]
    result.generation = "ai"
    validate_result_safety(result)
    return result
