from pathlib import Path
import json
from unittest.mock import patch

from hse.models import parse_when
from hse.store import Store
from hse.providers.tiktok import has_app_secret, has_token, TikTokProvider


def test_tiktok_secret_and_token_detection(tmp_path: Path):
    app = tmp_path / 'tiktok_app.json'
    app.write_text(json.dumps({'client_key': 'ck', 'client_secret': 'sec'}), encoding='utf-8')
    token = tmp_path / 'tiktok_token.json'
    token.write_text(json.dumps({'access_token':'at','refresh_token':'rt','open_id':'oid'}), encoding='utf-8')
    assert has_app_secret(app)
    assert has_token(token)


def test_tiktok_inbox_upload_payload(tmp_path: Path):
    token = tmp_path / 'tiktok_token.json'
    token.write_text(json.dumps({'access_token':'at','refresh_token':'rt','open_id':'oid'}), encoding='utf-8')
    video = tmp_path / 'clip.mp4'
    video.write_bytes(b'fake')
    s = Store(tmp_path / 'x.db'); s.init()
    s.add_post('tiktok', 'hello tiktok', parse_when('now'), str(video))
    job = s.list_posts()[0]
    with patch('hse.providers.tiktok._request_json_body', return_value={'data': {'upload_url':'https://upload.example','publish_id':'pub123'}}) as req, \
         patch('hse.providers.tiktok._upload_put') as put:
        result = TikTokProvider(token).publish(job)
    assert result.provider_post_id == 'pub123'
    assert result.release_url == 'https://www.tiktok.com/messages?lang=en'
    payload = req.call_args.args[2]
    assert payload['source_info']['source'] == 'FILE_UPLOAD'
    assert payload['source_info']['total_chunk_count'] == 1
    put.assert_called_once()
