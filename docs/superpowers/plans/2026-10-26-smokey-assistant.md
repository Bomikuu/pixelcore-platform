# Smokey Business Assistant Implementation Plan

Status: implemented natively, 2026-10-27. The execution record at the end is the
authoritative outcome; the original procedural checklists below remain the plan,
not a claim that every command was run in precisely its proposed order.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install Smokey into PixelCore as an optional business reporting assistant with business-owned AI connections, truthful mascot feedback, drawer/modal access, full reports and light/dark themes.

**Architecture:** A reusable `smokey_assistant` Django package in the Smokey repository owns AI orchestration, connections, request state, report snapshots and usage. PixelCore supplies authorization, authoritative report facts and Celery dispatch through a small adapter. PixelCore uses native Nuxt/shadcn surfaces; the existing standalone React/Tailwind/shadcn dashboard retains its website workflows and gains consistent themes and reusable mascot presentation.

**Tech Stack:** Existing Django, Django REST Framework and Celery in PixelCore; PostgreSQL for transactional quota checks; Python `requests` and `cryptography`; Nuxt/Vue/Tailwind/shadcn in PixelCore; React/TypeScript/Tailwind CSS v4/shadcn in standalone Smokey.

**Spec:** `/home/micxsz/projects/pixelcore-platform/docs/superpowers/specs/2026-10-26-smokey-assistant-design.md`

## Global Constraints

- Multiple AI providers are available from launch.
- The dashboard is white-first, with dark theme capability.
- Use Tailwind CSS and shadcn/ui for dashboard controls.
- The mascot communicates loading and searching progress.
- Support a right drawer and modal, with a full generated report page.
- Keep reusable assistant code and assets in `/home/micxsz/projects/SmokeyChatbot`.
- The standalone dashboard keeps React and TypeScript, officially generated shadcn primitives, arrow-function conventions and focused feature files.
- PixelCore uses its canonical `components/ui` primitives, including ButtonLink/ButtonAnchor for action links.
- Do not run either project's production builds, browser inspections, visual tests or manual verification unless the user explicitly requests them.
- PixelCore policy requires targeted automated checks and `npm run check:ui` after frontend changes.
- Smokey's local policy prohibits running test suites unless requested, so use focused static/type checks there and describe unexecuted suites accurately.
- Preserve existing uncommitted work and the public website chatbot.
- Do not modify the protected `/home/bomiku1/projects/dineEase-web` source.

## Review Focus

1. Revoked membership, disabled capability or deleted connection during a queued generation must prevent later access/publication (Tasks 2, 5, 6).
2. Unknown provider usage after a timeout must remain unknown and must not free potentially spent quota for immediate reuse (Task 5).
3. Repeated shifts, midnight boundaries and excused lateness must not change distinct employee counts or imply absence (Task 4).
4. Cancellation, expired workers and request replay must never publish a stale result or automatically repeat a potentially billed AI call (Tasks 5, 7).
5. Storage failures, system-theme changes and static/custom mascots must preserve usable status and theme controls (Tasks 7, 9).

## Execution boundaries and file ownership

`S` below means `/home/micxsz/projects/SmokeyChatbot`; `P` means `/home/micxsz/projects/pixelcore-platform`. Expand these to absolute paths when executing. A path beginning `S/python/smokey_assistant/` belongs to the new reusable package; never copy it into PixelCore.

Use focused host integration tests under `P/pixelcore-backend/businesses/` to exercise the installed shared package without running Smokey's prohibited standalone test suite. Tests use mocked provider transports and non-secret fixture encryption keys. Use the available project Python runtime; if dependencies are missing, install only declared runtime/test requirements in an isolated environment, never a production database.

For backend checks, run from `P/pixelcore-backend` with test-only environment values: `DJANGO_SECRET_KEY=smokey-tests-only DJANGO_DB_ENGINE=sqlite CELERY_TASK_ALWAYS_EAGER=1 python manage.py test <named test module> --settings=pixelcore_backend.smokey_test_settings --noinput`. Task 1 creates that test-only settings module to register the shared app before Task 2 adds production installation. SQLite covers ordinary logic, not concurrency guarantees. Task 5 also requires a PostgreSQL transaction-test run using an available test database; report it as unverified if no test PostgreSQL is available. Do not start or rebuild Docker services to obtain one without an explicit build request.

