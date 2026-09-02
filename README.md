# Faceless YouTube Pipeline (Storytelling/Narration)

End-to-end automation: Reddit story → script → voiceover → captions → video → thumbnail → YouTube upload.

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
   * `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` — create an app at reddit.com/prefs/apps
   * `ANTHROPIC_API_KEY` — from console.anthropic.com
   * `ELEVENLABS_API_KEY` — from elevenlabs.io
   * YouTube: download OAuth `client_secrets.json` from Google Cloud Console into the project root (see comments in `scripts/upload_video.py`)

3. Assets — add before running:
   * `assets/backgrounds/*.mp4` — royalty-free loopable background footage (satisfying clips, gameplay, ambient scenes — search Pexels/Storyblocks)
   * `assets/thumb_template.png` — a base thumbnail template image
   * `assets/fonts/Anton-Regular.ttf` — or any bold font you like (Google Fonts)

4. Edit `config.py` — subreddits, voice ID, script style, upload schedule.

## Running

```bash
# Full pipeline: source -> script -> voice -> captions -> video -> thumbnail -> upload
python main.py --mode full

# Stop after script generation so you can review/edit it by hand
python main.py --mode review

# Generate script + audio only (no video render, no upload) — fast iteration
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
* Attribution/reuse: even lightly-transformative narration of someone else's Reddit post can raise reuse/copyright questions. Consider crediting the subreddit/author in the description, and check each subreddit's rules on content reuse before scaling this up.
* Caption styling, background clip selection logic, and the thumbnail template are deliberately simple — that's the highest-leverage place to spend manual creative effort since it's what actually drives CTR/retention.
