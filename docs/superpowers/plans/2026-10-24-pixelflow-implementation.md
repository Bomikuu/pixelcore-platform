# Pixelflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **User override:** execute natively in this chat, with no agents, delegation,
> separate chats, or agent reviewers. Preserve this choice for every phase.

**Goal:** Deliver an independently maintained Philippines-first payments service,
administration dashboard, isolated checkout and installable Python/TypeScript
clients for multiple host projects.

**Architecture:** One modular Django service owns scoped payment state and durable
events in PostgreSQL. Celery/Redis process provider operations and deliveries;
database recovery makes enqueue loss survivable. React/Vite dashboard and
checkout entries consume the API; hosts integrate through small SDKs and signed
events while keeping their own business records and fulfillment.

**Tech Stack:** Python, Django 5.2 LTS, Django REST Framework, PostgreSQL, Celery,
Redis, React, Vite, TypeScript, Tailwind CSS, upstream shadcn/ui, React Router,
TanStack Query, React Hook Form, Zod, REST/OpenAPI and Docker.

**Spec:** [2026-10-24-pixelflow-design.md](../specs/2026-10-24-pixelflow-design.md).

**State:** detailed plan prepared for user review; no product implementation has
started. The user already selected native execution. Plan approval does not
authorize production deployment, real charges, host cutover or registry release.

## Global Constraints

- Target new local repository: `/home/micxsz/projects/pixelflow`; do not overwrite
  any existing directory. Create a local repository only after plan approval.
- No agents or agent reviewers. Review and implementation remain in this chat.
- Use graphify and Jev, submit sanitized input, and verify judgments directly.
- Preserve PixelCore, Medframe and DineEase application source and data; actual
  host modifications/cutovers are a later integration phase.
- Do not modify `/home/bomiku1/projects/dineEase-web`.
- Django 5.2 LTS with supported security patches; lock compatible dependencies.
- Frontend: React + Vite + TypeScript. Tailwind CSS and upstream shadcn/ui are mandatory.
- Initial methods: GCash, Maya, cards and recorded cash; currency: PHP integer centavos.
- Each business uses its own merchant account; no custody or pooled payouts.
- API keys, records, memberships and provider references are tenant/environment scoped.
- Financial writes require durable idempotency; unknown writes never trigger blind retries.
- PostgreSQL is the financial source of truth; Redis is transport.
- SDKs contain no React, Vue, Tailwind or dashboard dependencies.
- No frontend/backend builds, visual tests, browser inspections or manual
  verification without an explicit user request. Use targeted automated checks.
- Actual future PixelCore frontend changes require its `npm run check:ui`.
- Merchant approval and real gateway configuration are separate activation
  prerequisites; mocked fixtures do not establish a working sandbox account.

## Review Focus

1. An invoice revision changes while an older gateway checkout remains payable:
   reject a new collectible attempt until the old one is resolved (Task 2).
2. A worker dies after dispatching a gateway write: preserve an uncertain
   operation and reserve funds instead of redispatching (Tasks 3 and 5).
3. A refund event arrives before a paid event or an old failure arrives after
   success: retain/reconcile evidence without double-applying money (Task 4).
4. A member loses access while cached dashboard data is visible: clear protected
   data on authorization failure and recheck every mutation server-side (Task 9).
5. A host receives both `payment.succeeded` and `cash.collected`: allocate money
   once and treat collection context as informational (Tasks 6 and 7).

---

## Shared contracts and file ownership

All paths below are relative to the new `pixelflow/` repository.

| Boundary | Canonical owner |
| --- | --- |
| Django configuration, HTTP error envelope and request IDs | `apps/api/config/` |
| Project, tenant, environment, membership and scoped key | `apps/api/accounts/` |
| Payables, snapshots, sessions, attempts, refunds and cash | `apps/api/payments/` |
| Provider protocol, capability rules and HTTP adapters | `apps/api/providers/` |
| Provider inbox, immutable events, delivery and recovery | `apps/api/events/` |
| Append-only actor/action history | `apps/api/audit/` |
| API schema | `docs/api/openapi.yaml`, generated from DRF serializers |
| Theme and Shadcn primitive implementations | `packages/ui/src/` |
| Dashboard routing, session and tenant/environment selection | `apps/dashboard/src/` |
| Public checkout client | `apps/checkout/src/` |
| Framework-independent clients and signature verification | `packages/sdk-python/`, `packages/sdk-typescript/` |
| Native host integration demonstrations | `examples/django-nuxt/`, `examples/django-next/` |

