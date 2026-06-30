from pathlib import Path
from hse.store import Store
from hse.models import parse_when
from hse.scheduler import Scheduler


def test_media_registry_and_local_json(tmp_path: Path):
    media = tmp_path / 'clip.mp4'
    media.write_bytes(b'fake-video')
    s = Store(tmp_path / 'x.db'); s.init()
    pid = s.add_post('local_json', 'caption', parse_when('now'), str(media))
    assert Scheduler(s, tmp_path).run_due() == [(pid, 'posted')]
    events = s.list_events(pid)
    assert any(e['event_type'] == 'media_registered' for e in events)
    assert (tmp_path / 'published' / f'post_{pid}.json').exists()


def test_retry_failed(tmp_path: Path):
    s = Store(tmp_path / 'x.db'); s.init()
    pid = s.add_post('dryrun', '   ', parse_when('now'))
    assert Scheduler(s, tmp_path).run_due() == [(pid, 'failed')]
    assert s.retry_failed(pid) == 1
    assert s.list_posts()[0].status == 'scheduled'
