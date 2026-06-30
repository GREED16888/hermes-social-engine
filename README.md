# Hermes Social Engine

Hermes-first social publishing engine for the user's owned channels. It is built to let Hermes schedule, validate, upload, and log posts across multiple platforms without relying on a third-party UI as the system of record.

> Status: active local project. Real upload verified for YouTube and Facebook Page. TikTok integration is scaffolded and waiting for TikTok Developer App credentials/review.

## Supported platforms

| Platform | Status | Mode | Notes |
|---|---|---|---|
| Telegram | Verified | Real text/photo/video/document post | Uses existing Hermes Telegram credentials. |
| YouTube | Verified | Video upload via YouTube Data API | Safe default: `private`. |
| Facebook Page | Verified | Text post + video upload via Meta Graph API | Primary page configured locally; secrets/tokens are not committed. |
| Instagram | Not connected | Planned | Requires IG Professional/Business account connected to a Facebook Page. |
| TikTok | Scaffolded | OAuth + inbox upload planned | Requires TikTok Developer App, HTTPS redirect, `video.upload`/Content Posting API access. |
| Local JSON / Dry run | Verified | Test providers | Used for safe pipeline verification. |

## Safety model

- No secrets, tokens, OAuth client files, or local SQLite state are committed.
- Upload defaults are conservative: YouTube `private`; TikTok starts with inbox/upload mode before direct public post.
- Every scheduled post has state transitions, event logs, attempt counts, and release URLs.
- Facebook secondary pages require explicit targeting/confirmation before automation.

## Quick start

```bash
cd /mnt/c/Users/LENOVO/Desktop/Ai/03_AI_Projects/Hermes_Social_Engine
uv sync
uv run hse init
uv run hse platform-status
```

Dry run:

```bash
uv run hse add --platform dryrun --content "test post" --when now
uv run hse run-due
uv run hse list
```

## OAuth setup files

Local-only secret files live under `secrets/` and are ignored by git:

```text
secrets/google_oauth_client.json
secrets/meta_app.json
secrets/tiktok_app.json
```

Local-only token/state files live under `data/` and are ignored by git:

```text
data/youtube_token.json
data/meta_token.json
data/tiktok_token.json
data/hse.sqlite3
```

## Platform commands

YouTube:

```bash
uv run hse youtube-auth
uv run hse add --platform youtube --content "Private upload test #shorts" --when now --media-path /path/to/video.mp4
uv run hse run-due
```

Facebook:

```bash
uv run hse meta-template
uv run hse meta-auth
uv run hse add --platform facebook --content "Caption" --when now --media-path /path/to/video.mp4
uv run hse run-due
```

TikTok:

```bash
uv run hse tiktok-template
uv run hse tiktok-auth
uv run hse tiktok-creator-info
uv run hse add --platform tiktok --content "Caption" --when now --media-path /path/to/video.mp4
uv run hse run-due
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Account connection guide](docs/ACCOUNT_CONNECT_GUIDE.md)
- [Meta/TikTok connection plan](docs/META_TIKTOK_CONNECT_PLAN.md)
- [Meta publishing policy](docs/META_PUBLISHING_POLICY.md)
- [Facebook video upload result](docs/FACEBOOK_VIDEO_UPLOAD_RESULT.md)
- [Postiz study](docs/POSTIZ_STUDY.md)
- [Postiz vs HSE decision research](docs/POSTIZ_VS_HSE_DECISION_RESEARCH.md)
- [Privacy Policy](docs/privacy.html)
- [Terms of Service](docs/terms.html)

## License

Personal project. Do not publish credentials or tokens.