Common types: `Scope(project_id, tenant_id, environment, principal_id, permissions)`;
`Money(amount: int, currency: Literal['PHP'])`; `PaymentStatus` = `created`,
`pending`, `uncertain`, `succeeded`, `failed`, `expired`, `cancelled`;
`RefundStatus` = `requested`, `pending`, `uncertain`, `succeeded`, `failed`.

All IDs are UUID strings in JSON. All timestamps use ISO 8601 UTC. An error has
`error: {code, message, request_id, details}`. Server pagination has
`{results, count, next, previous}`. Reads accept explicit bounded filters; mutable
financial states never come from an arbitrary update serializer.

### Task 1: Establish scoped identity and a runnable API boundary

**Files:** `pyproject.toml`, `uv.lock`, `AGENTS.md`, `.gitignore`, `.env.example`,
`apps/api/manage.py`, `config/{settings,urls,errors,middleware,celery}.py`,
`accounts/{models,authentication,policy,services,views,urls}.py`,
`audit/{models,services}.py`, and their `__init__.py`, app config and migration
files; `apps/api/tests/{conftest,test_scopes,test_sessions,test_keys}.py`.

**Interfaces:** `resolve_scope(request, permission: str) -> Scope`;
`issue_key(scope, name, permissions) -> IssuedKey(id, prefix, secret)`;
`revoke_key(scope, key_id) -> None`; `record_audit(scope, action, object_id, safe_details)`.
Dashboard memberships bind tenant/environment/role. Server keys bind the same
scope. No Django superuser bypass is implicit in domain authorization.

- [ ] Verify the target path is absent, initialize only that repository, copy
  this approved plan/spec, and write AGENTS.md with the user's native/no-agent,
  tooling, verification and protected-source rules. Add dedicated local settings
  with separate database names and production startup validation.
- [ ] Write denial tests for cross-project/tenant/environment access, revoked
  keys, privilege escalation through scope headers, and anonymous login without
  valid CSRF. Assert only the newly issued key response reveals its secret.
- [ ] Run `uv run pytest apps/api/tests/test_scopes.py apps/api/tests/test_sessions.py apps/api/tests/test_keys.py`;
  first require failure for the missing implementation.
- [ ] Implement the scoped models, hashed random API keys, session login/logout
  with CSRF protection even for anonymous login, role capability map and redacted
  error envelope. Keep provider secrets out of this task's responses/logs.
- [ ] Rerun those tests and `uv run python apps/api/manage.py check`. Expected:
  PASS against an isolated PostgreSQL test database. Commit this deliverable.

### Task 2: Implement payables, checkout identity and cash collection

**Files:** `payments/{models,types,validation,idempotency,checkout,cash,serializers,views,urls}.py`,
`payments/migrations/0001_initial.py`,
`tests/{test_checkout,test_idempotency,test_cash,test_concurrency}.py`.

**Interfaces:** `create_checkout(scope, payload, idempotency_key) -> CheckoutSession`;
`get_payment(scope, payment_id) -> PaymentDetail`;
`record_cash(scope, payment_id, amount, collected_at, reference, idempotency_key) -> PaymentDetail`.
`CheckoutInput` contains external payable ID/version, integer amount, PHP,
payer-safe description, methods, success/cancel URLs and optional approved theme.

- [ ] Write tests asserting booleans/fractions/zero/negative amounts are rejected;
  same-key replay returns the same IDs; changed payload is 409; cash selection
  stays unpaid; a viewer cannot collect; one authorized collection succeeds once.
