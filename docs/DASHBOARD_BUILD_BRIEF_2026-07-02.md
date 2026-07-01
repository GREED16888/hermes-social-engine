# HSE Creator Ops Dashboard Build Brief

## Goal
Build a real long-term dashboard for Hermes Social Engine (HSE) that is at least as useful as Postiz, but better for this user's revenue-first workflow.

## Current HSE facts
- Repo: GREED16888/hermes-social-engine
- Local path: /mnt/c/Users/LENOVO/Desktop/Ai/03_AI_Projects/Hermes_Social_Engine
- Providers: Telegram ready, YouTube ready, Facebook ready, TikTok app ready but token missing/in review, Instagram not connected.
- YouTube upload/schedule works; YouTube management scope works.
- Facebook text/video publishing works.
- TikTok review submitted; direct post off; initial workflow should be draft/inbox + manual basket.
- Duplicate media guard exists: exact sha256 blocking + perceptual media-audit CLI.
- Public metadata must never mention AI, Hermes, HSE, tools, automation, workflow, Money Printer, or internal project names.

## Dashboard MVP requirement
Must run locally, read real HSE data, and show:
1. Platform readiness cards.
2. Scheduled/posted/failed/private post status from HSE SQLite and local reports.
3. YouTube/Facebook/TikTok statuses.
4. Media audit/risk status.
5. Revenue-first placeholders/import-ready structure.
6. A long-term architecture path for analytics collectors and TikTok Shop/affiliate revenue.

## UX requirement
Use installed ui-ux-pro-max skill guidance. Make it beautiful, clear, dashboard-grade: dark command center, clean cards, status colors, table/calendar-ready layout. No internal/private public metadata leaking.

## Non-negotiable quality gates
- Real code, not mock-only essay.
- Tests must pass.
- Smoke run must start the dashboard server and fetch at least one endpoint/page.
- No secrets committed.
- Document how to run.
