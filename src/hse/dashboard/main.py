from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from hse.providers import credential_status
from hse.store import Store
from .risk import scan_public_metadata

PROJECT_ROOT = Path(os.environ.get("HSE_ROOT", "/mnt/c/Users/LENOVO/Desktop/Ai/03_AI_Projects/Hermes_Social_Engine"))
DATA_DIR = Path(os.environ.get("HSE_DATA_DIR", PROJECT_ROOT / "data"))
DB_PATH = Path(os.environ.get("HSE_DB", DATA_DIR / "hse.sqlite3"))
STATIC_DIR = Path(__file__).with_name("static")

app = FastAPI(title="HSE Creator Ops Dashboard", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    store = Store(DB_PATH)
    store.init()
    store.conn.close()


def _connect() -> sqlite3.Connection:
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _load_latest_json_report(prefix: str) -> dict[str, Any] | None:
    docs = PROJECT_ROOT / "docs"
    if not docs.exists():
        return None
    candidates = sorted(docs.glob(f"{prefix}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return {"path": str(path), "payload": payload}
        except Exception:
            continue
    return None


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/status")
def api_status() -> dict[str, Any]:
    creds = credential_status()
    platforms = {
        "telegram": {"ready": creds.get("telegram", False), "label": "Telegram alerts"},
        "youtube": {"ready": creds.get("youtube", False), "label": "YouTube upload/schedule"},
        "facebook": {"ready": creds.get("facebook", False), "label": "Facebook Page publish"},
        "tiktok": {"ready": creds.get("tiktok", False), "label": "TikTok content posting", "note": "App in review / token pending"},
        "instagram": {"ready": False, "label": "Instagram", "note": "Not connected"},
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_path": str(DB_PATH),
        "project_root": str(PROJECT_ROOT),
        "platforms": platforms,
    }


@app.get("/api/accounts")
def api_accounts(platform: str | None = None) -> dict[str, Any]:
    conn = _connect()
    try:
        if platform:
            rows = conn.execute("SELECT * FROM accounts WHERE platform=? ORDER BY platform, account", (platform,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM accounts ORDER BY platform, account").fetchall()
        accounts = []
        for row in rows:
            account = _row_dict(row)
            # Do not expose absolute token paths in the browser; show only readiness and filename.
            token_path = account.get("token_path")
            account["token_file"] = Path(token_path).name if token_path else None
            account["token_ready"] = bool(token_path and Path(token_path).exists())
            account.pop("token_path", None)
            accounts.append(account)
        return {"accounts": accounts, "count": len(accounts)}
    finally:
        conn.close()


@app.get("/api/posts")
def api_posts(limit: int = 100) -> dict[str, Any]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM posts ORDER BY scheduled_at DESC, id DESC LIMIT ?", (min(limit, 500),)
        ).fetchall()
        posts: list[dict[str, Any]] = []
        for row in rows:
            post = _row_dict(row)
            post["metadata_risk"] = scan_public_metadata(post.get("content") or "").__dict__
            posts.append(post)
        return {"posts": posts, "count": len(posts)}
    finally:
        conn.close()


@app.get("/api/overview")
def api_overview() -> dict[str, Any]:
    conn = _connect()
    try:
        status_counts = {r["status"]: r["count"] for r in conn.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")}
        platform_counts = {r["platform"]: r["count"] for r in conn.execute("SELECT platform, COUNT(*) as count FROM posts GROUP BY platform")}
        event_count = conn.execute("SELECT COUNT(*) as count FROM events").fetchone()["count"]
        media_count = conn.execute("SELECT COUNT(*) as count FROM media").fetchone()["count"]
        posts = conn.execute("SELECT id, platform, content, media_path, status, scheduled_at, release_url FROM posts ORDER BY id DESC LIMIT 10").fetchall()
        risks = []
        for row in posts:
            risk = scan_public_metadata(row["content"] or "")
            if risk.blocked:
                risks.append({"post_id": row["id"], "matches": risk.matches, "content": row["content"]})
        return {
            "status_counts": status_counts,
            "platform_counts": platform_counts,
            "event_count": event_count,
            "media_count": media_count,
            "risk_flags": risks,
            "reports": {
                "youtube_shorts": _load_latest_json_report("YOUTUBE_SHORTS"),
                "facebook_video": str(PROJECT_ROOT / "docs" / "FACEBOOK_VIDEO_UPLOAD_RESULT.md"),
                "tiktok_review": str(PROJECT_ROOT / "docs" / "AGY_DASHBOARD_REVIEW_2026-07-02.md"),
            },
        }
    finally:
        conn.close()


@app.get("/api/revenue")
def api_revenue() -> dict[str, Any]:
    # V1 is import-ready and honest: no fake revenue numbers.
    return {
        "total_revenue": 0,
        "currency": "THB",
        "source_status": {
            "youtube_adsense": "not_connected",
            "tiktok_shop": "csv_or_api_pending",
            "facebook_bonus": "not_connected",
            "manual_csv_import": "planned",
        },
        "message": "Revenue layer is ready for collectors/imports; no fabricated revenue is shown.",
    }


@app.get("/api/media")
def api_media(limit: int = 100) -> dict[str, Any]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM media ORDER BY id DESC LIMIT ?", (min(limit, 500),)).fetchall()
        return {"media": [_row_dict(r) for r in rows], "count": len(rows)}
    finally:
        conn.close()


@app.get("/api/post/{post_id}")
def api_post(post_id: int) -> dict[str, Any]:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="post not found")
        events = conn.execute("SELECT * FROM events WHERE post_id=? ORDER BY id", (post_id,)).fetchall()
        return {"post": _row_dict(row), "events": [_row_dict(e) for e in events]}
    finally:
        conn.close()
