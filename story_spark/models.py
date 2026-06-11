from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class StoryRequest(BaseModel):
    child_name: str = Field(default="", max_length=40)
    age_band: Literal["3-5", "6-8", "9-12"] = "6-8"
    mode: Literal["bedtime", "adventure", "read_aloud"] = "bedtime"
    theme: Literal["moonlit_forest", "ocean", "dinosaurs", "magic_garden", "space", "cozy_town"] = "moonlit_forest"
    characters: str = Field(default="a curious child and a friendly firefly", max_length=160)
    tone: Literal["gentle", "funny", "brave", "wonder"] = "gentle"
    length: Literal["short", "medium", "long"] = "short"
    lesson: str = Field(default="", max_length=120)
    exclusions: str = Field(default="", max_length=180)
    premium: bool = False

    @field_validator("child_name", "characters", "lesson", "exclusions")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.replace("<", " ").replace(">", " ").split())


class StoryPage(BaseModel):
    number: int = Field(ge=1, le=16)
    heading: str = Field(min_length=1, max_length=90)
    text: str = Field(min_length=20, max_length=1200)
    narrator_note: str = Field(default="", max_length=180)


class StoryChoice(BaseModel):
    label: str = Field(min_length=1, max_length=90)
    consequence: str = Field(min_length=10, max_length=300)


class StoryResult(BaseModel):
    id: str = ""
    title: str = Field(min_length=1, max_length=120)
    subtitle: str = Field(max_length=180)
    reading_minutes: int = Field(ge=1, le=30)
    pages: list[StoryPage] = Field(min_length=2, max_length=16)
    choices: list[StoryChoice] = Field(default_factory=list, max_length=4)
    ending: str = Field(min_length=20, max_length=900)
    narration_script: str = Field(min_length=20, max_length=4000)
    safety_notes: list[str] = Field(default_factory=list, max_length=5)
    ownership_note: str = "Created for personal family use with Story Spark Studio."
    generation: Literal["deterministic", "ai"] = "ai"
    credits_remaining: int | None = None
