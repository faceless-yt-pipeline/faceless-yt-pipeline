"""Turn a Reddit post into a spoken-narration script using Claude."""
import logging

import anthropic

import config

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "{style}\n\n"
    "Target length: {min_min}-{max_min} minutes of narration at roughly "
    "{wpm} words per minute (~{min_words}-{max_words} words). "
    "Output ONLY the narration script text, nothing else — no title, no labels, no quotation marks."
)


def generate_script(story: dict) -> str:
    client = anthropic.Anthropic()
    min_min, max_min = config.TARGET_VIDEO_MINUTES
    system = _SYSTEM_PROMPT.format(
        style=config.SCRIPT_STYLE,
        min_min=min_min,
        max_min=max_min,
        wpm=config.TARGET_WORDS_PER_MINUTE,
        min_words=min_min * config.TARGET_WORDS_PER_MINUTE,
        max_words=max_min * config.TARGET_WORDS_PER_MINUTE,
    )
    user_message = f"Title: {story['title']}\n\n{story['body']}"

    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    script = "".join(block.text for block in response.content if block.type == "text").strip()
    word_count = len(script.split())
    logger.info(
        "Generated script: %d words (~%.1f min at %d wpm)",
        word_count, word_count / config.TARGET_WORDS_PER_MINUTE, config.TARGET_WORDS_PER_MINUTE,
    )
    return script
