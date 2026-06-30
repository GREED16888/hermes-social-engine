# Postiz study

Inspected repo: `/mnt/c/Users/LENOVO/Desktop/Ai/02_AI_Agents/Postiz/postiz-app`

Key paths:
- `apps/sdk/src/index.ts` public SDK: post, postList, upload, integrations, deletePost.
- `apps/backend/src/public-api/routes/v1/public.integrations.controller.ts` public API.
- `libraries/nestjs-libraries/src/integrations/social/social.integrations.interface.ts` provider contract.
- `libraries/nestjs-libraries/src/integrations/integration.manager.ts` provider registry.
- `libraries/nestjs-libraries/src/dtos/posts/create.post.dto.ts` post DTO.
- `libraries/nestjs-libraries/src/database/prisma/schema.prisma` DB model.

Design lesson: keep provider adapters + durable DB + validation + publish logs; skip heavy web UI/Temporal for one-person v1.
