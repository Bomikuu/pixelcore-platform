# Smokey shared frontend planning handoff

Date: 2026-10-27 (Asia/Manila)
Status: shared source/local integration implemented; production cutover pending

The canonical shared frontend design and implementation plan live in the Smokey
repository, which owns the reusable dashboard and assistant UI:

- [Design specification](/home/micxsz/projects/SmokeyChatbot/docs/superpowers/specs/2026-10-27-smokey-shared-frontend-design.md)
- [Implementation plan](/home/micxsz/projects/SmokeyChatbot/docs/superpowers/plans/2026-10-27-smokey-shared-frontend.md)

Scope: preserve standalone login; replace duplicated PixelCore feature UI with a
directly mounted React module (no iframe); add one lower-right mascot and toolbar
toggle controlling a shared drawer/session; use a thin host adapter; publish
compatible versioned frontend releases independently of the PixelCore frontend.

PixelCore keeps authentication, business context, source/report queries, permission
enforcement, main navigation and its theme. Future hosts supply their own adapter.
Medframe's real authentication/data integration is not included in this migration.

The plan lists exact host adapter/descriptor/plugin/route/configuration changes and
the legacy files to remove after cutover. No duplicate plan is maintained here.
Previous backend/privacy/report requirements remain in force. Existing native
execution preference is preserved. The subsequent user instruction authorized native implementation and the necessary
local service wiring. No production build, browser/visual check, paid AI call or
credential change was performed. See the canonical verification record for results.
