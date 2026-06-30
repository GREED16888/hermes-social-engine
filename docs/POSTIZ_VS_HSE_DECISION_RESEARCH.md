# Postiz vs Hermes Social Engine Decision Research

Date: 2026-06-30

## Sources checked

- https://postiz.com/pricing
- https://docs.postiz.com/public-api
- https://docs.postiz.com/providers/youtube
- https://docs.postiz.com/configuration/reference
- https://developers.google.com/youtube/v3/getting-started#quota
- https://developers.google.com/youtube/v3/determine_quota_cost
- Local Postiz source:
  - `libraries/nestjs-libraries/src/integrations/social/youtube.provider.ts`
  - `libraries/nestjs-libraries/src/integrations/social/tiktok.provider.ts`
  - `libraries/nestjs-libraries/src/integrations/social/facebook.provider.ts`

## Findings

### Postiz Cloud limits

Pricing page says:

- Standard: $29/mo, 5 channels, 400 posts/month
- Team: $39/mo, 10 channels, unlimited posts/month
- Pro: $49/mo, 30 channels, unlimited posts/month
- Ultimate: $99/mo, 100 channels, unlimited posts/month

This is a Postiz plan quota. It does not remove platform limits.

### Postiz Public API limits

Docs say:

- create-post public API rate limit: 90 requests/hour self-host default
- Postiz Cloud uses 100 requests/hour
- multiple posts can be scheduled in one request
- self-hosters can adjust `API_LIMIT`
- channel and post quotas are tiered separately by plan

### YouTube in Postiz

Postiz YouTube docs require:

- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- YouTube Data API v3 enabled
- OAuth redirect URI

Local source confirms Postiz uploads via official YouTube API:

- `youtube.provider.ts` uses `google.youtube({ version: 'v3' })`
- calls `youtubeClient.videos.insert(...)`
- source comment: `// YouTube has strict upload quotas`

Therefore Postiz self-host still hits YouTube API quota/app/account rules.

### YouTube API quota

Google docs say:

- default quota includes 100 `videos.insert` calls and 10,000 units/day for other endpoints
- quota cost page says `videos.insert` costs 1600 points

Practical interpretation:

- Google docs now describe a separate default bucket of 100 `videos.insert` calls, plus general 10,000 unit pool for other endpoints.
- The older/common 10,000/1600 ~= 6 uploads/day interpretation is incomplete if the separate `videos.insert` bucket applies to the project.
- Real limit must be verified in Google Cloud quota page for the actual project.

### TikTok in Postiz

Postiz source handles errors:

- daily post limit reached
- pending posts limited to 5 within 24 hours
- app not approved for public posting
- daily active user quota reached

So Postiz does not bypass TikTok platform restrictions.

## Verdict

Building Hermes Social Engine is not wasted if the goal is: Hermes-controlled, one-person, customized workflow.

Postiz is better if the goal is: fastest existing dashboard/calendar with many platform integrations, accepting subscription/self-host complexity.

Best path:

1. Use Postiz Cloud/self-host as benchmark and optional fallback.
2. Continue Hermes Social Engine as owned controller.
3. Do not rebuild every provider blindly; first connect YouTube and test real quota in actual Google project.
4. If Postiz Cloud handles YouTube upload with less friction and acceptable cost, use Postiz as backend engine while Hermes remains the brain/controller.
