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
    "closing line."
)
STORY_HISTORY_SIZE = 200  # how many past titles to remember, to steer the model away from repeats
TARGET_WORDS_PER_MINUTE = 150
TARGET_VIDEO_MINUTES = (2, 6)  # (min, max) target narration length

# --- Voiceover (ElevenLabs) ---
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # default "Rachel" voice — swap for your own
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"
ELEVENLABS_STABILITY = 0.45
ELEVENLABS_SIMILARITY_BOOST = 0.75

# --- Captions ---
CAPTION_WORDS_PER_CHUNK = 4
CAPTION_FONT = ASSETS_DIR / "fonts" / "Anton-Regular.ttf"
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
THUMB_MAX_CHARS_PER_LINE = 18

# --- YouTube upload ---
YT_CLIENT_SECRETS_FILE = ROOT_DIR / "client_secrets.json"
YT_TOKEN_FILE = STATE_DIR / "youtube_token.json"
YT_CATEGORY_ID = "24"  # Entertainment
YT_PRIVACY_STATUS = "private"  # "private" | "unlisted" | "public" — start private, promote manually
YT_DEFAULT_TAGS = ["reddit stories", "storytime", "aita"]
