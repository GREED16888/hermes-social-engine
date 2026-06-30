from __future__ import annotations
import json
import mimetypes
import os
import re
import uuid
import urllib.request
from pathlib import Path
from hse.models import PostJob

def _env(name: str) -> str | None:
    if os.getenv(name):
        return os.getenv(name)
    env_path = Path('/root/.hermes/.env')
    if env_path.exists():
        m = re.search(rf'^{re.escape(name)}=(.*)$', env_path.read_text(errors='ignore'), re.M)
        if m:
            return m.group(1).strip().strip('\"').strip("'")
    return None

class TelegramProvider:
    name = 'telegram'
    api_base = 'https://api.telegram.org'

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None, timeout: int = 60):
        self.bot_token = bot_token if bot_token is not None else (_env('HSE_TELEGRAM_BOT_TOKEN') or _env('TELEGRAM_BOT_TOKEN'))
        self.chat_id = chat_id if chat_id is not None else (_env('HSE_TELEGRAM_CHAT_ID') or _env('TELEGRAM_HOME_CHANNEL'))
        self.timeout = timeout

    def validate(self, job: PostJob) -> None:
        if not self.bot_token or not self.chat_id:
            raise RuntimeError('Telegram credentials missing: need TELEGRAM_BOT_TOKEN and TELEGRAM_HOME_CHANNEL or HSE_* equivalents')
        if not job.content.strip() and not job.media_path:
            raise ValueError('content or media_path required')
        if job.media_path and not Path(job.media_path).exists():
            raise FileNotFoundError(job.media_path)

    def publish(self, job: PostJob):
        self.validate(job)
        if job.media_path:
            path = Path(job.media_path)
            mime = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
            if mime.startswith('video/') or path.suffix.lower() in {'.mp4','.mov','.mkv','.webm'}:
                data = self._multipart({'chat_id': self.chat_id, 'caption': job.content[:1024]}, 'video', path, mime)
                endpoint = 'sendVideo'
            elif mime.startswith('image/'):
                data = self._multipart({'chat_id': self.chat_id, 'caption': job.content[:1024]}, 'photo', path, mime)
                endpoint = 'sendPhoto'
            else:
                data = self._multipart({'chat_id': self.chat_id, 'caption': job.content[:1024]}, 'document', path, mime)
                endpoint = 'sendDocument'
            resp = self._post(endpoint, data['body'], data['content_type'])
        else:
            body = urllib.parse.urlencode({'chat_id': self.chat_id, 'text': job.content}).encode('utf-8')
            resp = self._post('sendMessage', body, 'application/x-www-form-urlencoded')
        msg = resp.get('result', {})
        message_id = str(msg.get('message_id', job.id))
        release_url = f'telegram://chat/{self.chat_id}/message/{message_id}'
        class Result:
            pass
        result = Result()
        result.provider_post_id = message_id
        result.release_url = release_url
        return result

    def _post(self, endpoint: str, body: bytes, content_type: str) -> dict:
        url = f'{self.api_base}/bot{self.bot_token}/{endpoint}'
        req = urllib.request.Request(url, data=body, method='POST', headers={'Content-Type': content_type})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            text = r.read().decode('utf-8')
        data = json.loads(text)
        if not data.get('ok'):
            raise RuntimeError(f'Telegram API failed: {data}')
        return data

    def _multipart(self, fields: dict[str, str], file_field: str, path: Path, mime: str) -> dict:
        boundary = '----hse-' + uuid.uuid4().hex
        chunks: list[bytes] = []
        for k, v in fields.items():
            chunks += [f'--{boundary}\r\n'.encode(), f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()]
        chunks += [f'--{boundary}\r\n'.encode(), f'Content-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\n'.encode(), f'Content-Type: {mime}\r\n\r\n'.encode(), path.read_bytes(), b'\r\n', f'--{boundary}--\r\n'.encode()]
        return {'body': b''.join(chunks), 'content_type': f'multipart/form-data; boundary={boundary}'}