- [ ] Add PostgreSQL concurrency tests: simultaneous creation has one collectible
  attempt; changing the payable version cannot bypass an older unresolved
  checkout; separate tenants can use the same external payable ID safely.
- [ ] Run `uv run pytest apps/api/tests/test_checkout.py apps/api/tests/test_idempotency.py apps/api/tests/test_cash.py apps/api/tests/test_concurrency.py` and observe initial failures.
- [ ] Implement an immutable snapshot per version and lock a stable payable row
  scoped to tenant/environment/external ID. Reserve operations before external
  work. A successful attempt permanently blocks recollection of that snapshot;
  unresolved attempts also block a newer version of the same payable. A new
  installment must use its host-authorized payable identity/version.
- [ ] Store random checkout capabilities with a lookup digest and encrypted
  recoverable value for idempotent URL replay. Use a configured encryption
  keyring, allowlisted return origins, bounded expiry and no production fallback
  secret. Audit cash collection in the same transaction as financial state.
- [ ] Rerun the task tests. Expected: PASS, including PostgreSQL race cases.
  Commit the payment/cash domain boundary.

### Task 3: Add the provider protocol and PayMongo checkout adapter

**Files:** `providers/{base,registry,paymongo,capabilities,crypto}.py`,
`accounts/{models,connections,serializers,views,urls}.py` and the merchant-connection
migration, `payments/{models,gateway_operations,tasks,public_views}.py` and the
gateway-operation migration,
`tests/{test_provider_contract,test_paymongo_checkout,test_gateway_recovery,test_public_checkout}.py`,
`docs/providers/paymongo.md`.

**Interfaces:** `Provider.create_checkout(snapshot, operation_id) -> CheckoutResult`;
`retrieve_checkout(reference) -> ProviderSnapshot`; `expire_checkout(reference) -> ProviderSnapshot`;
`continue_checkout(token, method) -> PublicCheckoutAction`;
`dispatch_gateway_operation(operation_id) -> None`.
`CheckoutResult` has provider session reference, validated HTTPS checkout URL and
raw provider status translated to the public domain vocabulary.

- [ ] Write mocked HTTP tests for the documented v2 request, `maya`→`paymaya`,
  bounded timeout, key/environment mismatch and safe handling of malformed
  successful responses. Assert no unknown checkout host URL reaches a browser.
- [ ] Add recovery tests: timeout after dispatch becomes uncertain; stale worker
  lease does not repeat POST; a second public continue returns the same operation;
  changing to cash cannot bypass an active electronic checkout.
- [ ] Run `uv run pytest apps/api/tests/test_provider_contract.py apps/api/tests/test_paymongo_checkout.py apps/api/tests/test_gateway_recovery.py apps/api/tests/test_public_checkout.py` and require initial failures.
- [ ] Implement write-only encrypted merchant connection credentials, explicit
  capabilities, a gateway-operation dispatch marker committed before network
  I/O, and typed definite/uncertain errors. Retrieve methods may retry with
  bounds; writes cannot assume provider idempotency from an arbitrary header.
- [ ] Expose public capability-based GET/continue endpoints with minimal safe
  data. Local expiry denies new actions without asserting an outstanding provider
  URL is noncollectible. No public endpoint can confirm cash or mark payment paid.
- [ ] Rerun those tests; expected PASS. Record exact official documentation and
  fixture provenance, unsupported envelope/merchant prerequisites and no live
  verification claim. Commit the adapter.

### Task 4: Persist, verify and reconcile provider events

**Files:** `events/{models,inbox,signatures,provider_views,tasks}.py`,
`payments/{transitions,reconciliation}.py`,
`tests/{test_provider_signatures,test_inbox,test_transitions,test_reconciliation}.py`,
`tests/fixtures/paymongo/*.json`.

**Interfaces:** `verify_event(raw_body, headers, connection, now) -> VerifiedProviderEvent`;
`receive_provider_event(connection_id, raw_body, headers) -> InboxReceipt`;
`process_inbox(inbox_id) -> None`; `reconcile_payment(scope, payment_id, idempotency_key) -> Operation`.
Verified events include deduplication identity, environment, resource references,
event type, amount/currency evidence and a verified body digest.