The optional installed package must be present before host integration tests load its models. Install locally with `python -m pip install -e /home/micxsz/projects/SmokeyChatbot/python --no-deps` after its declared dependencies are available. This is package installation, not an application production build. No dependency lockfile or unrelated file may be committed incidentally. Commit only task-owned changes after checking the staged diff in each repository.

## Shared contracts decided before implementation

- `HostContext(tenant_id: str, actor_id: str, timezone: str, permissions: frozenset[str])`; PixelCore tenant IDs are `pixelcore:<business UUID>`. Shared models use tenant strings and actor strings, not PixelCore foreign keys.
- Actions: `configure`, `generate`, `view_reports`, `delete_reports`. Owners/admins have all four; managers have the middle two. Staff and device tokens have none. Reauthorize resource reads and each worker boundary.
- `ReportPlan(kind, date_from, date_to)` uses ISO local dates and kinds `daily`, `sales`, `attendance`, `late`. Maximum inclusive range: 367 dates, matching the current report endpoint's 366-day difference limit. The server supplies business timezone and UTC boundaries.
- `FactSnapshot` has `version: 1`, `tenant_id`, `kind`, local `date_from`/`date_to`, `timezone`, `generated_at`, `metrics`, `tables`, `sources`, `unavailable_sources`. Decimal money travels as strings with currency; tables contain at most 100 preview rows with full counts and authenticated pagination links.
- `ResolvedReport(facts: FactSnapshot, detail_rows: Iterable[ReportRow])` separates provider-safe facts from server-only immutable detail rows. Persist up to 10,000 allowlisted detail rows per table, identify truncation and full row counts, and paginate persisted rows rather than live operational records. Complete aggregates never depend on that detail cap.
- `Narrative` has `summary: str` and `highlights: list[str]`, at most 4,000 characters total. It contains no HTML, source URLs or authority over metric values.
- `ProviderResult(narrative: Narrative, input_tokens: int | None, output_tokens: int | None, provider_request_id: str | None)` and `ProviderError(code, retryable, usage_unknown)`. Provider keys: `openai`, `anthropic`, `gemini`, `openrouter`. Fixed official API destinations only.
- Request states: `queued`, `searching`, `generating`, `succeeded`, `empty`, `failed`, `cancelled`. Mascot states map these to `idle`, `searching`, `generating`, `success`, `empty`, `error`, `cancelled`; queued uses idle pose plus "Waiting to start...".
- Settings include default connection/model, permitted models, presentation `drawer|modal`, mascot configuration and daily/monthly request/token budgets. Theme `light|dark|system` is a local user preference, separate from business-wide assistant settings.
- Every billable call, including classification and connection probes that consume tokens, has a usage attempt. No background automatic provider retry. A connection's status is `untested|ready|invalid|unavailable`; changing credentials/model invalidates previous readiness.

## Task 1: Package, schemas and encrypted persistence

**Files:** Create `S/python/pyproject.toml`; `S/python/smokey_assistant/{__init__,apps,contracts,models,credentials,checks}.py`; `S/python/smokey_assistant/migrations/{__init__,0001_initial}.py`; `S/python/smokey_assistant/assets/office-cat-sprite.webp` (reuse existing licensed repository asset). Create `P/pixelcore-backend/businesses/test_smokey_contracts.py` and `P/pixelcore-backend/pixelcore_backend/smokey_test_settings.py` (test-only app registration).

**Interfaces:** Produce `encrypt_secret(value: str) -> str`, `decrypt_secret(value: str) -> str` using `SMOKEY_ENCRYPTION_KEYS` (first Fernet key writes, remaining keys permit rotation reads), and `connection_payload(connection) -> dict` which never returns decrypted data. Define models `AssistantSettings`, `ProviderConnection`, `GenerationRequest`, `ReportSnapshot`, `ReportDetailRow`, `UsageAttempt`, `UsageBucket` and all contracts above. Unique settings by tenant; unique request by `(tenant_id, actor_id, idempotency_key)`; indexed tenant/request/report IDs; detail rows indexed by report/table/row ordinal. Save an immutable connection revision on a queued request, without copying plaintext credentials.

