from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

ALLOWED_MIME_PREFIXES = ("image/", "video/")
ALLOWED_EXACT = {"application/octet-stream"}  # fallback for uncommon video mime on WSL


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
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
    mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
    if not (mime.startswith(ALLOWED_MIME_PREFIXES) or mime in ALLOWED_EXACT):
        raise ValueError(f"unsupported media mime: {mime}")
    return {
        "path": str(p),
        "size": p.stat().st_size,
        "mime": mime,
        "sha256": sha256_file(p),
    }


@dataclass(frozen=True)
class MediaAuditResult:
    exact_duplicates: list[tuple[str, str, str]]
    similar_videos: list[tuple[str, str, float]]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.exact_duplicates and not self.similar_videos


def _ffprobe_duration(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    try:
        raw = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
            stderr=subprocess.DEVNULL,
            timeout=20,
        )
        duration = json.loads(raw).get("format", {}).get("duration")
        return float(duration) if duration else None
    except Exception:
        return None


def _average_hash_frame(path: Path, timestamp: float, size: int = 16) -> int | None:
    if not shutil.which("ffmpeg"):
        return None
    try:
        raw = subprocess.check_output(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                f"scale={size}:{size},format=gray",
                "-f",
                "rawvideo",
                "pipe:1",
            ],
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        if len(raw) != size * size:
            return None
        avg = sum(raw) / len(raw)
        bits = 0
        for b in raw:
            bits = (bits << 1) | int(b >= avg)
        return bits
    except Exception:
        return None


def video_perceptual_signature(path: str | Path, samples: int = 5) -> list[int]:
    """Return sampled average hashes for a video; empty list when ffmpeg cannot inspect it."""
    p = Path(path)
    duration = _ffprobe_duration(p)
    if not duration or duration <= 0:
        return []
    # Avoid exact first/last black frames; sample through the body of the clip.
    times = [duration * (i + 1) / (samples + 1) for i in range(samples)]
    hashes: list[int] = []
    for t in times:
        h = _average_hash_frame(p, t)
        if h is not None:
            hashes.append(h)
    return hashes


def _hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def signature_distance(a: list[int], b: list[int]) -> float | None:
    if not a or not b:
        return None
    n = min(len(a), len(b))
    return sum(_hamming(a[i], b[i]) for i in range(n)) / n


def audit_media_batch(paths: list[str | Path], similar_threshold: float = 10.0) -> MediaAuditResult:
    """Detect exact duplicate media and near-identical video files before batch upload.

    `similar_threshold` is average Hamming distance over 16x16 grayscale frame hashes.
    Lower values are stricter; <=10 catches near-identical videos while avoiding most
    unrelated clips.
    """
    warnings: list[str] = []
    infos = [inspect_media(str(p)) for p in paths]
    exact: list[tuple[str, str, str]] = []
    seen: dict[str, str] = {}
    for info in infos:
        if not info:
            continue
        sha = info["sha256"]
        path = info["path"]
        if sha in seen:
            exact.append((seen[sha], path, sha))
        else:
            seen[sha] = path

    similar: list[tuple[str, str, float]] = []
    video_infos = [info for info in infos if info and str(info["mime"]).startswith("video/")]
    signatures: dict[str, list[int]] = {}
    for info in video_infos:
        sig = video_perceptual_signature(info["path"])
        if not sig:
            warnings.append(f"perceptual signature unavailable: {info['path']}")
        signatures[info["path"]] = sig
    for i, left in enumerate(video_infos):
        for right in video_infos[i + 1 :]:
            dist = signature_distance(signatures[left["path"]], signatures[right["path"]])
            if dist is not None and dist <= similar_threshold:
                similar.append((left["path"], right["path"], dist))
    return MediaAuditResult(exact, similar, warnings)
