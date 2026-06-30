from pathlib import Path
from hse.models import parse_when
from hse.store import Store
from hse.providers.telegram import TelegramProvider


def test_telegram_validation_missing_credentials(tmp_path: Path, monkeypatch):
    monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
    monkeypatch.delenv('TELEGRAM_HOME_CHANNEL', raising=False)
    s = Store(tmp_path / 'x.db'); s.init()
    pid = s.add_post('telegram', 'hello', parse_when('now'))
    job = s.list_posts()[0]
    try:
        TelegramProvider(bot_token='', chat_id='').validate(job)
    except RuntimeError as e:
        assert 'credentials missing' in str(e)
    else:
        raise AssertionError('expected missing credentials error')


def test_telegram_validation_accepts_video(tmp_path: Path):
    media = tmp_path / 'clip.mp4'
    media.write_bytes(b'fake')
    s = Store(tmp_path / 'x.db'); s.init()
    s.add_post('telegram', 'caption', parse_when('now'), str(media))
    TelegramProvider(bot_token='token', chat_id='chat').validate(s.list_posts()[0])
