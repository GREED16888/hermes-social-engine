from __future__ import annotations

import re
from pathlib import Path

SAFE_ACCOUNT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")


def validate_account_name(account: str | None) -> str | None:
    if account in (None, ""):
        return None
    if not SAFE_ACCOUNT_RE.match(account):
        raise ValueError("account must be 1-64 chars: letters, numbers, _, ., -")
    return account


def youtube_token_path(data_dir: Path, account: str | None = None) -> Path:
    account = validate_account_name(account)
    if account:
        return Path(data_dir) / "tokens" / "youtube" / f"{account}.json"
    return Path(data_dir) / "youtube_token.json"
