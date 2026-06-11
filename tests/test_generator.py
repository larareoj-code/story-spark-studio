import pytest

from story_spark.generator import generate_free_story
from story_spark.models import StoryRequest, StoryResult


def test_deterministic_story_is_stable():
    request = StoryRequest(child_name="Maya", theme="space")
    assert generate_free_story(request).model_dump() == generate_free_story(request).model_dump()


@pytest.mark.parametrize("mode", ["bedtime", "adventure", "read_aloud"])
def test_all_modes_generate(mode):
    result = generate_free_story(StoryRequest(mode=mode))
    assert isinstance(result, StoryResult)
    assert len(result.pages) >= 2
    assert len(result.choices) == (2 if mode == "adventure" else 0)


@pytest.mark.parametrize("characters", ["Mickey Mouse", "meet a stranger", "email me at child@example.com", "medical advice for a diagnosis"])
def test_unsafe_or_trademarked_prompts_are_rejected(characters):
    with pytest.raises(ValueError):
        generate_free_story(StoryRequest(characters=characters))


def test_schema_rejects_unsupported_age():
    with pytest.raises(ValueError):
        StoryRequest(age_band="13-17")

