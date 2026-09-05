"""Central configuration for the faceless YouTube pipeline."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"
ASSETS_DIR = ROOT_DIR / "assets"
STATE_DIR = ROOT_DIR / "state"

# --- Story generation (Anthropic) ---
# Stories are entirely invented by Claude — no external source (e.g. Reddit) is
# scraped, which avoids needing separate approval for AI/commercial use of
# someone else's platform data.
ANTHROPIC_MODEL = "claude-sonnet-5"
STORY_GENRES = [
    "an unexpected twist that recontextualizes everything at the end",
    "a workplace conflict that escalates and then resolves satisfyingly",
    "a family secret uncovered years later",
    "a small act of justice against someone who had it coming",
    "a stranger's kindness that changes the outcome of a bad day",
]
STORY_STYLE = (
    "You are writing a narration script for a faceless YouTube storytelling channel. "
    "Write it as a first-person spoken narration: a strong hook in the first sentence, "
    "natural spoken cadence, short sentences, no markdown or headers, and a satisfying "
    "closing line. Do not include suicide, self-harm, or suicidal ideation as a plot "
    "point or emotional beat, even briefly or as something the narrator only considers "
    "and moves past — low points should come from other sources of hardship instead."
)
STORY_HISTORY_SIZE = 200  # how many past titles to remember, to steer the model away from repeats
TARGET_WORDS_PER_MINUTE = 150
TARGET_VIDEO_MINUTES = (2, 6)  # (min, max) target narration length

# --- Voiceover (edge-tts — free, no API key) ---
# Full voice list: run `edge-tts --list-voices` after installing requirements.
EDGE_TTS_VOICE = "en-US-AriaNeural"
EDGE_TTS_RATE = "+0%"   # e.g. "+10%" to speed up, "-10%" to slow down

# --- Captions ---
CAPTION_WORDS_PER_CHUNK = 4
CAPTION_FONT = ASSETS_DIR / "fonts" / "Anton-Regular.ttf"
CAPTION_FONT_FAMILY = "Anton"  # the font's actual family name, not its filename — libass
                                 # matches on this. Check with fontTools if you swap fonts:
                                 # TTFont(path)['name'].getDebugName(1)
CAPTION_FONT_SIZE = 90
CAPTION_FONT_COLOR = "FFFFFF"      # RGB hex, white
CAPTION_HIGHLIGHT_COLOR = "FFD700"  # RGB hex, gold — active word
CAPTION_OUTLINE_COLOR = "000000"   # RGB hex, black outline
CAPTION_MARGIN_V = 260

# --- Video render ---
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
BACKGROUND_DIR = ASSETS_DIR / "backgrounds"

# --- Thumbnail ---
THUMB_TEMPLATE = ASSETS_DIR / "thumb_template.png"
THUMB_SIZE = (1280, 720)
THUMB_FONT = ASSETS_DIR / "fonts" / "Anton-Regular.ttf"
THUMB_FONT_SIZE = 110
THUMB_FONT_COLOR = (255, 255, 255)
THUMB_STROKE_COLOR = (0, 0, 0)
THUMB_STROKE_WIDTH = 6

# --- YouTube upload ---
YT_CLIENT_SECRETS_FILE = ROOT_DIR / "client_secrets.json"
YT_TOKEN_FILE = STATE_DIR / "youtube_token.json"
YT_CATEGORY_ID = "24"  # Entertainment
YT_PRIVACY_STATUS = "private"  # "private" | "unlisted" | "public" — start private, promote manually
YT_DEFAULT_TAGS = ["quiet confessions", "storytime", "storytelling"]

# --- Hashtags (YouTube shows the first 3 found in a description above the title) ---
VIDEO_HASHTAGS = ["#QuietConfessions", "#StoryTime", "#Storytelling"]
SHORTS_HASHTAGS = ["#QuietConfessions", "#Shorts", "#StoryTime"]

# --- Shorts ---
SHORTS_ENABLED = True
SHORTS_PER_VIDEO = 3  # spread evenly across the story: opening, ~1/3, ~2/3
SHORTS_MAX_SECONDS = 55  # comfortably under YouTube's 60s "classic" Shorts threshold
SHORTS_DEFAULT_TAGS = ["quiet confessions", "shorts", "storytime"]
