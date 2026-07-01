from pathlib import Path
import json

from hse.accounting import youtube_token_path, validate_account_name
from hse.models import parse_when
from hse.store import Store
from hse.providers import get_provider
from hse.providers.youtube import YouTubeProvider


def test_youtube_account_token_path(tmp_path: Path):
    assert youtube_token_path(tmp_path, "youtube_th") == tmp_path / "tokens" / "youtube" / "youtube_th.json"
    assert youtube_token_path(tmp_path, None) == tmp_path / "youtube_token.json"


def test_invalid_account_name_rejected():
    try:
        validate_account_name("../../bad")
    except ValueError as e:
        assert "account" in str(e)
    else:
        raise AssertionError("invalid account name should fail")


def test_store_persists_post_account(tmp_path: Path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake")
    s = Store(tmp_path / "x.db"); s.init()
    pid = s.add_post("youtube", "Title", parse_when("now"), str(video), account="youtube_th")
    job = s.list_posts()[0]
    assert pid == job.id
    assert job.account == "youtube_th"


def test_store_account_registry(tmp_path: Path):
    s = Store(tmp_path / "x.db"); s.init()
    s.upsert_account("youtube", "youtube_th", label="Thai Channel", language="th", token_path="data/tokens/youtube/youtube_th.json", max_posts_per_day=1)
    rows = s.list_accounts("youtube")
    assert rows[0]["account"] == "youtube_th"
    assert rows[0]["language"] == "th"


def test_get_provider_uses_account_token_path(tmp_path: Path):
    provider = get_provider("youtube", tmp_path, "youtube_en")
    assert isinstance(provider, YouTubeProvider)
    assert provider.token_file == tmp_path / "tokens" / "youtube" / "youtube_en.json"
