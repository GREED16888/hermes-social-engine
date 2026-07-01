from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from hse.models import PostJob
from hse.accounting import youtube_token_path, validate_account_name

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_MANAGE_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_SCOPES = (YOUTUBE_UPLOAD_SCOPE, YOUTUBE_MANAGE_SCOPE)
DEFAULT_ROOT = Path("/mnt/c/Users/LENOVO/Desktop/Ai/03_AI_Projects/Hermes_Social_Engine")
DEFAULT_CLIENT_SECRETS = DEFAULT_ROOT / "secrets" / "google_oauth_client.json"
DEFAULT_TOKEN_FILE = DEFAULT_ROOT / "data" / "youtube_token.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def has_client_secret(path: Path = DEFAULT_CLIENT_SECRETS) -> bool:
    try:
        data = _load_json(path)
        return bool(data.get("installed", {}).get("client_id") and data.get("installed", {}).get("client_secret"))
    except Exception:
        return False


def account_token_file(account: str | None = None, data_dir: Path | None = None) -> Path:
    return youtube_token_path(data_dir or (DEFAULT_ROOT / "data"), account)


def has_token(path: Path = DEFAULT_TOKEN_FILE) -> bool:
    try:
        data = _load_json(path)
        return bool(data.get("refresh_token") and data.get("client_id") and data.get("client_secret"))
    except Exception:
        return False


def client_id_preview(path: Path = DEFAULT_CLIENT_SECRETS) -> str:
    data = _load_json(path)
    cid = data.get("installed", {}).get("client_id", "")
    if not cid:
        return "missing"
    return cid[:18] + "..."


def run_oauth_local_server(
    client_secrets: Path = DEFAULT_CLIENT_SECRETS,
    token_file: Path = DEFAULT_TOKEN_FILE,
    port: int = 8088,
    scopes: Iterable[str] = YOUTUBE_SCOPES,
) -> Path:
    """Run Google installed-app OAuth and persist refresh token.

    This starts a localhost callback server. The user must approve in their browser.
    The saved token file contains secrets and must not be committed.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_secrets = Path(client_secrets)
    token_file = Path(token_file)
    token_file.parent.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), scopes=list(scopes))
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=port,
        authorization_prompt_message="AUTH_URL: {url}",
        success_message="Hermes Social Engine YouTube OAuth complete. You can close this tab.",
        open_browser=False,
        prompt="consent",
        access_type="offline",
    )
    payload = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or scopes),
    }
    token_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(token_file, 0o600)
    except OSError:
        pass
    return token_file


def credentials_from_token(token_file: Path = DEFAULT_TOKEN_FILE):
    from google.oauth2.credentials import Credentials
    data = _load_json(Path(token_file))
    return Credentials.from_authorized_user_info(data, scopes=list(data.get("scopes") or YOUTUBE_SCOPES))


def channel_identity(token_file: Path = DEFAULT_TOKEN_FILE) -> dict:
    """Read the authorized channel identity without exposing token data."""
    from googleapiclient.discovery import build
    creds = credentials_from_token(token_file)
    service = build("youtube", "v3", credentials=creds)
    resp = service.channels().list(part="id,snippet", mine=True).execute()
    items = resp.get("items") or []
    if not items:
        return {"channel_id": None, "title": None}
    item = items[0]
    return {"channel_id": item.get("id"), "title": (item.get("snippet") or {}).get("title")}


class YouTubeProvider:
    name = "youtube"

    def __init__(self, token_file: Path = DEFAULT_TOKEN_FILE, youtube_client=None):
        self.token_file = Path(token_file)
        self._youtube_client = youtube_client

    def validate(self, job: PostJob) -> None:
        if not self.token_file.exists():
            raise RuntimeError(f"YouTube token missing: run `youtube-auth` first ({self.token_file})")
        if not job.media_path:
            raise ValueError("YouTube upload requires --media-path video file")
        path = Path(job.media_path)
        if not path.exists():
            raise FileNotFoundError(job.media_path)
        if path.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm", ".avi", ".mpeg", ".mpg"}:
            raise ValueError(f"Unsupported YouTube video extension: {path.suffix}")
        if not job.content.strip():
            raise ValueError("YouTube upload requires title/content")

    def publish(self, job: PostJob):
        self.validate(job)
        path = Path(job.media_path)
        youtube = self._youtube_client or self._build_youtube_client()
        body = {
            "snippet": {
                "title": job.content.strip()[:100],
                "description": job.content.strip(),
                "categoryId": "22",
            },
            "status": {
                # Safe default: never publish publicly until user explicitly changes policy.
                "privacyStatus": os.getenv("HSE_YOUTUBE_PRIVACY", "private"),
                "selfDeclaredMadeForKids": False,
            },
        }
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=str(path),
        )
        response = request.execute()
        video_id = response.get("id")
        if not video_id:
            raise RuntimeError(f"YouTube API response missing video id: {response}")
        class Result:
            pass
        result = Result()
        result.provider_post_id = video_id
        result.release_url = f"https://youtu.be/{video_id}"
        return result

    def _build_youtube_client(self):
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        # Patch media_body from string into MediaFileUpload by wrapping the videos().insert call.
        creds = credentials_from_token(self.token_file)
        service = build("youtube", "v3", credentials=creds)
        original_videos = service.videos

        class VideosWrapper:
            def __init__(self, videos):
                self._videos = videos
            def insert(self, part, body, media_body):
                return self._videos.insert(
                    part=part,
                    body=body,
                    media_body=MediaFileUpload(media_body, chunksize=-1, resumable=True),
                )
        class ServiceWrapper:
            def videos(self):
                return VideosWrapper(original_videos())
        return ServiceWrapper()
