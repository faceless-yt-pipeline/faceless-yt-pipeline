"""Generate an original narration script (title + story) using Claude.

No external story source is scraped or adapted — Claude invents a fictional
story matching the configured genre/style. This intentionally avoids relying
on Reddit's API, since AI use of Reddit data requires separate written
approval under Reddit's Responsible Builder Policy.
"""
import json
import logging
import random

import anthropic

import config

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "{style}\n\n"
    "Invent an original, entirely fictional story for the requested genre — do not "
    "reuse or lightly adapt any specific real post, article, or published work; the "
    "story and characters must be your own invention. "
    "Target length: {min_min}-{max_min} minutes of narration at roughly {wpm} words "
    "per minute (~{min_words}-{max_words} words). "
    "Respond in exactly this format, nothing else:\n"
    "TITLE: <a punchy, clickable title under 80 characters, for a video thumbnail>\n"
    "---\n"
    "<the full narration script — no markdown, no labels, no quotation marks>"
)


def _load_used_titles() -> list:
    path = config.STATE_DIR / "used_titles.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _remember_title(title: str) -> None:
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = config.STATE_DIR / "used_titles.json"
    titles = _load_used_titles()
    titles.append(title)
    path.write_text(json.dumps(titles[-config.STORY_HISTORY_SIZE:]), encoding="utf-8")


def generate_story() -> dict:
    """Return {"title": str, "script": str} for a freshly invented story."""
    client = anthropic.Anthropic()
    min_min, max_min = config.TARGET_VIDEO_MINUTES
    genre = random.choice(config.STORY_GENRES)

    used_titles = _load_used_titles()
    avoid_note = ""
    if used_titles:
        avoid_note = "Avoid reusing these previous titles/premises: " + "; ".join(used_titles[-15:])

    system = _SYSTEM_PROMPT.format(
        style=config.STORY_STYLE,
        min_min=min_min,
        max_min=max_min,
        wpm=config.TARGET_WORDS_PER_MINUTE,
        min_words=min_min * config.TARGET_WORDS_PER_MINUTE,
        max_words=max_min * config.TARGET_WORDS_PER_MINUTE,
    )
    user_message = f"Genre/theme: {genre}\n{avoid_note}".strip()

    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()

    title, _, script = text.partition("---")
    title = title.replace("TITLE:", "").strip()
    script = script.strip()

    if not title or not script:
        raise RuntimeError(f"Could not parse title/script from model output:\n{text[:500]}")

    _remember_title(title)
    word_count = len(script.split())
    logger.info(
        "Generated original story %r: %d words (~%.1f min at %d wpm)",
        title, word_count, word_count / config.TARGET_WORDS_PER_MINUTE, config.TARGET_WORDS_PER_MINUTE,
    )
    return {"title": title, "script": script}
