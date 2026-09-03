# Faceless YouTube Pipeline (Storytelling/Narration)

End-to-end automation: AI-generated story → voiceover → captions → video → thumbnail → YouTube upload.

Stories are entirely invented by Claude — nothing is scraped or adapted from Reddit or any other
platform. (An earlier version of this pipeline sourced stories from Reddit; that approach was
dropped after Reddit denied API access, citing their Responsible Builder Policy's restriction on
using Reddit data for AI/commercial purposes without separate written approval.)

## Setup

1. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

   Also install `ffmpeg` on your system (not via pip):
   * Mac: `brew install ffmpeg`
   * Ubuntu: `sudo apt install ffmpeg`
   * Windows: download from ffmpeg.org and add to PATH

2. API keys — set these as environment variables (see `.env.example`):
   * `ANTHROPIC_API_KEY` — from console.anthropic.com
   * YouTube: download OAuth `client_secrets.json` from Google Cloud Console into the project root (see comments in `scripts/upload_video.py`)

   Voiceover uses `edge-tts` (Microsoft Edge's free online neural voices) — no API key needed. Run
   `edge-tts --list-voices` after installing dependencies to see available voices, then set
   `EDGE_TTS_VOICE` in `config.py`.

3. Assets — add before running:
   * `assets/backgrounds/*.mp4` — royalty-free loopable background footage (satisfying clips, gameplay, ambient scenes — search Pexels/Storyblocks)
   * `assets/thumb_template.png` — a base thumbnail template image
   * `assets/fonts/Anton-Regular.ttf` — or any bold font you like (Google Fonts)

4. Edit `config.py` — story genres/style, voice ID, upload schedule.

## Running

```bash
# Full pipeline: story -> voice -> captions -> video -> thumbnail -> upload
python main.py --mode full

# Stop after story generation so you can review/edit it by hand
python main.py --mode review

# Generate story + audio only (no video render, no upload) — fast iteration
python main.py --mode dry-run
```

Recommended: run in `review` mode for your first 10-20 videos to sanity-check scripts before trusting `full` mode unattended.

## Scheduling it to run automatically

Once you trust the pipeline, run it on a cron job / GitHub Actions / cloud scheduler, e.g. daily at a fixed time:

```cron
0 10 * * * cd /path/to/faceless-yt-pipeline && /usr/bin/python3 main.py --mode full >> logs/pipeline.log 2>&1
```

## Important notes

* Start uploads as "private" or "unlisted" (already default in `config.py`) until you've watched a few end-to-end outputs and trust the pipeline not to publish something broken or off-brand.
* YouTube's policy on mass-produced/repetitive content has tightened — fully unattended channels risk demonetization or suppression. Keeping the `review` mode checkpoint (even skimming the script/thumbnail before `full` runs) meaningfully reduces this risk and costs you ~2 minutes/video.
* Since stories are AI-generated rather than true accounts, don't present them as real events in titles/descriptions — check YouTube's disclosure requirements for altered/synthetic content if that's ever ambiguous for your framing.
* Caption styling, background clip selection logic, and the thumbnail template are deliberately simple — that's the highest-leverage place to spend manual creative effort since it's what actually drives CTR/retention.
