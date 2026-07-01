from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
STATUS_SCHEDULED="scheduled"
STATUS_PUBLISHING="publishing"
def utcnow(): return datetime.now(timezone.utc)
def parse_when(v:str):
    v=v.strip()
    if v.lower()=="now": return utcnow()
    if v.endswith("Z"): v=v[:-1]+"+00:00"
    d=datetime.fromisoformat(v)
    if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)
@dataclass(frozen=True)
class PostJob:
    id:int; platform:str; content:str; scheduled_at:datetime; status:str; media_path:Optional[str]=None; provider_post_id:Optional[str]=None; release_url:Optional[str]=None; attempts:int=0; last_error:Optional[str]=None; account:Optional[str]=None
