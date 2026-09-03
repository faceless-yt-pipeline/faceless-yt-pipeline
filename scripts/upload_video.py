"""Upload the rendered video to YouTube.

Setup:
  1. In Google Cloud Console, create a project and enable the "YouTube Data API v3".
  2. Create OAuth 2.0 credentials of type "Desktop app".
  3. Download the JSON and save it as client_secrets.json in the project root
     (see config.YT_CLIENT_SECRETS_FILE).
  4. On first run this opens a browser for you to grant access; the resulting
     token is cached at config.YT_TOKEN_FILE so future runs are unattended.
"""
import logging
from pathlib import Path

import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import config

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials() -> Credentials:
    creds = None
    if config.YT_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(config.YT_TOKEN_FILE), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            if not config.YT_CLIENT_SECRETS_FILE.exists():
                raise RuntimeError(
                    f"Missing {config.YT_CLIENT_SECRETS_FILE}. Download OAuth client_secrets.json "
                    "from Google Cloud Console — see the module docstring in scripts/upload_video.py."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(config.YT_CLIENT_SECRETS_FILE), _SCOPES)
            creds = flow.run_local_server(port=0)
        config.YT_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        config.YT_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return creds


def upload_video(video_path: Path, thumbnail_path: Path, title: str, description: str) -> str:
    """Upload video + thumbnail, return the resulting YouTube video ID."""
    youtube = build("youtube", "v3", credentials=_get_credentials())

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": config.YT_DEFAULT_TAGS,
            "categoryId": config.YT_CATEGORY_ID,
        },
        "status": {"privacyStatus": config.YT_PRIVACY_STATUS},
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info("Upload progress: %d%%", int(status.progress() * 100))

    video_id = response["id"]
    logger.info("Uploaded video https://youtu.be/%s (privacyStatus=%s)", video_id, config.YT_PRIVACY_STATUS)

    if thumbnail_path.exists():
        try:
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumbnail_path))).execute()
            logger.info("Set thumbnail for %s", video_id)
        except HttpError as exc:
            logger.warning(
                "Video uploaded but setting the thumbnail failed (channel may need phone "
                "verification for custom thumbnails — see youtube.com/verify): %s", exc,
            )

    return video_id
