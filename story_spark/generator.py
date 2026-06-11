from __future__ import annotations

import hashlib
import random

from .models import StoryChoice, StoryPage, StoryRequest, StoryResult
from .safety import validate_request_safety


THEMES = {
    "moonlit_forest": ("The Lantern in the Moonlit Forest", "silver leaves", "a lantern moth", "the quiet hill"),
    "ocean": ("The Song Beneath the Teal Sea", "bubble gardens", "a giggling seahorse", "the coral arch"),
    "dinosaurs": ("The Tiny Roar in Fern Valley", "giant ferns", "a gentle baby dinosaur", "the warm stone nest"),
    "magic_garden": ("The Garden That Woke at Dusk", "singing flowers", "a pocket-sized gardener", "the wishing gate"),
    "space": ("The Sleepy Starship", "glowing constellations", "a helpful moon robot", "the lavender planet"),
    "cozy_town": ("The Bell of Buttonberry Town", "cinnamon rooftops", "a mail-carrying squirrel", "the clockwork square"),
}

TONE_LINES = {
    "gentle": "Nothing needed to be rushed; the best discoveries waited for careful footsteps.",
    "funny": "The plan was excellent, except for the part involving a hat that kept sneezing.",
    "brave": "Being brave did not mean feeling fearless; it meant taking one kind step anyway.",
    "wonder": "Every ordinary thing seemed to hold a small, bright secret.",
}


def _seed(request: StoryRequest) -> int:
    return int(hashlib.sha256(request.model_dump_json().encode()).hexdigest()[:16], 16)


def generate_free_story(request: StoryRequest) -> StoryResult:
    validate_request_safety(request)
    rng = random.Random(_seed(request))
    title, place, companion, destination = THEMES[request.theme]
    hero = request.child_name or "the young storyteller"
    lesson = request.lesson or "small kindness can light the way"
    details = [
        f"As evening settled, {hero} noticed {place} shimmering beyond the window. {TONE_LINES[request.tone]}",
        f"At the edge of the path, {hero} met {companion}. Together they followed three soft clues toward {destination}.",
        f"The final clue could only be solved by remembering that {lesson}. The path brightened as soon as they tried.",
    ]
    rng.shuffle(details)
    pages = [StoryPage(number=index + 1, heading=("Once Upon Tonight", "A Curious Clue", "The Bright Way Home")[index], text=text, narrator_note="Pause for a breath and invite a quiet prediction." if index == 1 else "") for index, text in enumerate(details)]
    choices = []
    if request.mode == "adventure":
        choices = [
            StoryChoice(label="Follow the glowing footprints", consequence="They lead to a friendly puzzle beneath the old arch."),
            StoryChoice(label="Listen for the tiny bell", consequence="The sound reveals a hidden shortcut lined with fireflies."),
        ]
    ending = f"Back at home, {hero} tucked the adventure beside their dreams and remembered that {lesson}."
    narration = "\n\n".join(f"{page.heading}. {page.text}" for page in pages) + f"\n\n{ending}"
    story_id = hashlib.sha1(f"free:{_seed(request)}".encode()).hexdigest()[:12]
    return StoryResult(id=story_id, title=title, subtitle=f"A {request.tone} {request.mode.replace('_', ' ')} for ages {request.age_band}", reading_minutes=4, pages=pages, choices=choices, ending=ending, narration_script=narration, safety_notes=["Use as a calm shared reading activity.", "All characters and settings are original."], generation="deterministic")

