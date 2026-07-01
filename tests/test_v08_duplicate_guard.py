from pathlib import Path

import pytest

from hse.media import audit_media_batch
from hse.models import parse_when
from hse.store import Store


def test_store_blocks_exact_duplicate_media_for_same_platform(tmp_path: Path):
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    first.write_bytes(b"same video bytes")
    second.write_bytes(b"same video bytes")

    store = Store(tmp_path / "hse.db")
    store.init()
    store.add_post("youtube", "part 1", parse_when("now"), str(first))

    with pytest.raises(ValueError, match="duplicate media blocked"):
        store.add_post("youtube", "part 2", parse_when("now"), str(second))


def test_store_allows_same_media_on_different_platform(tmp_path: Path):
    media = tmp_path / "clip.mp4"
    media.write_bytes(b"same cross-post bytes")

    store = Store(tmp_path / "hse.db")
    store.init()
    store.add_post("youtube", "caption", parse_when("now"), str(media))
    post_id = store.add_post("facebook", "caption", parse_when("now"), str(media))

    assert post_id == 2


def test_media_audit_detects_exact_duplicate_batch(tmp_path: Path):
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    first.write_bytes(b"same video bytes")
    second.write_bytes(b"same video bytes")

    result = audit_media_batch([first, second])

    assert not result.ok
    assert result.exact_duplicates
    assert result.exact_duplicates[0][0].endswith("first.mp4")
    assert result.exact_duplicates[0][1].endswith("second.mp4")