- [ ] Add host tests for contract rejection, tenant-specific uniqueness, encryption/decryption/rotation, masked output and missing-key configuration: `assert raw_secret not in json.dumps(connection_payload(connection))` and `assert encrypted_secret != raw_secret`.
- [ ] Run `businesses.test_smokey_contracts` and confirm the initial failure is missing package behavior, not broken environment setup.
- [ ] Implement package metadata, named models, initial migration and schema validation. Use a package dependency on Django, requests and cryptography with compatibility derived from the installed host versions; do not upgrade either application unnecessarily. Supply schema errors with stable codes.
- [ ] Re-run that module and run `python manage.py makemigrations smokey_assistant --check --dry-run` after the optional app is registered in Task 2. Both must pass before considering migration work complete.
- [ ] Commit only the package files and host contract tests in their owning repositories.

## Task 2: Optional installation and business authorization

**Files:** Modify `P/pixelcore-backend/pixelcore_backend/settings.py`, `P/pixelcore-backend/businesses/{models,serializers,services,urls}.py`. Create `P/pixelcore-backend/businesses/smokey_bridge.py`, `P/pixelcore-backend/businesses/test_smokey_access.py`, and `P/pixelcore-backend/businesses/migrations/0020_smokey_capability.py` (rebase its sequence if new migrations arrive). Modify `P/docker-compose.yml` and `P/dc.dev.yml` only if their existing sibling-package mount conventions require a Smokey mount; preserve unrelated service settings.

**Interfaces:** Produce `assistant_context(request, business_public_id, action: str) -> HostContext`, `worker_context(tenant_id, actor_id, action) -> HostContext`, and `smokey_available() -> bool`. Load an installed package normally; support `SMOKEY_ROOT/python` as an explicit local-development fallback. Package absence leaves unrelated app startup intact. Authorization uses PixelCore's JWT/membership checks, never the public widget's origin checks.

- [ ] Test that `smokey` is supported but absent from `default_modules()`, new businesses have no active Smokey capability, owners can enable it, managers cannot configure it, staff/device/public clients cannot generate, and another tenant's IDs are inaccessible. Pin `assert 'smokey' not in default_modules()`.
- [ ] Run `businesses.test_smokey_access` and confirm failing assertions for the missing capability/adapter.
- [ ] Separate the supported capability catalog from default enablement in serializers and services; add `smokey` without changing existing default behavior. Ensure explicit enablement creates a missing optional capability row, and legacy identity updates cannot accidentally enable it. Register the package only when installed; host endpoints exist only when usable. Add environment-driven encryption configuration without insecure production fallback.
- [ ] Re-run access/contract modules; add coverage for package absence and disablement after a context has been created. Confirm source-level host imports cannot become a dependency of the shared package.
- [ ] Commit task-owned access, migration and installation changes.

## Task 3: Four provider adapters and validated connections

**Files:** Create `S/python/smokey_assistant/providers/{__init__,base,openai,anthropic,gemini,openrouter}.py`, `S/python/smokey_assistant/{connections,classification}.py`, `S/docs/PROVIDERS.md`; create `P/pixelcore-backend/businesses/test_smokey_providers.py`.

**Interfaces:** Produce `get_provider(name: str) -> ProviderAdapter`; adapter methods `validate_connection(secret, model) -> ConnectionCheck`, `classify(secret, model, prompt, allowed_tools) -> ReportPlan | Clarification`, `summarize(secret, model, facts, max_output_tokens) -> ProviderResult`. Model catalog responses include model ID, provider, structured-output capability and date checked. Do not bake in the old README's model identifier.

- [ ] Read current official provider documentation and record endpoint/auth/schema/usage references in `S/docs/PROVIDERS.md`. OpenAI research follows the available openai-docs skill. No real paid calls or customer credentials.
- [ ] Add parameterized mocked-transport tests for all four provider names, wrong-provider model rejection, unsupported capabilities, HTTP authentication/quota/timeout errors, malformed schemas and absent usage: `assert result.input_tokens is None` when omitted. Verify no adapter accepts caller-controlled base URLs or leaks secrets in errors.
- [ ] Run `businesses.test_smokey_providers` to establish expected failures.
- [ ] Implement adapters, bounded provider-aware catalog/probe calls, classification schema validation and sanitized errors. Model readiness belongs to a specific credential revision. Never fall back to a global key. Bound all HTTP timeouts and output tokens.
- [ ] Re-run the provider module with all calls mocked and commit only adapter/connection changes plus tests and references.

