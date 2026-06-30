from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

NotificationLevel = Literal['info', 'success', 'warning', 'error']

@dataclass(frozen=True)
class Notification:
    level: NotificationLevel
    title: str
    message: str
    post_id: int | None = None

class FileNotifier:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, note: Notification) -> None:
        payload = {
            'level': note.level,
            'title': note.title,
            'message': note.message,
            'post_id': note.post_id,
        }
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False) + '\n')

class NullNotifier:
    def send(self, note: Notification) -> None:
        return None

def build_notifier(data_dir: Path, mode: str | None = None):
    mode = (mode or 'file').lower()
    if mode == 'none':
        return NullNotifier()
    if mode == 'file':
        return FileNotifier(Path(data_dir) / 'notifications.jsonl')
    raise ValueError(f'Unknown notification mode: {mode}')