- [ ] Write signature tests for exact raw bytes, stale/future timestamps beyond
  300 seconds, tampering and test/live selection. Add independently named
  fixtures for each documented supported envelope; unknown shapes stay rejected
  or explicitly unresolved and never establish success.
- [ ] Write tests for duplicate IDs, inconsistent duplicate bodies, unmatched
  resources, amount/currency/merchant mismatch, a refund event preceding paid,
  and a failure arriving after success. Assert late verified paid evidence is
  retained after local expiry and produces a reconciliation flag where needed.
- [ ] Run `uv run pytest apps/api/tests/test_provider_signatures.py apps/api/tests/test_inbox.py apps/api/tests/test_transitions.py apps/api/tests/test_reconciliation.py` and require initial failures.
- [ ] Implement signature-first durable inbox acceptance, unique deduplication,
  monotonic financial transitions and recoverable failed/unmatched processing.
  Acknowledge only after durable persistence. Use provider retrieval when event
  evidence is incomplete; never use a redirect query parameter as evidence.
- [ ] Rerun the task tests; expected PASS. Commit verified event processing.

### Task 5: Implement refund reservations and bounded reconciliation

**Files:** `payments/{models,refunds,refund_policy,serializers,views,urls}.py` and
the refund migration, `providers/paymongo_refunds.py`,
`tests/{test_refunds,test_refund_concurrency,test_refund_capabilities}.py`.

**Interfaces:** `request_refund(scope, payment_id, amount, reason, idempotency_key) -> RefundDetail`;
`Provider.create_refund(payment_reference, amount, reason, operation_id) -> RefundResult`;
`retrieve_refund(refund_reference) -> RefundSnapshot`.
Payment details return paid/refunded/reserved/refundable amounts separately.

- [ ] Write tests asserting pending and uncertain refunds reserve their amount;
  simultaneous partial refunds cannot exceed the original paid amount; duplicate
  requests do not call the provider twice; full refund preserves original success.
- [ ] Add capability tests for same-day Maya partial restriction using
  Asia/Manila dates, unsupported cash gateway refund, missing paid timestamp and
  unknown card-installment eligibility. Never advertise unsupported eligibility.
- [ ] Run `uv run pytest apps/api/tests/test_refunds.py apps/api/tests/test_refund_concurrency.py apps/api/tests/test_refund_capabilities.py` and require initial failures.
- [ ] Implement row-locked reservations, reason validation, provider reference
  tracking and uncertain-write recovery using Task 3's operation protocol.
  Definitive failure releases its reservation; uncertain outcomes retain it.
  Cash corrections remain an explicitly unsupported capability in the first MVP.
- [ ] Rerun tests; expected PASS against PostgreSQL. Commit refunds.

### Task 6: Deliver signed events from a durable outbox

**Files:** `events/{models,outbox,delivery,destinations,recovery,serializers,views,urls}.py`
and the outbox/delivery/endpoint migrations, `payments/{cash,transitions,refunds}.py`
to connect the domain event hooks, `config/urls.py`,
`events/management/commands/recover_events.py`, `config/celery.py`,
`tests/{test_outbox,test_delivery,test_delivery_recovery,test_destination_policy}.py`.

**Interfaces:** `emit_event(scope, event_type, payment, context=None) -> DomainEvent`;
`deliver_event(delivery_id, now=None) -> DeliveryResult`;
`recover_events(now=None, limit=100) -> RecoverySummary`;
`sign_event(event_id, timestamp, raw_body, secret) -> str`.
Signature header: `Pixelflow-Signature: t=<unix>,v1=<hex HMAC-SHA256>` over
`event_id + '.' + timestamp + '.' + exact_body`; event identity is the JSON `id`
and must match any separate event-ID header. Tolerance: 300 seconds.

