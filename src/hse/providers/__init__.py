from pathlib import Path
from .telegram import TelegramProvider
from .youtube import YouTubeProvider, has_client_secret as youtube_has_client_secret, has_token as youtube_has_token, account_token_file
from .meta import MetaFacebookProvider, has_app_secret as meta_has_app_secret, has_token as meta_has_token
from .tiktok import TikTokProvider, has_app_secret as tiktok_has_app_secret, has_token as tiktok_has_token

class Result:
    def __init__(self,pid,url): self.provider_post_id=pid; self.release_url=url
class DryRun:
    def publish(self,job):
        if not job.content.strip() and not job.media_path: raise ValueError("content or media_path required")
        return Result(f"dryrun-{job.id}", f"dryrun://post/{job.id}")
class LocalJson:
    def __init__(self,out): self.out=Path(out); self.out.mkdir(parents=True,exist_ok=True)
    def publish(self,job):
        import json
        if not job.content.strip() and not job.media_path: raise ValueError("content or media_path required")
        p=self.out/f"post_{job.id}.json"; p.write_text(json.dumps({"id":job.id,"platform":job.platform,"content":job.content,"media_path":job.media_path},ensure_ascii=False,indent=2),encoding="utf-8")
        return Result(f"local-{job.id}", str(p))
def get_provider(name,data_dir,account=None):
    if name=="dryrun": return DryRun()
    if name=="local_json": return LocalJson(Path(data_dir)/"published")
    if name=="telegram": return TelegramProvider()
    if name=="youtube": return YouTubeProvider(account_token_file(account, Path(data_dir)))
    if name=="facebook": return MetaFacebookProvider()
    if name=="tiktok": return TikTokProvider()
    raise KeyError(f"Unknown provider: {name}")
def credential_status():
    import os
    from .telegram import _env
    return {
        'telegram': bool((_env('HSE_TELEGRAM_BOT_TOKEN') or _env('TELEGRAM_BOT_TOKEN')) and (_env('HSE_TELEGRAM_CHAT_ID') or _env('TELEGRAM_HOME_CHANNEL'))),
        'youtube_client': youtube_has_client_secret(),
        'youtube_token': youtube_has_token(),
        'youtube': youtube_has_client_secret() and youtube_has_token(),
        'meta_app': meta_has_app_secret(),
        'meta_token': meta_has_token(),
        'facebook': meta_has_app_secret() and meta_has_token(),
        'tiktok_app': tiktok_has_app_secret(),
        'tiktok_token': tiktok_has_token(),
        'tiktok': tiktok_has_app_secret() and tiktok_has_token(),
    }