## Task 4: Authoritative sales and attendance tools

**Files:** Create `P/pixelcore-backend/businesses/smokey_reports.py`, `P/pixelcore-backend/businesses/test_smokey_reports.py`; modify the Task 2 bridge to expose tool resolution. Reuse `operations/analytics.py` calculations where appropriate without changing unrelated dashboard behavior.

**Interfaces:** Produce `resolve_report(context: HostContext, plan: ReportPlan) -> ResolvedReport` and `report_rows(context, report_id, table_key, cursor) -> Page`. Tool registry exposes only the four agreed kinds and permitted source categories. Fact and row queries derive business identity from context.

- [ ] Add fixtures around Manila midnight and a DST timezone, repeated shifts, overnight shifts, excused late arrivals, no records, unavailable sources, Decimal totals and more than 100 rows. Pin `assert facts.metrics['attended_employees'] == 1` for two shifts by one employee; missing clock-in does not produce inferred absence.
- [ ] Run `businesses.test_smokey_reports` to confirm failures before implementation.
- [ ] Implement timezone-aware half-open UTC ranges. Count qualifying distinct employees; show recorded late minutes/excused flags, separate currently-clocked-in counts, and identify unavailable sources explicitly. Match existing sales/order status definitions; label ordered sales separately from collected payments. Keep aggregates complete while detail previews paginate.
- [ ] Build source links from host routes; field-allowlist provider snapshots to exclude documents, reasons and contact details. Return full aggregates and bounded server-only detail rows separately. Serve paginated report detail from the saved snapshot so later edits cannot change historical results; test both the 100-row preview cap and explicit 10,000-row persisted-detail truncation.
- [ ] Re-run report tests including permission loss on pagination and commit the resolver and tests.

## Task 5: Background generation, quotas and cancellation

**Files:** Create `S/python/smokey_assistant/{generation,quotas,usage,recovery}.py`; create `P/pixelcore-backend/businesses/smokey_tasks.py`, `P/pixelcore-backend/businesses/test_smokey_generation.py`, `P/pixelcore-backend/businesses/test_smokey_concurrency.py`; modify `P/pixelcore-backend/businesses/tasks.py` for task discovery.

**Interfaces:** Produce `start_generation(context, prompt, plan, idempotency_key) -> GenerationRequest`, `run_generation(request_id, resolve_context, resolve_report) -> None`, `cancel_generation(context, request_id) -> GenerationRequest`, and `usage_summary(context, date_from, date_to) -> dict`. Host dispatch uses Celery via `transaction.on_commit`; worker jobs are at-most-once claimed with persistent leases and no automatic paid-call retry.

- [ ] Test the complete successful/empty/clarification paths, duplicate HTTP submission, duplicate worker delivery, invalid default connection, revocation during execution, cancellation before/during provider calls, missing usage and expired worker leases. Pin `assert provider.call_count == 1` after identical idempotency replay and `assert request.report_id is None` after cancellation wins a publication race.
- [ ] Run `businesses.test_smokey_generation` to confirm failures.
- [ ] Atomically reserve daily/monthly request and token budgets using locked tenant buckets; reserve conservative provider-aware input/output ceilings for every possible classification/summary call. On unknown provider usage, preserve the unknown spend/reservation explicitly instead of refunding potentially spent tokens. Connection probes also respect quotas.
- [ ] Implement genuine searching/generating transitions, revision validation, pre-call/post-call authorization checks and transactional publication/cancellation. Record consumed usage even when cancellation prevents publishing. Redact errors and audit metadata. Recovery expires abandoned jobs without replaying a potentially billed call; explicit retry creates a new request/attempt.
- [ ] Re-run generation tests and run PostgreSQL `TransactionTestCase` races in `businesses.test_smokey_concurrency`: competing reservations cannot exceed budget; cancel/publish is mutually exclusive; duplicate workers cannot both call a provider. Record any unavailable PostgreSQL check as a delivery limitation.
- [ ] Commit lifecycle, accounting and task changes in their owning repositories.