- [ ] Write tests for atomic domain change/outbox creation, enqueue loss,
  duplicate delivery, expired leases, network timeout, non-2xx response,
  manual redelivery and bounded retry exhaustion. Assert immutable payload/ID
  across retries while the signature timestamp is refreshed per delivery.
- [ ] Add tests that `payment.succeeded` is the single money-allocation trigger;
  `cash.collected` carries context and cannot create a second success event.
  Reject unapproved/non-HTTPS production URLs, private network destinations and
  redirect-following. Make localhost delivery an explicit development setting.
- [ ] Run `uv run pytest apps/api/tests/test_outbox.py apps/api/tests/test_delivery.py apps/api/tests/test_delivery_recovery.py apps/api/tests/test_destination_policy.py` and require initial failures.
- [ ] Implement DB leases/locks, persisted attempt history, exponential backoff
  with configured attempt/time bounds and a periodic database recovery sweep.
  Production deployment must enforce outbound network restrictions against DNS
  rebinding; hostname syntax checks alone do not establish network safety.
- [ ] Rerun tests; expected PASS. Commit durable event delivery and recovery.

### Task 7: Publish API contracts and implement installable SDKs/examples

**Files:** root `package.json`, npm lockfile and `vitest.config.ts` for SDK
workspace commands; `apps/api/config/schema.py`, `payments/serializers.py`,
`docs/api/openapi.yaml`, `docs/events/v1.md`,
`packages/sdk-python/{pyproject.toml,pixelflow/client.py,pixelflow/webhooks.py,tests/test_client.py,tests/test_webhooks.py}`,
`packages/sdk-typescript/{package.json,tsconfig.json,src/client.mjs,src/browser.mjs,src/server.mjs,src/index.d.ts,src/browser.d.ts,src/server.d.ts,tests/client.test.ts,tests/webhooks.test.ts}`,
`examples/{django-nuxt,django-next}/`.

**Interfaces:** Both clients expose `createCheckout`, `getPayment`, `listPayments`,
`requestRefund`, `recordCashCollection`, `reconcilePayment` and server-side
`verifyWebhook` (Python uses snake_case). Constructor accepts base URL, scoped
key and timeout; mutation methods require caller-provided idempotency keys.
The TypeScript package has a build-free ES-module runtime plus public TypeScript
declarations, checked together, avoiding committed duplicate compiled sources.

- [ ] Establish the root npm workspace/test/typecheck commands and lock the SDK
  development dependencies before invoking workspace checks. Generate OpenAPI
  from domain serializers, inspect required request/response
  fields and validate schema coverage. Define environment, error codes,
  capabilities and pagination before writing client calls.
- [ ] Write SDK contract tests for exact routes/headers, bounded errors, reused
  idempotency identity, no automatic write retries and raw-body event signature
  rejection. Add a TypeScript consumer type fixture and a browser-entry import
  test proving there are no Node/server-secret/UI imports.
- [ ] Run `uv run pytest packages/sdk-python/tests` and
  `npm run test --workspace @pixelflow/sdk`; require initial failure.
- [ ] Implement the clients with browser-safe and server-only package exports.
  Webhook verification checks the envelope's ID/version after signature
  verification. Responses preserve integer minor units; SDK types mirror OpenAPI.
- [ ] Add standalone Django examples authorizing their own synthetic payable,
  creating checkout server-side and applying a unique event ID under a database
  transaction. Nuxt/Next examples only request their host backend's checkout URL.
  Handle `cash.collected` without allocating money. Do not patch actual hosts.
- [ ] Rerun Python/SDK tests and `npm run typecheck --workspace @pixelflow/sdk`;
  validate install manifests without lifecycle scripts or registry publication.
  Expected: PASS; commit SDKs, schema and examples.

### Task 8: Establish the Pixelflow visual system and shared components

**Files:** `PRODUCT.md`, `DESIGN.md`, `UX-CONTRACT.md`, `.impeccable/config.json`
(only when the user chooses a workflow default), `docs/design/dashboard.md`,
`packages/ui/{package.json,components.json,src/styles.css,src/lib/utils.ts,src/components/ui/}`,
updates to root `package.json`/lockfile and `scripts/check-ui.mjs`.

