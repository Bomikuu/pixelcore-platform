# Smokey implementation verification — 2026-10-27

Implementation spans PixelCore and the separately maintained SmokeyChatbot package.
Feature branches are `codex/smokey-assistant` and `codex/pixelcore-assistant`.
Product edits remain in the working directories for review; existing PixelCore
work was preserved. No merge, push, runtime migration or service recreation occurred.

## Passed checks

| Check | Result |
|---|---|
| Seven focused `businesses.test_smokey_*` modules | 40 passed on PostgreSQL in isolated `test_smokey_assistant`; database removed afterwards |
| Frontend Smokey utility/controller checks | 10 passed |
| `npm run check:ui` | Passed; Vue templates compile and no forbidden application primitives |
| Smokey Vue script block compilation | Passed |
| Standalone `npm run typecheck` | Passed |
| Focused standalone theme contracts | Passed, including denied storage and system preference resolution |
| Django migration drift | No changes detected for `businesses` or `smokey_assistant` |
| Ruff checks on new backend/package code | Passed |
| Whitespace and Compose configuration | Passed |
| Installed editable package, migration and asset presence | Confirmed |
| Scoped PixelCore Impeccable detector | No findings |

Backend checks mock all provider calls. They cover tenant/role boundaries,
credential masking, provider envelopes/errors, idempotency, free-text classification,
clarification, cancellation before/during calls, quota races, duplicate workers,
unknown usage, immutable snapshots, collected payments without new orders, DST and
Manila date boundaries, private mascot assets and 100/10,000-row caps.

The independent static review found theme persistence, connection readiness,
collection-only reports, generation usage attribution and post-reservation
cancellation issues. Its targeted follow-up scored all five resolved.

## Verification limits

- No frontend/backend application builds, browser inspections, visual tests,
  manual UI verification, live paid AI calls or standalone test suites were run.
- Real provider model/key availability is verified by the explicit connection
  check after a business supplies credentials, not by the mocked adapter checks.
- The standalone Impeccable detector flags the existing Instrument Sans choice,
  retained under the established design brief. The broad Premium audits are not
  clean project-wide results: they include existing form/ownership gaps and
  false positives identifying authored shadcn Select components as native selects.
  Logs are in the ignored `output/smokey-*-audit.json` files. No visual approval is claimed.
- Production distribution/asset builds remain unverified; source package metadata,
  editable import, migrations and local assets were inspected without an app build.

## Activation

Configure `SMOKEY_ENCRYPTION_KEYS`, install or mount the shared package, apply the
`businesses` and `smokey_assistant` migrations, and reload the affected Django/Celery
services. Then enable Smokey per business, add/test its provider connection and
select its default model. See [setup](smokey-assistant.md) and the sibling project's
`docs/PIXELCORE-INTEGRATION.md` for the complete contract.


## Shared frontend migration — 2026-10-27

Shared source/local integration is implemented; production cutover is pending.
Passed: Smokey typecheck and six focused scripts; 10 new PixelCore Node tests;
7 descriptor PostgreSQL tests in the isolated test database; `npm run check:ui`;
Compose/Nginx syntax, whitespace, development module HTTP graph and standalone
session/settings/report reads. The scoped Impeccable detector retained the existing
Instrument Sans warning under the approved design. A fresh reviewer found and
verified fixes for repeated Stop and public SDK release exports.

Local module delivery was started and the frontend/Nginx were recreated/reloaded
without an application build. No provider call, account/key/record change or new
schema migration occurred for this frontend migration. No production release was
built/promoted and no browser/visual/manual UI check was run. Real packaging,
keyboard/mobile/Shadow DOM acceptance and final legacy deletion remain gated.

See the full [shared verification record](/home/micxsz/projects/SmokeyChatbot/docs/SHARED-FRONTEND-VERIFICATION.md)
and [release guide](/home/micxsz/projects/SmokeyChatbot/docs/SHARED-FRONTEND-RELEASES.md).
The earlier result tables remain a historical record of the backend/initial UI
implementation, not evidence that the shared module passed browser acceptance.
