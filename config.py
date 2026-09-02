"""Central configuration for the faceless YouTube pipeline."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"
LOG_DIR = ROOT_DIR / "logs"
ASSETS_DIR = ROOT_DIR / "assets"
STATE_DIR = ROOT_DIR / "state"

# --- Reddit source ---
SUBREDDITS = ["AmItheAsshole", "confession", "tifu"]
POST_SORT = "top"          # "top", "hot", "new"
POST_TIME_FILTER = "week"  # used when POST_SORT == "top": hour/day/week/month/year/all
MIN_UPVOTES = 500
MIN_BODY_CHARS = 800
MAX_BODY_CHARS = 6000
REDDIT_USER_AGENT = "faceless-yt-pipeline/0.1"
POSTS_TO_FETCH_PER_RUN = 25  # candidates pulled per subreddit before filtering/dedup

# --- Script generation (Anthropic) ---
ANTHROPIC_MODEL = "claude-sonnet-5"
SCRIPT_STYLE = (
    "You are writing a narration script for a faceless YouTube storytelling channel. "
    "Rewrite the Reddit post as a first-person spoken narration: a strong hook in the "
    "first sentence, natural spoken cadence, short sentences, no markdown or headers, "
    "no reference to Reddit, upvotes, or subreddit names, and a satisfying closing line."
)
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
