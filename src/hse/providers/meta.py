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
DEFAULT_META_APP = DEFAULT_ROOT / "secrets" / "meta_app.json"
DEFAULT_META_TOKEN = DEFAULT_ROOT / "data" / "meta_token.json"
META_GRAPH_VERSION = os.getenv("HSE_META_GRAPH_VERSION", "v20.0")
META_OAUTH_SCOPES = [
    "public_profile",
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_metadata",
    "pages_manage_posts",
    "business_management",
    "instagram_basic",
    "instagram_content_publish",
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


def has_app_secret(path: Path = DEFAULT_META_APP) -> bool:
    try:
        data = _load_json(path)
        app_id = str(data.get("app_id", "")).strip()
        app_secret = str(data.get("app_secret", "")).strip()
        return bool(app_id and app_secret and app_secret != "PASTE_META_APP_SECRET_HERE")
    except Exception:
        return False


def has_token(path: Path = DEFAULT_META_TOKEN) -> bool:
    try:
        data = _load_json(path)
        return bool(data.get("user_access_token") and data.get("pages"))
    except Exception:
        return False


def app_id_preview(path: Path = DEFAULT_META_APP) -> str:
    try:
        app_id = str(_load_json(path).get("app_id", ""))
    except Exception:
        return "missing"
    return app_id[:8] + "..." if app_id else "missing"


def build_app_template(path: Path = DEFAULT_META_APP, app_id: str = "1464342022114588") -> Path:
    path = Path(path)
    if path.exists():
        data = _load_json(path)
    else:
        data = {}
    data.setdefault("app_id", app_id)
    data.setdefault("app_secret", "PASTE_META_APP_SECRET_HERE")
    data.setdefault("redirect_uri", "http://localhost:8089/")
    _write_private_json(path, data)
    return path


def _request_json(url: str, data: Optional[dict] = None) -> dict:
    encoded = None
    headers = {}
    if data is not None:
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=encoded, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            body = res.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise RuntimeError(f"Meta API HTTP {e.code}: {body}") from e
    payload = json.loads(body)
    if isinstance(payload, dict) and payload.get("error"):
        raise RuntimeError(f"Meta API error: {payload['error']}")
    return payload


def _graph(path: str, access_token: str, params: Optional[dict] = None) -> dict:
    params = dict(params or {})
    params["access_token"] = access_token
    url = f"https://graph.facebook.com/{META_GRAPH_VERSION}/{path.lstrip('/')}?{urllib.parse.urlencode(params)}"
    return _request_json(url)


def _post_graph(path: str, access_token: str, params: Optional[dict] = None) -> dict:
    params = dict(params or {})
    params["access_token"] = access_token
    url = f"https://graph.facebook.com/{META_GRAPH_VERSION}/{path.lstrip('/')}"
    return _request_json(url, params)


def _post_video_graph(page_id: str, access_token: str, video_path: Path, description: str) -> dict:
    import requests

    url = f"https://graph.facebook.com/{META_GRAPH_VERSION}/{page_id}/videos"
    data = {
        "access_token": access_token,
        "description": description,
        "title": (description.strip().splitlines()[0] or "Hermes Social Engine video")[:100],
        "published": "true",
    }
    with Path(video_path).open("rb") as fh:
        files = {"source": (Path(video_path).name, fh, "video/mp4")}
        res = requests.post(url, data=data, files=files, timeout=300)
    try:
        payload = res.json()
    except Exception:
        payload = {"raw": res.text}
    if res.status_code >= 400 or (isinstance(payload, dict) and payload.get("error")):
        raise RuntimeError(f"Meta video upload HTTP {res.status_code}: {payload}")
    return payload


class _CallbackHandler(BaseHTTPRequestHandler):
    server_version = "HSEMetaOAuth/1.0"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        self.server.oauth_query = qs  # type: ignore[attr-defined]
        if "code" in qs:
            msg = "Hermes Social Engine Meta OAuth complete. You can close this tab."
            self.send_response(200)
        else:
            msg = "Hermes Social Engine Meta OAuth failed. Return to Telegram."
            self.send_response(400)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(msg.encode("utf-8"))


def run_oauth_local_server(app_file: Path = DEFAULT_META_APP, token_file: Path = DEFAULT_META_TOKEN, port: int = 8089) -> Path:
    app = _load_json(app_file)
    app_id = str(app.get("app_id", "")).strip()
    app_secret = str(app.get("app_secret", "")).strip()
    if not app_id or not app_secret or app_secret == "PASTE_META_APP_SECRET_HERE":
        raise RuntimeError(f"Meta app secret missing. Edit {app_file} first.")
    redirect_uri = str(app.get("redirect_uri") or f"http://localhost:{port}/")
    state = secrets.token_urlsafe(24)
    auth_params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
        "scope": ",".join(META_OAUTH_SCOPES),
        "auth_type": "rerequest",
    }
    auth_url = "https://www.facebook.com/v20.0/dialog/oauth?" + urllib.parse.urlencode(auth_params)
    print(f"AUTH_URL: {auth_url}", flush=True)
    server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
    server.timeout = 600
    server.oauth_query = {}  # type: ignore[attr-defined]
    qs = {}
    # Browsers can hit localhost with favicon/probe/stale callbacks. Ignore anything
    # that does not contain the exact OAuth state and wait for the real callback.
    for _ in range(20):
        server.handle_request()
        current = dict(server.oauth_query)  # type: ignore[attr-defined]
        if current.get("state", [None])[0] == state and ("code" in current or "error" in current):
            qs = current
            break
        print(f"IGNORED_CALLBACK state_mismatch_or_missing keys={sorted(current.keys())}", flush=True)
    if not qs:
        raise RuntimeError("OAuth callback not received with matching state; use the latest AUTH_URL from this run")
    if "error" in qs:
        raise RuntimeError(f"Meta OAuth error: {qs}")
    code = qs.get("code", [None])[0]
    if not code:
        raise RuntimeError(f"Meta OAuth missing code: {qs}")

    token_url = "https://graph.facebook.com/v20.0/oauth/access_token?" + urllib.parse.urlencode({
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "client_secret": app_secret,
        "code": code,
    })
    short = _request_json(token_url)
    short_token = short["access_token"]

    long_url = "https://graph.facebook.com/v20.0/oauth/access_token?" + urllib.parse.urlencode({
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    })
    long_payload = _request_json(long_url)
    user_token = long_payload.get("access_token", short_token)

    me = _graph("me", user_token, {"fields": "id,name"})
    accounts = _graph("me/accounts", user_token, {"fields": "id,name,access_token,instagram_business_account{id,username,name}"})
    pages = accounts.get("data", [])
    payload = {
        "app_id": app_id,
        "user_id": me.get("id"),
        "user_name": me.get("name"),
        "user_access_token": user_token,
        "expires_in": long_payload.get("expires_in"),
        "pages": pages,
        "selected_page_id": pages[0]["id"] if pages else None,
        "selected_page_name": pages[0]["name"] if pages else None,
        "selected_ig_user_id": (pages[0].get("instagram_business_account") or {}).get("id") if pages else None,
    }
    _write_private_json(token_file, payload)
    return Path(token_file)


