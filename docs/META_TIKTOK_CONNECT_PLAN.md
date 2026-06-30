# Meta/Facebook/Instagram + TikTok Connect Plan

Last checked: 2026-06-30

## Current HSE platform status

```text
telegram=ready
youtube_client=ready
youtube_token=ready
youtube=ready
tiktok=missing_credentials
meta=missing_credentials
```

## Ground truth from Postiz source

Local Postiz source inspected:

```text
/mnt/c/Users/LENOVO/Desktop/Ai/02_AI_Agents/Postiz/postiz-app/libraries/nestjs-libraries/src/integrations/social/facebook.provider.ts
/mnt/c/Users/LENOVO/Desktop/Ai/02_AI_Agents/Postiz/postiz-app/libraries/nestjs-libraries/src/integrations/social/instagram.provider.ts
/mnt/c/Users/LENOVO/Desktop/Ai/02_AI_Agents/Postiz/postiz-app/libraries/nestjs-libraries/src/integrations/social/instagram.standalone.provider.ts
/mnt/c/Users/LENOVO/Desktop/Ai/02_AI_Agents/Postiz/postiz-app/libraries/nestjs-libraries/src/integrations/social/tiktok.provider.ts
```

Findings:

- Postiz also needs official developer app credentials for Meta and TikTok.
- Postiz Facebook provider uses `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, Graph API OAuth, and Page access tokens.
- Postiz Instagram Facebook Business provider requires Instagram Business account connected to a Facebook Page.
- Postiz Instagram Standalone provider uses `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET`, Instagram OAuth scopes.
- Postiz TikTok provider uses `TIKTOK_CLIENT_ID`, `TIKTOK_CLIENT_SECRET`, OAuth token/refresh token, and TikTok Content Posting API.
- TikTok source explicitly handles limits/errors such as daily post limit reached, pending posts limited to 5 within 24h, unaudited app can only post to private accounts, daily active user cap, spam risk, format/duration/frame-rate checks.

## Recommendation

Connect in this order:

1. Facebook Page text/photo/video posting
2. Instagram Reels via Meta/Facebook Business if the user's IG can be converted/connected
3. TikTok last, because Content Posting API/app review/limits are stricter

## Meta/Facebook/Instagram requirements

Needed from user/platform:

- Facebook account
- Facebook Page where the user has admin/full control
- For Instagram Reels: Instagram Professional/Business account connected to that Facebook Page
- Meta Developer app
- App products/permissions as needed:
  - Facebook Login / Graph API
  - `pages_show_list`
  - `pages_read_engagement`
  - `pages_manage_posts`
  - `business_management` may be useful for Page discovery
  - For IG Business route:
    - `instagram_basic`
    - `instagram_content_publish`

HSE needs stored secrets/tokens:

```text
META_APP_ID
META_APP_SECRET
META_USER_ACCESS_TOKEN
META_PAGE_ID
META_PAGE_ACCESS_TOKEN
IG_USER_ID
```

Implementation path:

- Build `meta-auth` helper for local OAuth.
- Exchange short-lived user token to long-lived token.
- List pages with `/me/accounts`.
- Store chosen Page ID + Page access token.
- Add `facebook` provider for Page feed/photo/video.
- Add `instagram` provider only after IG Business connection is verified.

## TikTok requirements

Needed from user/platform:

- TikTok account
- TikTok Developer app
- Content Posting API access
- OAuth redirect URL
- Scopes similar to Postiz source:
  - `user.info.basic`
  - `user.info.profile`
  - `user.info.stats`
  - `video.upload`
  - `video.publish`
  - `video.list`

HSE needs stored secrets/tokens:

```text
TIKTOK_CLIENT_ID
TIKTOK_CLIENT_SECRET
TIKTOK_ACCESS_TOKEN
TIKTOK_REFRESH_TOKEN
TIKTOK_OPEN_ID
```

Important TikTok constraints to expect:

- May require app review/approval for public posting.
- Unreviewed app may be restricted to private/test posting.
- Pending posts can be limited.
- Daily posting/rate limits can trigger.
- TikTok validates video format, duration, frame rate, spam risk, account status.

Implementation path:

- Build `tiktok-auth` helper after client id/secret exist.
- Query creator info before upload.
- Add safe defaults: private/self-only first if allowed.
- Add retry/error mapping for TikTok error codes.
- Test one private/direct upload only after approval/permissions are ready.

## Postiz comparison for these platforms

Postiz is useful as a UI/calendar and reference implementation, but it does not remove developer app/OAuth requirements.

If Postiz Cloud already has approved app flows for TikTok/Meta, it may reduce setup friction. If self-hosted, it still needs the same env credentials and callback/public URL setup.

Decision: keep HSE as the controller. Use Postiz as fallback/backend only if its hosted OAuth flow materially reduces friction.