**Interfaces:** shared Shadcn components and semantic CSS variables; canonical
`MoneyText`, `PaymentStatusBadge`, `AsyncState`, `PageHeading`, `ActionDialog`
and typed `ButtonLink`. Public theme input is validated against an allowlist;
provider and financial statuses remain text-labelled.

- [ ] Record the spec-approved product/audiences/stack in PRODUCT.md. Resolve
  Impeccable's visual direction and code/mockup preference through the user's
  structured selection; do not invent a saved preference from silence. Backend
  work is independent of this UI selection.
- [ ] Write DESIGN.md and UX-CONTRACT.md with token ownership, theme mapping,
  navigation, feedback, permission denial, recovery, locale and keyboard rules.
  Read Impeccable's craft floor immediately before UI edits.
- [ ] Add shared Shadcn primitives and exact canonical ownership; prevent raw
  button/input/select/textarea/table elements outside that layer through the
  new repository's `npm run check:ui` automated check.
- [ ] Add automated component assertions for role/labels, focus restoration,
  status text, exact centavo formatting, decimal-input parsing, reduced-motion
  CSS and malicious theme rejection. Run `npm run test --workspace @pixelflow/ui`
  and `npm run check:ui`; expected PASS. No browser/visual/build step.
- [ ] Run applicable static design/token audits and commit the selected system.

### Task 9: Implement the administration workflows against the real API

**Files:** `apps/dashboard/{package.json,index.html,vite.config.ts,tsconfig.json}`,
`apps/dashboard/src/{main.tsx,router.tsx,app-shell.tsx}`,
`src/features/{session,scope,payments,refunds,cash,connections,developers,deliveries,settings}/`,
`src/lib/{api,query-client,money}.ts`, and feature-local `*.test.tsx`.

**Interfaces:** `DashboardScope {tenantId, environment, permissions}`;
`usePayments(scope, filters)`, `usePayment(scope, id)` and mutation hooks calling
the same domain/API services as SDKs. Query keys always begin with tenant and
environment. Dashboard API headers select membership scope without granting it.

- [ ] Write automated component/API-boundary tests for login/CSRF, empty/error/
  loading states, searchable server pagination, filter-preserving detail return,
  role-restricted actions and revocation while cached data is visible.
- [ ] Add tests for refund/cash review dialogs: amount/currency/reason visible,
  pending prevents duplicate submission, transport uncertainty retains the
  original operation key, and successful UI state requires a server result.
- [ ] Run the targeted dashboard tests; require initial failures.
- [ ] Implement overview, payments/detail, refunds, cash collection, provider
  connections, key issuance/revocation, webhook delivery history/replay and
  branding/settings. Use API data and actionable empty states; no invented
  merchant totals, configured connections or live readiness claims.
- [ ] Cancel scoped reads and clear protected caches on scope change, logout or
  authorization failure. Handle stale mutations with a typed conflict message;
  no optimistic financial success and no new write key on ambiguous retry.
- [ ] Run `npm run test --workspace @pixelflow/dashboard`,
  `npm run typecheck --workspace @pixelflow/dashboard`, and `npm run check:ui`.
  Expected: PASS. Run applicable static UI audit; commit the dashboard.

### Task 10: Implement the separate customer checkout entry

**Files:** `apps/checkout/{package.json,index.html,vite.config.ts,tsconfig.json}`,
`apps/checkout/src/{main.tsx,checkout-page.tsx,api.ts,checkout.test.tsx}`,
`scripts/check-boundaries.mjs`.

**Interfaces:** `getPublicCheckout(token) -> PublicCheckout`;
`continuePublicCheckout(token, method) -> {status, checkout_url?, payment_id}`.
`PublicCheckout` exposes merchant branding, description, amount/currency,
allowed methods, expiry and payer-safe status only.

- [ ] Write component tests for missing/expired capabilities, unavailable
  providers, cash selection remaining pending, provider redirect validation,
  preparing/uncertain/succeeded states and a forged success URL parameter.
