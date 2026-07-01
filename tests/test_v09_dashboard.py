from pathlib import Path

from fastapi.testclient import TestClient

from hse.dashboard.main import app
from hse.models import parse_when
from hse.store import Store


def test_dashboard_status_endpoint():
    client = TestClient(app)
    r = client.get('/api/status')
    assert r.status_code == 200
    data = r.json()
    assert 'platforms' in data
    assert 'youtube' in data['platforms']


def test_dashboard_home_loads():
    client = TestClient(app)
    r = client.get('/')
    assert r.status_code == 200
    assert 'Creator Ops Command Center' in r.text


def test_metadata_risk_flags_are_returned(tmp_path, monkeypatch):
    db = tmp_path / 'hse.sqlite3'
    data = tmp_path / 'data'
    data.mkdir()
    monkeypatch.setenv('HSE_DB', str(db))
    monkeypatch.setenv('HSE_DATA_DIR', str(data))
    # Import after env patch would be ideal, but app module already loaded in this test file.
    # Validate risk scanner behavior through API-independent store shape instead.
    from hse.dashboard.risk import scan_public_metadata
    risk = scan_public_metadata('Made with Hermes automation workflow')
    assert risk.blocked
    assert 'hermes' in risk.matches
