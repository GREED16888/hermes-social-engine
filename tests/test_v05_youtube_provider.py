from pathlib import Path
import json
from hse.models import parse_when
from hse.store import Store
from hse.providers.youtube import has_client_secret, has_token, YouTubeProvider


def test_youtube_secret_and_token_detection(tmp_path: Path):
    secret = tmp_path / 'client.json'
    secret.write_text(json.dumps({'installed': {'client_id': 'cid.apps.googleusercontent.com', 'client_secret': 'sec'}}), encoding='utf-8')
    token = tmp_path / 'token.json'
    token.write_text(json.dumps({'refresh_token': 'rt', 'client_id': 'cid', 'client_secret': 'sec'}), encoding='utf-8')
    assert has_client_secret(secret)
    assert has_token(token)


class FakeInsert:
    def execute(self):
        return {'id': 'video123'}

class FakeVideos:
    def __init__(self):
        self.calls = []
    def insert(self, **kwargs):
        self.calls.append(kwargs)
        return FakeInsert()

class FakeYouTube:
    def __init__(self):
        self.v = FakeVideos()
    def videos(self):
        return self.v


def test_youtube_provider_upload_payload_private(tmp_path: Path):
    video = tmp_path / 'clip.mp4'
    video.write_bytes(b'fake')
    token = tmp_path / 'token.json'
    token.write_text(json.dumps({'refresh_token': 'rt', 'client_id': 'cid', 'client_secret': 'sec'}), encoding='utf-8')
    s = Store(tmp_path / 'x.db'); s.init()
    pid = s.add_post('youtube', 'My Shorts Title #shorts', parse_when('now'), str(video))
    job = s.list_posts()[0]
    fake = FakeYouTube()
    result = YouTubeProvider(token, youtube_client=fake).publish(job)
    assert result.provider_post_id == 'video123'
    assert result.release_url == 'https://youtu.be/video123'
    call = fake.v.calls[0]
    assert call['body']['status']['privacyStatus'] == 'private'
    assert call['body']['snippet']['title'] == 'My Shorts Title #shorts'
    assert call['media_body'] == str(video)
