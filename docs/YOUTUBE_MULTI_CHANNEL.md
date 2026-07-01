# YouTube Multi-Channel Accounts

HSE supports multiple YouTube channels under one Google account or multiple Google accounts by storing one OAuth token per named channel account.

## Recommended accounts for this project

```text
youtube_en = existing channel, English Shorts
youtube_th = new Thai channel, Thai Shorts
```

## Token paths

```text
data/tokens/youtube/youtube_en.json
data/tokens/youtube/youtube_th.json
```

Legacy single-channel token path remains supported:

```text
data/youtube_token.json
```

## Authenticate each channel

English/existing channel:

```bash
uv run hse youtube-auth --account youtube_en --language en --label "English YouTube Channel"
```

Thai/new channel:

```bash
uv run hse youtube-auth --account youtube_th --language th --label "Thai YouTube Channel"
```

During Google OAuth, choose the exact YouTube channel/Brand Account. HSE reads back the authorized channel ID/title after OAuth and stores the account registry row.

## Verify a channel token

```bash
uv run hse youtube-status --account youtube_en
uv run hse youtube-status --account youtube_th
uv run hse accounts --platform youtube
```

## Schedule to a specific channel

```bash
uv run hse add \
  --platform youtube \
  --account youtube_th \
  --content "ชื่อคลิปภาษาไทย #Shorts" \
  --when "2026-07-03T04:30:00+07:00" \
  --media-path /path/to/th_video.mp4
```

```bash
uv run hse add \
  --platform youtube \
  --account youtube_en \
  --content "English Shorts Title #Shorts" \
  --when "2026-07-03T21:30:00+07:00" \
  --media-path /path/to/en_video.mp4
```

## Safety rules

- Do not run legacy `youtube-auth` without `--account` for multi-channel setup unless intentionally updating `data/youtube_token.json`.
- Run `hse media-audit` before every multi-clip batch.
- Do not upload the exact same file to both channels.
- Public metadata must not mention AI, Hermes, HSE, automation, workflow, internal project names, source folders, or production tools.
- Start conservative: 1 clip/day/channel, then 2/day/channel after the workflow is stable.
