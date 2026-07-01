# HSE Creator Ops Dashboard MVP

## What it is

A local FastAPI dashboard for Hermes Social Engine. It is designed as a revenue-first command center, not just a social scheduler.

## Run

```bash
uv run uvicorn hse.dashboard.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Current V1 capabilities

- Platform readiness cards: Telegram, YouTube, Facebook, TikTok, Instagram.
- SQLite-backed post overview: status counts, platform counts, events, media.
- Latest posts table from real `data/hse.sqlite3`.
- Metadata leak scanner for forbidden public terms.
- Revenue layer placeholder that intentionally shows no fabricated revenue.
- UI/UX Pro Max installed into project `.claude/skills/` for ongoing design work.

## Long-term direction

- YouTube and Meta analytics collectors.
- TikTok Shop CSV/API revenue imports.
- Manual basket workflow for TikTok drafts and product attachment.
- Campaign/revenue schema for revenue-per-clip ranking.
- Telegram daily summary backed by dashboard API.

## Safety rules

- No secrets in dashboard responses.
- Do not show token values or client secrets.
- Public metadata must never mention internal tools, AI workflow, project names, or automation.
- Run `hse media-audit` before every multi-clip upload batch.
