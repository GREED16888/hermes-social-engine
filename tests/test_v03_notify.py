import json
from pathlib import Path
from hse.store import Store
from hse.models import parse_when
from hse.scheduler import Scheduler
from hse.notify import FileNotifier


def test_file_notification_on_success(tmp_path: Path):
    s = Store(tmp_path / 'x.db')
    s.init()
    pid = s.add_post('dryrun', 'hello', parse_when('now'))
    note_path = tmp_path / 'notifications.jsonl'
    assert Scheduler(s, tmp_path, FileNotifier(note_path)).run_due() == [(pid, 'posted')]
    rows = [json.loads(x) for x in note_path.read_text(encoding='utf-8').splitlines()]
    assert rows[0]['level'] == 'success'
    assert rows[0]['post_id'] == pid


def test_file_notification_on_failure(tmp_path: Path):
    s = Store(tmp_path / 'x.db')
    s.init()
    pid = s.add_post('dryrun', '   ', parse_when('now'))
    note_path = tmp_path / 'notifications.jsonl'
    assert Scheduler(s, tmp_path, FileNotifier(note_path)).run_due() == [(pid, 'failed')]
    rows = [json.loads(x) for x in note_path.read_text(encoding='utf-8').splitlines()]
    assert rows[0]['level'] == 'error'
    assert 'content or media_path required' in rows[0]['message']
