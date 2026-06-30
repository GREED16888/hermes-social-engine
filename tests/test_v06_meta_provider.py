from pathlib import Path
import json
from unittest.mock import patch

from hse.models import parse_when
from hse.store import Store
from hse.providers.meta import has_app_secret, has_token, token_summary, MetaFacebookProvider


def test_meta_secret_and_token_detection(tmp_path: Path):
    app = tmp_path / 'meta_app.json'
    app.write_text(json.dumps({'app_id': '123', 'app_secret': 'sec'}), encoding='utf-8')
    token = tmp_path / 'meta_token.json'
    token.write_text(json.dumps({'user_access_token': 'ut', 'pages': [{'id':'p1','name':'Page','access_token':'pt'}]}), encoding='utf-8')
    assert has_app_secret(app)
    assert has_token(token)
    assert 'Page' in token_summary(token)


def test_facebook_provider_video_upload_payload(tmp_path: Path):
    token = tmp_path / 'meta_token.json'
    token.write_text(json.dumps({'selected_page_id':'p1','pages':[{'id':'p1','name':'Page','access_token':'pt'}]}), encoding='utf-8')
    video = tmp_path / 'clip.mp4'
    video.write_bytes(b'fake')
    s = Store(tmp_path / 'x.db'); s.init()
    s.add_post('facebook', 'hello video', parse_when('now'), str(video))
    job = s.list_posts()[0]
    with patch('hse.providers.meta._post_video_graph', return_value={'id': 'vid123'}) as mocked:
        result = MetaFacebookProvider(token).publish(job)
    assert result.provider_post_id == 'vid123'
    assert result.release_url == 'https://www.facebook.com/p1/videos/vid123/'
    args = mocked.call_args.args
    assert args[0] == 'p1'
    assert args[1] == 'pt'
    assert args[2] == video
    assert args[3] == 'hello video'