def token_summary(token_file: Path = DEFAULT_META_TOKEN) -> str:
    data = _load_json(token_file)
    lines = [f"user={data.get('user_name')} ({data.get('user_id')})"]
    for i, p in enumerate(data.get("pages", []), 1):
        ig = p.get("instagram_business_account") or {}
        suffix = f" | IG={ig.get('username') or ig.get('id')}" if ig else " | IG=not_connected"
        selected = " *selected*" if p.get("id") == data.get("selected_page_id") else ""
        lines.append(f"{i}. page={p.get('name')} ({p.get('id')}){suffix}{selected}")
    return "\n".join(lines)


def selected_page(token_file: Path = DEFAULT_META_TOKEN) -> dict:
    data = _load_json(token_file)
    sid = data.get("selected_page_id")
    pages = data.get("pages", [])
    for p in pages:
        if p.get("id") == sid:
            return p
    if pages:
        return pages[0]
    raise RuntimeError("No Facebook Pages found in Meta token. Check Page admin role and permissions.")


class MetaFacebookProvider:
    name = "facebook"

    def __init__(self, token_file: Path = DEFAULT_META_TOKEN):
        self.token_file = Path(token_file)

    def validate(self, job: PostJob) -> None:
        if not self.token_file.exists():
            raise RuntimeError(f"Meta token missing: run `meta-auth` first ({self.token_file})")
        if not job.content.strip() and not job.media_path:
            raise ValueError("Facebook post requires content or --media-path")
        if job.media_path and not Path(job.media_path).exists():
            raise FileNotFoundError(job.media_path)

    def publish(self, job: PostJob):
        self.validate(job)
        page = selected_page(self.token_file)
        page_id = page["id"]
        token = page["access_token"]
        if job.media_path:
            path = Path(job.media_path)
            if path.suffix.lower() not in {".mp4", ".mov", ".m4v"}:
                raise ValueError(f"Unsupported Facebook video extension: {path.suffix}")
            response = _post_video_graph(page_id, token, path, job.content.strip())
            post_id = response.get("id")
            if not post_id:
                raise RuntimeError(f"Facebook video response missing id: {response}")
            class Result:
                pass
            result = Result()
            result.provider_post_id = post_id
            result.release_url = f"https://www.facebook.com/{page_id}/videos/{post_id}/"
            return result

        response = _post_graph(f"{page_id}/feed", token, {"message": job.content.strip()})
        post_id = response.get("id")
        if not post_id:
            raise RuntimeError(f"Facebook response missing post id: {response}")
        class Result:
            pass
        result = Result()
        result.provider_post_id = post_id
        result.release_url = f"https://www.facebook.com/{post_id}"
        return result
