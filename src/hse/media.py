from __future__ import annotations
import hashlib
import mimetypes
from pathlib import Path

ALLOWED_MIME_PREFIXES = ("image/", "video/")
ALLOWED_EXACT = {"application/octet-stream"}  # fallback for uncommon video mime on WSL


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def inspect_media(path: str | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    if not p.is_file():
        raise ValueError(f"media_path is not a file: {p}")
    mime = mimetypes.guess_type(str(p))[0] or 'application/octet-stream'
    if not (mime.startswith(ALLOWED_MIME_PREFIXES) or mime in ALLOWED_EXACT):
        raise ValueError(f"unsupported media mime: {mime}")
    return {
        'path': str(p),
        'size': p.stat().st_size,
        'mime': mime,
        'sha256': sha256_file(p),
    }
