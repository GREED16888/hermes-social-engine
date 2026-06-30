# Facebook Video Upload Verification

Date: 2026-07-01

## Verification summary

Facebook Page publishing was verified in a local deployment of HSE:

```text
facebook text post=verified
facebook video upload=verified
```

Real page names, Page IDs, post IDs, and release URLs are intentionally excluded from this public repository. They are stored only in the owner's local HSE logs/state.

## Capability status

```text
telegram=implemented
youtube=implemented
facebook text post=implemented
facebook video upload=implemented
instagram=not connected by default
TikTok=scaffolded / pending developer app credentials
```

## Guardrail

Do not scale Facebook posting aggressively. Start with 1-2 clips/day on the primary page and avoid duplicate clips/captions across pages.
