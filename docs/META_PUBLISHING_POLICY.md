# Meta Publishing Policy

Last updated: 2026-07-01

## Page targeting

HSE supports explicit Facebook Page targeting through locally stored Meta tokens. Real page names, Page IDs, and access tokens are intentionally kept out of the public repository.

Local deployment should define:

```text
primary_page_id=<stored locally in data/meta_token.json>
secondary_page_ids=<optional, stored locally>
```

Instagram:

```text
No Instagram Business account is required unless the owner explicitly connects one to a Facebook Page.
```

## Current public capability status

```text
telegram=implemented
Youtube upload=implemented
Facebook Page text/video=implemented
TikTok OAuth/inbox upload=scaffolded
Instagram=planned/not connected
```

## Operational limits and guardrails

Meta/Facebook does not provide one simple fixed public number like "X videos per day" for every Page. Practical publishing capacity is governed by:

- Graph API rate limits per app/user/page over rolling windows.
- Page quality and spam enforcement.
- Repetitive/duplicate content detection.
- Account/Page trust, age, historical behavior, monetization status, and user feedback.
- Media processing limits and upload errors.

Safe operating policy for HSE:

1. Start Facebook Page automation with 1 real post/day/page until posting is verified and no Page Quality warnings appear.
2. Increase gradually to 2-3 posts/day/page only if reach/engagement and Page Quality remain healthy.
3. Avoid mass-posting 10+ near-duplicate clips/day to the same Page.
4. Keep at least 3-4 hours between automated video/Reels posts on the same Page unless the owner explicitly overrides.
5. For commerce/product content, prefer real product proof, accurate stock/price, no exaggerated health/earnings claims, and no copyrighted music unless rights are clear.

## Meta compliance checklist before publishing

- Content is owned by the operator or licensed for commercial use.
- Music/audio is licensed or platform-safe.
- Product claims are factual: price, stock, delivery area, expiry, ingredients, allergens.
- No medical/cure/guaranteed benefit claims.
- No misleading before/after, fake scarcity, fake discount, fake customer review, or bait engagement.
- AI-generated realistic people/events are labeled or framed clearly if they could mislead.
- Caption language matches audience; for local shop pages, avoid overclaiming and keep details verifiable.
- Do not repeatedly publish the exact same video/caption across pages in a short time window.

## Implementation note

HSE has Facebook text Page post and video upload capability. Production use should include:

- media validation
- per-page rate guard
- dryrun preview
- explicit confirmation before first real media post
- post ID/URL verification after publish

TikTok should be handled after a TikTok Developer App and Content Posting API access exist.