## Task 6: Authenticated API and private reports

**Files:** Create `P/pixelcore-backend/businesses/{smokey_views,smokey_serializers}.py`, `P/pixelcore-backend/businesses/test_smokey_api.py`; modify the existing business URLs with conditional module routes. Add `S/python/smokey_assistant/{assets_api,reporting}.py` for reusable asset validation and report operations.

**Interfaces:** Base URL is `/api/businesses/<business UUID>/smokey/`. Expose `GET/PATCH settings/`; `GET/POST connections/`; `PATCH/DELETE connections/<id>/`; `POST connections/<id>/check/`; `GET connections/<id>/models/`; `POST generations/`; `GET generations/<id>/`; `POST generations/<id>/cancel/`; `GET reports/`; `GET/DELETE reports/<id>/`; `GET reports/<id>/tables/<key>/`; `GET usage/`; and owner/admin mascot upload plus authenticated asset reads. Model probes are explicit operations, not invisible on every page load.

- [ ] Add endpoint tests for all role groups, cross-tenant identifiers, validation errors, connection readiness changes, deleting a selected connection, secret-free representations, private report deletion, correct POST/GET semantics, usage filters and invalid/oversized mascot uploads. Pin `assert response.status_code in (403, 404)` for a different business's saved report.
- [ ] Run `businesses.test_smokey_api` before implementing views.
- [ ] Implement thin DRF views over shared services and host authorization; preserve existing JWT/CSRF mechanisms. POST generations accepts an idempotency key and returns `202` with opaque request ID/status URL; replay returns the same request. Response state includes truthful stage text, report ID, error category and clarification as applicable, never provider credentials. Bound prompts to 4,000 characters and source/details pages to 100 rows.
- [ ] Validate PNG/WebP custom assets up to the existing 5 MB limit, sprite dimensions/frame bounds and ownership. Internal assets must not become accessible through public widget site routes. Existing static/sprite/standard modes remain available.
- [ ] Re-run API/access/generation modules; confirm every endpoint rejects capability disablement and revoked membership, then commit API changes.

## Task 7: Shared client state and mascot feedback

**Files:** Create `P/pixelcore-frontend/utils/{smokeyAssistant,smokeyRequestState}.js` and matching `.test.mjs` files; `P/pixelcore-frontend/composables/useSmokeyAssistant.js`; `P/pixelcore-frontend/components/smokey/{SmokeyMascotStatus,SmokeyConversation,SmokeyAssistantPanel}.vue`.

**Interfaces:** Produce `createSmokeyClient(apiFetch, businessId)` using Task 6 endpoints, `mascotPresentation(state, source)`, and a testable request controller with `submit`, `stop`, `resume`, `dispose`, `setBusiness`. One controller owns drawer/modal state. Poll every 1.5 seconds with at most one outstanding poll, stop on terminal state/unmount, preserve request ID for reopening, and discard results tagged with stale business/controller epochs.

- [ ] Add Node tests with fake timers/deferred transports for duplicate submit, terminal polling, close/reopen, cancellation, retry idempotency keys, business changes during slow responses, static custom mascots and reduced-motion behavior. Pin `assert.equal(oldBusinessResultIsVisible, false)` after a business switch.
- [ ] Run `node --test utils/smokeyAssistant.test.mjs utils/smokeyRequestState.test.mjs` from the frontend to confirm failures.
- [ ] Implement the controller, explicit retry and text-plus-mascot states. Reuse existing sprite frames: different feedback can use pose/indicator/text without fabricating animation frames. Supply polite transition-only announcements, `aria-busy`, reachable Stop, and focus restoration. No roaming during a pending request.
- [ ] Compose the same conversation in canonical Sheet/Dialog primitives. Narrow layouts use a full-height surface with reachable close/composer; closing does not cancel. Preserve original prompt on errors and explain when a stopped upstream call may still consume usage.
- [ ] Re-run Node tests and `npm run check:ui`; commit the client/controller/components only.

## Task 8: PixelCore Smokey dashboard and full report pages

