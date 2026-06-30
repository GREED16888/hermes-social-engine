from __future__ import annotations

import json
import os
import secrets
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

from hse.models import PostJob

DEFAULT_ROOT = Path("/mnt/c/Users/LENOVO/Desktop/Ai/03_AI_Projects/Hermes_Social_Engine")
DEFAULT_TIKTOK_APP = DEFAULT_ROOT / "secrets" / "tiktok_app.json"
DEFAULT_TIKTOK_TOKEN = DEFAULT_ROOT / "data" / "tiktok_token.json"
TIKTOK_SCOPES = [
    "user.info.basic",
    "user.info.profile",
    "user.info.stats",
    "video.upload",
    "video.publish",
    "video.list",
]


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_private_json(path: Path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def has_app_secret(path: Path = DEFAULT_TIKTOK_APP) -> bool:
    try:
        data = _load_json(path)
        client_key = str(data.get("client_key", "")).strip()
        client_secret = str(data.get("client_secret", "")).strip()
        return bool(client_key and client_secret and client_secret != "PASTE_TIKTOK_CLIENT_SECRET_HERE")
    except Exception:
        return False


def has_token(path: Path = DEFAULT_TIKTOK_TOKEN) -> bool:
    try:
        data = _load_json(path)
        return bool(data.get("access_token") and data.get("refresh_token") and data.get("open_id"))
    except Exception:
        return False


def build_app_template(path: Path = DEFAULT_TIKTOK_APP) -> Path:
    path = Path(path)
    data = _load_json(path) if path.exists() else {}
    data.setdefault("client_key", "PASTE_TIKTOK_CLIENT_KEY_HERE")
    data.setdefault("client_secret", "PASTE_TIKTOK_CLIENT_SECRET_HERE")
    data.setdefault("redirect_uri", "https://greed16888.github.io/hermes-social-engine/tiktok-callback.html")
    data.setdefault("upload_mode", "inbox")
    _write_private_json(path, data)
    return path


def client_key_preview(path: Path = DEFAULT_TIKTOK_APP) -> str:
    try:
        key = str(_load_json(path).get("client_key", ""))
    except Exception:
        return "missing"
    if not key or key == "PASTE_TIKTOK_CLIENT_KEY_HERE":
        return "missing"
    return key[:8] + "..."


def _request_json(url: str, method: str = "GET", data: Optional[dict] = None, headers: Optional[dict] = None) -> dict:
    body = None
    headers = dict(headers or {})
    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            raw = res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok API HTTP {e.code}: {raw}") from e
    payload = json.loads(raw)
    if isinstance(payload, dict) and payload.get("error") and payload.get("error") != "ok":
        raise RuntimeError(f"TikTok API error: {payload}")
    return payload


def _request_json_body(url: str, access_token: str, data: dict) -> dict:
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            raw = res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok API HTTP {e.code}: {raw}") from e
    payload = json.loads(raw)
    if payload.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok API error: {payload}")
    return payload


class _CallbackHandler(BaseHTTPRequestHandler):
    server_version = "HSETikTokOAuth/1.0"
    def log_message(self, fmt, *args):
        return
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        self.server.oauth_query = qs  # type: ignore[attr-defined]
        if "code" in qs:
            msg = "Hermes Social Engine TikTok OAuth complete. You can close this tab."
            self.send_response(200)
        else:
            msg = "Hermes Social Engine TikTok OAuth failed. Return to Telegram."
            self.send_response(400)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(msg.encode("utf-8"))


def run_oauth_local_server(app_file: Path = DEFAULT_TIKTOK_APP, token_file: Path = DEFAULT_TIKTOK_TOKEN, port: int = 8090) -> Path:
    app = _load_json(app_file)
    client_key = str(app.get("client_key", "")).strip()
    client_secret = str(app.get("client_secret", "")).strip()
    if not client_key or not client_secret or client_secret == "PASTE_TIKTOK_CLIENT_SECRET_HERE":
        raise RuntimeError(f"TikTok app credentials missing. Edit {app_file} first.")
    redirect_uri = str(app.get("redirect_uri") or f"http://localhost:{port}/")
    state = secrets.token_urlsafe(24)
    auth_params = {
        "client_key": client_key,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
        "scope": ",".join(TIKTOK_SCOPES),
    }
    auth_url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(auth_params)
    print(f"AUTH_URL: {auth_url}", flush=True)
    server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
    server.timeout = 600
    server.oauth_query = {}  # type: ignore[attr-defined]
    qs = {}
    for _ in range(20):
        server.handle_request()
        current = dict(server.oauth_query)  # type: ignore[attr-defined]
        if current.get("state", [None])[0] == state and ("code" in current or "error" in current):
            qs = current
            break
        print(f"IGNORED_CALLBACK state_mismatch_or_missing keys={sorted(current.keys())}", flush=True)
    if not qs:
        raise RuntimeError("TikTok OAuth callback not received with matching state; use latest AUTH_URL")
    if "error" in qs:
        raise RuntimeError(f"TikTok OAuth error: {qs}")
    code = qs.get("code", [None])[0]
    if not code:
        raise RuntimeError(f"TikTok OAuth missing code: {qs}")

    token = _request_json(
        "https://open.tiktokapis.com/v2/oauth/token/",
        method="POST",
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )
    access_token = token.get("access_token")
    if not access_token:
        raise RuntimeError(f"TikTok token response missing access_token: {token}")
    user = _request_json(
        "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name,username",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    payload = {
        "client_key": client_key,
        "access_token": access_token,
        "refresh_token": token.get("refresh_token"),
        "expires_in": token.get("expires_in"),
        "refresh_expires_in": token.get("refresh_expires_in"),
        "scope": token.get("scope"),
        "open_id": (user.get("data", {}).get("user", {}) or {}).get("open_id") or token.get("open_id"),
        "user": user.get("data", {}).get("user", {}),
    }
    _write_private_json(token_file, payload)
    return Path(token_file)


def exchange_auth_code(code: str, app_file: Path = DEFAULT_TIKTOK_APP, token_file: Path = DEFAULT_TIKTOK_TOKEN) -> Path:
    app = _load_json(app_file)
    client_key = str(app.get("client_key", "")).strip()
    client_secret = str(app.get("client_secret", "")).strip()
    redirect_uri = str(app.get("redirect_uri") or "https://greed16888.github.io/hermes-social-engine/tiktok-callback.html")
    if not client_key or not client_secret or client_secret == "PASTE_TIKTOK_CLIENT_SECRET_HERE":
        raise RuntimeError(f"TikTok app credentials missing. Edit {app_file} first.")
    token = _request_json(
        "https://open.tiktokapis.com/v2/oauth/token/",
        method="POST",
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )
    access_token = token.get("access_token")
    if not access_token:
        raise RuntimeError(f"TikTok token response missing access_token: {token}")
    user = _request_json(
        "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name,username",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    payload = {
        "client_key": client_key,
        "access_token": access_token,
        "refresh_token": token.get("refresh_token"),
        "expires_in": token.get("expires_in"),
        "refresh_expires_in": token.get("refresh_expires_in"),
        "scope": token.get("scope"),
        "open_id": (user.get("data", {}).get("user", {}) or {}).get("open_id") or token.get("open_id"),
        "user": user.get("data", {}).get("user", {}),
    }
    _write_private_json(token_file, payload)
    return Path(token_file)

def token_summary(token_file: Path = DEFAULT_TIKTOK_TOKEN) -> str:
    data = _load_json(token_file)
    user = data.get("user", {}) or {}
    return "\n".join([
        f"display_name={user.get('display_name')}",
        f"username={user.get('username')}",
        f"open_id={data.get('open_id')}",
        f"scope={data.get('scope')}",
    ])


def creator_info(token_file: Path = DEFAULT_TIKTOK_TOKEN) -> dict:
    access = _load_json(token_file)["access_token"]
    return _request_json_body(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/",
        access,
        {},
    )


def _upload_put(upload_url: str, video_path: Path) -> None:
    data = Path(video_path).read_bytes()
    req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(len(data)),
            "Content-Range": f"bytes 0-{len(data)-1}/{len(data)}",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as res:
            res.read()
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"TikTok upload PUT HTTP {e.code}: {raw}") from e


class TikTokProvider:
    name = "tiktok"
    def __init__(self, token_file: Path = DEFAULT_TIKTOK_TOKEN):
        self.token_file = Path(token_file)

    def validate(self, job: PostJob) -> None:
        if not self.token_file.exists():
            raise RuntimeError(f"TikTok token missing: run `tiktok-auth` first ({self.token_file})")
        if not job.media_path:
            raise ValueError("TikTok upload requires --media-path video file")
        path = Path(job.media_path)
        if not path.exists():
            raise FileNotFoundError(job.media_path)
        if path.suffix.lower() != ".mp4":
            raise ValueError("TikTok MVP supports .mp4 only")
        if not job.content.strip():
            raise ValueError("TikTok upload requires caption/content")

    def publish(self, job: PostJob):
        self.validate(job)
        token = _load_json(self.token_file)
        access = token["access_token"]
        path = Path(job.media_path)
        total = path.stat().st_size
        init = _request_json_body(
            "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
            access,
            {
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": total,
                    "chunk_size": total,
                    "total_chunk_count": 1,
                },
            },
        )
        data = init.get("data", {})
        upload_url = data.get("upload_url")
        publish_id = data.get("publish_id")
        if not upload_url or not publish_id:
            raise RuntimeError(f"TikTok init response missing upload_url/publish_id: {init}")
        _upload_put(upload_url, path)
        class Result:
            pass
        result = Result()
        result.provider_post_id = publish_id
        # Inbox upload requires user to finish in TikTok app; safer than public direct-post.
        result.release_url = "https://www.tiktok.com/messages?lang=en"
        return result
