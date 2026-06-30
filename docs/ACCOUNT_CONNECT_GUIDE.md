# Account Connect Guide — Hermes Social Engine

Status checked:

```text
telegram=ready
youtube=missing_credentials
tiktok=missing_credentials
meta=missing_credentials
```

## What this means

Hermes Social Engine can already post real clips to Telegram because Hermes already has Telegram bot credentials.

For YouTube, TikTok, Facebook, and Instagram, the user must connect accounts through official developer/OAuth flows. No tool can bypass this.

## Recommended order

1. YouTube Shorts
2. Facebook Page / Instagram Reels
3. TikTok

## YouTube connection

Needed:

- Google Cloud project
- YouTube Data API v3 enabled
- OAuth consent screen
- OAuth Client ID type: Web application or Desktop app
- scopes:
  - `https://www.googleapis.com/auth/youtube.upload`
  - optionally `https://www.googleapis.com/auth/youtube.readonly`

Output needed by Hermes Social Engine:

```text
YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN
```

## Facebook / Instagram connection

Needed:

- Meta Developer app
- Facebook Login / Graph API
- Facebook Page connected to Instagram Professional account if using IG Reels
- permissions usually include:
  - `pages_show_list`
  - `pages_read_engagement`
  - `pages_manage_posts`
  - `instagram_basic`
  - `instagram_content_publish`

Output needed:

```text
FACEBOOK_APP_ID
FACEBOOK_APP_SECRET
META_PAGE_ID
META_PAGE_ACCESS_TOKEN
IG_USER_ID
```

## TikTok connection

Needed:

- TikTok Developer app
- Content Posting API access
- OAuth redirect URL
- app approval may be required

Output needed:

```text
TIKTOK_CLIENT_ID
TIKTOK_CLIENT_SECRET
TIKTOK_REFRESH_TOKEN
```

## Safe rule

Secrets must be added to env/config; do not paste them into normal chat logs. Hermes can provide a secure helper script later that prompts locally without echoing secrets.


## Current YouTube credential state

OAuth client JSON has been received and stored locally as:

```text
secrets/google_oauth_client.json
```

Next step is to run local OAuth once to create:

```text
data/youtube_token.json
```

Command:

```bash
cd /mnt/c/Users/LENOVO/Desktop/Ai/03_AI_Projects/Hermes_Social_Engine
uv run python -m hse.cli youtube-auth
```

Do not paste client secrets or token JSON into chat/logs. Rotate the OAuth secret in Google Cloud if it was exposed in a public or shared place.