**Files:** Create `P/pixelcore-frontend/pages/workspace/smokey/{index,assistant,reports,appearance,connections,usage}.vue`, `P/pixelcore-frontend/pages/workspace/smokey/reports/[reportId].vue`; `P/pixelcore-frontend/components/smokey/{SmokeyDashboardNav,SmokeyConnectionForm,SmokeyAppearanceForm,SmokeyUsage,SmokeyReportView,SmokeyThemeSelect}.vue`; `P/pixelcore-frontend/utils/smokeySettings.js` and `.test.mjs`. Modify only the necessary navigation/launcher sections of the already-dirty `WorkspaceShell.vue`; use existing business/auth stores.

**Interfaces:** Routes consume Task 6 API and Task 7 controller. Settings form saves business configuration; theme uses existing Nuxt color mode and defaults to light if the user has no prior choice. Preserve existing explicit workspace theme preferences. Do not introduce a second competing root theme controller.

- [ ] Add Node tests for settings validation, administrative action visibility, provider/model coupling, failed connection readiness, null usage, date labels, terminal errors and reconnect behavior. Include every nonready connection state and manager read-only configuration.
- [ ] Run `node --test utils/smokeySettings.test.mjs` to establish failures; inspect existing surface context before editing UI and follow Impeccable's applicable craft-floor guidance. The approved white-first brief and host identity remain authoritative; no redesign tournament.
- [ ] Implement first-run enable/configure/test/model/mascot flow and the six navigation destinations. Use explicit loading/empty/error states, secret replacement fields with masked saved values, permitted-model selection, quota fields and genuine connection-check progress. Never place saved API keys in browser storage.
- [ ] Implement report history/detail, totals from facts, text-only narrative, source links and snapshot pagination. Regenerate visibly creates a new billed attempt; read/refresh does not. Usage includes failed/cancelled/unknown-token attempts and labels limits as application limits, not provider balance. Omit cost estimates until a dated rate table exists.
- [ ] Implement semantic light/dark tokens, white main surfaces and restrained accents for the new surfaces without redesigning unrelated workspace pages. Run all three Smokey Node test modules and `npm run check:ui`. Run the Impeccable mechanical detector once on the completed changed UI; no browser/visual verification without user authorization.
- [ ] Commit the new surfaces and only the relevant WorkspaceShell diff, preserving unrelated pending edits.

## Task 9: Standalone dashboard theme and mascot consistency

**Files:** Create `S/dashboard/src/features/theme/{ThemeProvider,ThemeSelect}.tsx`, `S/dashboard/src/lib/theme.ts`, `S/dashboard/src/components/common/MascotStatus.tsx`; modify `S/dashboard/{index.html,src/index.css,src/main.tsx}`, existing `features/{auth,sites,knowledge,appearance,install}/` components and generated UI primitives only where fixed colors prevent proper themes. Update `S/PRODUCT.md` and `S/DESIGN.md` with the approved theme behavior.

**Interfaces:** Produce arrow-function `resolveTheme(preference, systemDark)`, `readThemePreference(storage)`, `applyTheme(preference)` and `MascotStatus({state, label, reducedMotion, asset})`. The React and Vue status mappings share contract names and copy, not framework components. Standalone owner/site authentication and public knowledge access are preserved; internal PixelCore report routes cannot be accessed by public site IDs.

- [ ] Add focused TypeScript contract fixtures for valid theme/status unions; extract pure theme logic so storage-denied and media-query changes can be checked without a browser. Do not run a standalone test suite under current local policy.
- [ ] Add any missing shared primitives with the official shadcn CLI from `S/dashboard`, preserving the existing preset/configuration and reviewing generated source. No hand-written substitute primitive library.
- [ ] Apply theme before visible render, persist Light/Dark/System when possible, subscribe/unsubscribe system changes, and handle blocked storage. Replace dashboard hardcoded light colors with semantic Tailwind tokens throughout auth, sidebar, forms, preview panels and notices. Keep the light palette predominantly white with existing cobalt identity.
- [ ] Use real pending operations for mascot feedback during owner authentication, knowledge loading/search operations and appearance loading. Do not display a searching stage for an operation that merely saves configuration. Static mascot and reduced-motion cases retain identical text status. Keep the public widget's branding independent of owner dashboard theme.
- [ ] Run `npm run typecheck` from `S/dashboard`, scoped Python syntax checks if reusable backend files changed, and Impeccable's mechanical detector once over the completed standalone UI. Do not run `npm run build`, browser inspections or standalone test suites. Report any status behavior that cannot be verified without an authorized browser check.
- [ ] Commit standalone dashboard/theme documentation changes separately from PixelCore commits.