- [ ] Add a source import-graph check proving checkout cannot import dashboard
  entries/features and SDKs cannot import either frontend or UI dependencies.
- [ ] Run the task tests and observe initial failures.
- [ ] Implement minimal branded checkout with shared Shadcn components, keyboard
  controls and API-driven status refresh. Set no-referrer policy, keep capability
  URLs out of telemetry, and redirect only to validated provider URLs. Cash
  instructions cannot claim collection. Do not render raw card fields.
- [ ] Run `npm run test --workspace @pixelflow/checkout`,
  `npm run typecheck --workspace @pixelflow/checkout`, `npm run check:ui` and
  `npm run check:boundaries`. Expected: PASS. Commit isolated checkout.

### Task 11: Package local operations and record scoped acceptance

**Files:** `compose.yaml`, `apps/api/Dockerfile`, `deploy/{nginx.conf,network-policy.md}`,
`README.md`, `docs/operations/{local-development,configuration,recovery,release,verification}.md`,
`docs/integrations/{pixelcore,medframe,dineease}.md`, `.github/workflows/checks.yml`.

**Interfaces:** `docker compose up -d postgres redis` starts isolated data services;
documented native API/worker/scheduler/frontend dev commands start processes
without production builds. `recover_events` and reconciliation commands preserve
operation/event identity. CI separates checks from opt-in release builds.

- [ ] Document environment/keyring setup, migration ordering, owner onboarding,
  merchant registration, provider callbacks, secure cookies, network egress,
  backup/restore and the difference between mock tests, account sandbox and live.
- [ ] Add configuration checks for production secrets, host/return origins,
  trusted proxy configuration, HTTPS cookies and disabled development exceptions.
  Validate compose syntax without building images or affecting host databases.
- [ ] Run one accumulated targeted verification pass after all new changes:
  backend domain/API tests on PostgreSQL, Python/TypeScript SDK tests, frontend
  component/type checks, UI/import-boundary checks, Django system checks and
  static design audits. If a new failure requires a correction, rerun only the
  affected checks. Do not repeat passing broad checks without a new reason.
- [ ] Generate a task-scoped graphify map in the new repository; exclude keys,
  environment files, dependencies and generated artifacts. Record exact coverage,
  graph health warnings and real token accounting. Use code-only AST extraction
  so graph work requires no agents. Save sanitized Jev judgments as advisory evidence.
- [ ] Record exact commands/results, incomplete acceptance, gateway prerequisites
  and no host cutover in `docs/operations/verification.md`. Mark completed plan
  steps truthfully. Commit the independently runnable MVP; do not push, publish,
  deploy or claim live merchant acceptance.

## Plan self-review and acceptance boundaries

- Spec coverage: Tasks 1–2 own scope/records/cash; 3–5 own provider lifecycle and
  refunds; 6 owns durable events/recovery; 7 owns API/SDK/examples; 8–10 own the
  selected frontend and checkout boundary; 11 owns operations/compatibility.
- The five Review Focus cases have named tests in their owning tasks.
- The same Scope/Money/status names and operation identities travel across
  tasks. API serializers and OpenAPI precede SDK/UI consumption.
- No real provider keys, payment requests, patient records, host mutations or
  production activation are prerequisites for writing/test-running the MVP.
- A passing mock suite establishes implementation behavior only. Real sandbox
  and live gateway acceptance remain explicitly unverified until authorized and
  configured; account terms/eligibility cannot be inferred from code.
- UI direction remains a user selection under Impeccable. Until then backend,
  SDK and operations tasks can proceed after plan approval.

## Tooling evidence for this planning change

Graphify queried existing PixelCore `payment invoice order` concepts; its capped
result was truncated and was not treated as complete impact coverage. Existing
source evidence remains in the specification. Jev selected `invariants` as the
verification priority with confidence 1.0 (442 input / 43 output tokens); input
contained generic architecture only. No tests, builds or browser/manual checks
were run for this documentation-only change. No agents were used.