## Task 10: Packaging instructions and final scoped verification

**Files:** Create `S/docs/PIXELCORE-INTEGRATION.md`, `P/docs/smokey-assistant.md`; update `S/README.md`, `S/.env.example`, `P/README.md` and `P/.env.example`. Use placeholder values only. Keep the approved spec and this plan as review artifacts.

**Interfaces:** Document optional package installation, encryption key creation/rotation, required host callbacks, provider/model validation, Celery worker requirements, business enablement, connection checks, usage semantics, cancellation limits, private report deletion and package removal/disable behavior.

- [ ] Check final implementation against every acceptance criterion in the spec; identify the owning task and actual verification evidence. Fix missing coverage without widening into unrelated refactoring.
- [ ] Run the targeted PixelCore backend modules from Tasks 1–6 together, the PostgreSQL concurrency module where available, the three frontend Smokey utility suites, `npm run check:ui`, and standalone `npm run typecheck`. Do not repeat previously passed checks unless later changes affect them. Real provider calls, production asset packaging and visual/browser checks remain explicitly unverified unless authorized.
- [ ] Review package asset inclusion using installed package metadata and file manifests, with no application build. Confirm documented install paths work without a developer-specific mandatory sibling checkout; the `SMOKEY_ROOT` path is a development convenience.
- [ ] Update setup/operations documentation and distinguish app-token limits from provider billing; redact fixture secrets from examples/output. Do not claim that mocked adapters prove live model availability.
- [ ] Review `git diff --check` and task-owned staged diffs in both repositories. Preserve unrelated work and report changed files, passed checks, unexecuted checks and deployment configuration needed.
- [ ] After implementation, complete the available review workflow at its permitted scope. A static review cannot be reported as visual approval; Impeccable visual/finish-review steps requiring browser captures must wait for explicit user authorization under repository policy.

## Plan self-review

Coverage: package/permissions (1–2); all four providers and credentials (1, 3);
authoritative reports/timezones (4); quota/state/cancellation (5); authenticated
APIs/assets (6); mascot/drawer/modal (7); native dashboard/full reports/usage (8);
standalone themes and feedback (9); documentation/verification (10). The five review
focus conditions have explicit tests or focused permitted checks in their owning
tasks. Shared names, state mappings, routes and DTOs above are the source of truth.

## Native execution record — 2026-10-27

- [x] Tasks 1–3: reusable package, encrypted connections, optional installation,
  capability/role boundaries and all four provider adapters implemented.
- [x] Tasks 4–6: authoritative facts, private snapshots, transactional accounting,
  background requests, recovery/cancellation, assets and authenticated API implemented.
- [x] Tasks 7–9: business-scoped client controller, drawer/modal, report/dashboard
  pages, standalone white/dark/system themes and mascot feedback implemented.
- [x] Task 10: installation/operations documentation and permitted checks completed.

Actual evidence: 40 PostgreSQL backend checks, 10 frontend utility checks,
`npm run check:ui`, Vue script compilation, standalone TypeScript checks, focused
theme contracts, migration drift checks, Ruff and whitespace/Compose validation.
An independent static reviewer found five issues; its follow-up scored all five
resolved. This verdict is scoped to those findings, not browser or visual approval.

Implementation adjustments: report history lives at `reports/index.vue` so Nuxt
does not treat a non-outlet history page as the parent of report detail. Custom
mascots are stored privately in the shared settings record; image/grid validation
and authenticated reads avoid public media exposure. Existing workspace theme
work changed during execution; integration follows the current shared controller
and its actual storage key. Some API/client tests were introduced alongside code
rather than in separately recorded red/green cycles; final behavior is verified.

Product changes remain reviewable in the two feature-branch working directories,
with pre-existing PixelCore edits preserved. No merge, push or application deployment
was performed. Application builds, browser/visual checks, live provider calls and
standalone test suites were not authorized/run. Runtime activation needs encryption
configuration, migrations and worker/service reloads; it does not require another
implementation stage. See `docs/smokey-assistant-verification.md`.
