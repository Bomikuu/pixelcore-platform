# Smokey business assistant design

Date: 2026-10-26
Status: proposed specification; conversational scope approved, written-spec review pending

## Purpose and agreed requirements

Smokey is an optional, reusable reporting assistant installed into PixelCore. A
business brings its own provider credentials, selects its AI model and mascot,
and asks questions about records it is authorized to access. Supported requests
include a daily business report, sales and order totals, who attended today, and
who arrived late today. Answers have a quick chat presentation and a full report.

The user approved the module boundary and first-release scope on 2026-10-26 and
added these requirements:

- Multiple AI providers are available from launch.
- The dashboard is white-first, with dark theme capability.
- Use Tailwind CSS and shadcn/ui for dashboard controls.
- The mascot communicates loading and searching progress.
- Support a right drawer and modal, with a full generated report page.

This is an extension of the existing products, not a replacement identity.

## Current implementation evidence

- `SmokeyChatbot/backend/core` implements a standalone Django website chatbot.
  `Site` belongs to an owner account; model and OpenAI credentials currently come
  from server settings. Public widget endpoints use site IDs and origin checks.
- `SmokeyChatbot/dashboard` already uses React, TypeScript, Tailwind CSS v4 and
  generated shadcn/ui components. Appearance, knowledge, installation and usage
  already exist. Many components use fixed light colors, so dark support needs
  semantic tokens across the dashboard rather than just a theme switch.
- PixelCore optionally loads Website Builder as an installed Django app with
  authorization and data hooks supplied by `content/builder_bridge.py`.
- PixelCore has business memberships, capability states, business timezones,
  attendance records with explicit lateness fields, and reporting/analytics code.
- PixelFlow provides a separately hosted service and thin SDK pattern. That is
  useful precedent for packaging, but the proposed Smokey runtime uses the local
  installed-module pattern to reuse host authentication and records directly.

Graphify was used to trace business, membership, capability and attendance
relationships; current source was read directly to verify its findings. Jev
judgments used generic, secret-free requirements as advisory input only.

## Architecture and repository ownership

Keep reusable assistant code and assets in
`/home/micxsz/projects/SmokeyChatbot`. Introduce a uniquely named Django package,
`smokey_assistant`, rather than installing the standalone app named `core` into
another project. PixelCore owns a small host adapter and its business data queries.

The shared package owns provider adapters, encrypted credential persistence,
assistant settings, request state, report snapshots, usage accounting and mascot
assets. It must not import PixelCore business, attendance, sales or user models.

The host adapter supplies authenticated tenant resolution, action authorization,
available report tools, validated data resolution, timezone and source links.
Tenant identity is derived from the authorized host context, never from an AI
response. Every tool invocation, report read and settings mutation rechecks host
authorization. Disabled modules reject requests as well as hiding their UI.

PixelCore has two distinct installation states: the package is installed on the
server, and a business explicitly enables its Smokey capability. Package presence
does not enable Smokey for every business. A missing optional package must not
break unrelated PixelCore routes.

The standalone Smokey React dashboard retains its existing account and public
website workflows. Its reusable assistant services are shared with host mode.
PixelCore's integrated Smokey dashboard uses its native Nuxt and shadcn layer,
its existing login and active business; users do not need a second Smokey login.
Both clients use the same configuration and report schemas. Host mode never
links a business to an arbitrary public site ID.

## First-release scope and authorization

Owners and admins enable the module and manage credentials, default provider,
default model, permitted models, limits and mascot appearance. Owners, admins and
managers can generate and view business reports, subject to the host's report
permissions. Changing the provider or credential is an administrative operation.
Staff self-service reporting is outside this first release.

Supported report tools are daily business overview, sales/order totals, attendance
for a date range, and late arrivals for a date range. Daily overview combines
available sales and attendance facts. A source that is unavailable or unauthorized
is explicitly identified as unavailable; it is never silently interpreted as zero.
Other report categories and record-changing actions are outside this release.

## Providers, credentials and model selection

Ship adapters for OpenAI, Anthropic, Google Gemini and OpenRouter. Each adapter
normalizes model capabilities, request results, token usage, cancellation limits
and errors. Provider-specific API details and model availability must be verified
against current official documentation during implementation; do not copy the
standalone README's model identifier as a supported-model guarantee.

One business may configure several provider connections and choose an active
connection and model. The server validates that a model belongs to the chosen
provider and supports the structured generation required by the assistant.
Credentials are encrypted at rest with a deployment-managed encryption key kept
outside the database, never returned by read APIs, never logged, and never sent
to browser storage. APIs return only a masked suffix and configuration status.
An explicit connection check reports authentication, unavailable model, provider
quota and connectivity errors without exposing upstream secrets.

Use fixed provider destinations; arbitrary endpoint URLs are outside this scope.
Do not silently fall back to another business's key, a platform key, provider or
model. Existing standalone legacy configuration must be explicitly scoped to the
legacy website experience and cannot fund internal business reports.

## Reporting pipeline and factual boundaries

1. Authenticate the user, resolve the active business, and verify module access.
2. Resolve the requested report type and date range into a validated plan. AI may
   classify a free-text request, but only allowlisted report tools can execute.
   Ambiguous unsupported requests return a clarification, not invented results.
3. Reserve quota and establish an idempotent generation request before any AI call.
4. Execute business-scoped host queries and construct a bounded fact snapshot.
5. Generate explanatory prose from those facts using the chosen provider/model.
6. Validate the response schema and save a private report plus usage outcome.

PixelCore computes totals and attendance classifications. Authoritative metric
tiles and tables render from the fact snapshot; AI prose cannot replace their
values. Source links are supplied by the host and allowlisted, not invented by
the model. No generated SQL, Python, HTML or arbitrary HTTP requests execute.
Names and user-provided fields are untrusted content and render as text.

"Today" means the business's local calendar date with explicit timezone and UTC
query boundaries. Attendance means distinct employees with a qualifying clock-in
in the selected period; currently clocked in is a separate metric. A late employee
is identified using recorded lateness, not an AI inference from a name or schedule.
Show excused lateness separately and do not infer absence from a missing clock-in.
Repeated shifts must not inflate distinct-employee totals. Missing records are
reported as missing information, not proof that an employee was absent.

Only fields needed for the selected report are included in provider input. Omit
attendance reasons, employee documents, contact details and unrelated records.
Bound record counts and mark truncation or pagination explicitly. The provider
summarizes the complete authoritative aggregates even when detail rows paginate.

## Dashboard and report interaction

The integrated navigation contains Overview, Assistant, Reports, Appearance,
AI connections, and Usage. Each page has one clear main task. The first-run flow
is enable module, add/test connection, choose model, choose mascot/presentation,
then run a suggested report. A saved but untested or invalid connection cannot
appear as ready.

The assistant drawer preserves the underlying workspace. The modal is an
alternative presentation of the same conversation state, not a separate chat
implementation. The business selects a default presentation. On narrow screens,
both become a full-height sheet with a reachable close control and composer.
Switching business clears conversation and active report state before loading the
next business. Switching presentation does not duplicate an in-flight request.

Suggested prompts include "Summarize today's business", "Who attended today?",
"Who arrived late today?", and "Show today's sales totals". Show the resolved
date range and source categories alongside the answer. Open full report navigates
to an authenticated report detail page with a title, generated timestamp, business,
timezone, model, factual totals, narrative, detail tables and source links.

Reports are private snapshots, never public links. Report history records who
generated the result. Regenerating creates a new snapshot and clearly communicates
that it consumes usage. Refreshing or reopening an existing report makes no AI
request. Automatic exports and public report sharing are outside this release.

## White-first theme and shared components

Default to Light. Offer Light, Dark and System, persist the preference locally,
and apply it before the first visible render. A failed storage write must not
prevent theme switching. System mode follows operating-system changes.

Light surfaces are predominantly white with quiet neutral canvas areas, readable
slate text and restrained cobalt accents in standalone Smokey. PixelCore retains
its existing typography and business brand accents. Dark mode uses explicit
semantic background, surface, border, text, focus and status tokens throughout;
fixed white backgrounds must not leave isolated light panels in dark mode.
Charts, tables, dialogs, popovers, forms and loading/error states all inherit theme.

Use Tailwind CSS and shadcn/ui. The standalone dashboard keeps React and TypeScript,
officially generated shadcn primitives, arrow-function conventions and focused
feature files. PixelCore uses its canonical `components/ui` primitives, including
ButtonLink/ButtonAnchor for action links. Do not add raw application form or table
primitives. Preserve keyboard navigation, visible focus and 320px usability.

## Mascot progress and request lifecycle

Use a shared state contract across the drawer, modal, dashboard preview and report
page: idle, searching, generating, success, empty, error, and cancelled. Statuses
must reflect actual server work; never advance through a staged animation while
the server is still doing something else. No fabricated percentages or timers.

- Searching: mascot investigates; text says "Checking today's attendance..." or
  names the actual report source being queried.
- Generating: mascot thinks or speaks; text says "Writing your summary...".
- Success: a brief acknowledgment, followed by the readable result.
- Empty: a calm pose and an explicit no-records explanation.
- Error: a settled pose with a useful error, preserved prompt and explicit Retry.
- Cancelled: stop motion and say "Generation stopped".

Existing sprite frames may be reused; distinct feedback must not depend on new
artwork or unavailable animation frames. Static custom mascots use a small status
indicator and the same text. The standard launcher uses the same progress contract.
The mascot remains within its progress area while a request is pending rather
than roaming across controls. It never hides the prompt or resulting data.

Pair visual state with a polite accessible live status. Announce state transitions,
not every poll or animation frame. Reduced-motion mode displays a static pose.
Pending requests prevent accidental duplicate submission and expose Stop. A stop
request prevents saving or presenting a later result even if the provider cannot
abort a request already in flight; consumed provider usage is still recorded.
Closing a panel preserves the active request and allows reopening; stopping it is
an explicit action. Navigation or business changes cannot attach a stale result
to another business.

Use persisted server request state and bounded polling for the first release.
Run generation in the host's background task facility so progress endpoints remain
responsive. Polling stops at a terminal state or on unmount. Reconnecting can
recover the request by its opaque ID after rechecking authorization.

## Usage, failure handling and operational controls

Record generation ID, tenant, actor, connection, provider, model, timestamps,
outcome, input/output tokens when supplied, and categorized errors. Include plan
classification calls as well as summary calls. Failed, cancelled and retried
requests remain visible; absent token usage is unknown, not zero.

Show daily/monthly requests and token usage by connection/model, plus configured
request/token limits. Estimates must be labeled and based on a dated rate table;
the app does not claim to show the provider's exact invoice or remaining balance.
Implement request and token budgets with atomic reservations so concurrent calls
cannot simply bypass limits. Release unused reservations and reconcile actual
usage, including cancellation races.

Handle missing credentials, invalid credentials, inaccessible models, permission
loss, no records, provider quota, timeout and upstream failure separately. Never
automatically retry a billed generation. Explicit retry creates a new attempt;
network resubmission with the same idempotency key returns the original attempt.
Audit configuration changes without recording secret values or sensitive prompts.
Reports remain business-scoped and deletable by owners/admins. Do not store raw
provider request/response bodies in routine logs.

## Verification and delivery constraints

Implement focused automated coverage for tenant isolation, role checks, module
disablement, credentials never appearing in output, provider selection, schema
validation, timezones, distinct attendance counts, excused lateness, empty data,
idempotency, concurrent quotas, polling terminal states, cancellation races and
stale business responses. Mock provider calls; real paid calls are opt-in.

PixelCore policy requires targeted automated checks and
`npm run check:ui` after frontend changes. Smokey's local policy prohibits running
test suites unless requested, so use focused static/type checks there and describe
unexecuted suites accurately. Documentation-only changes need no application tests.
Do not run either project's production builds, browser inspections, visual tests
or manual verification unless the user explicitly requests them.

Preserve existing uncommitted work and the public website chatbot. Do not modify
the protected `/home/bomiku1/projects/dineEase-web` source. Document package
installation, required encryption configuration and business enablement; production
asset packaging must be verified when a build is explicitly authorized.

## Acceptance criteria

1. A business explicitly enables an optional Smokey module and configures its own
   connection; another business cannot read or spend that connection.
2. All four providers have implemented, mock-verified adapters with server-validated
   model selection; unsupported provider capabilities produce a clear error.
3. An authorized user can request the supported reports through either presentation
   and open a private full report with authoritative facts and source links.
4. Search and generation show truthful mascot feedback, text status, accessible
   announcements and reduced-motion behavior, including failure and cancellation.
5. The white-first dashboard supports persisted Light/Dark/System settings across
   all surfaces and uses each project's Tailwind and shadcn component boundary.
6. Usage records attempts and available tokens without leaking credentials or
   claiming provider billing accuracy; limits apply under concurrent requests.
7. Focused permitted checks pass, and any unexecuted checks are reported explicitly.

## Review checkpoint

This written spec is ready for user review. Implementation planning begins after
written-spec approval; product code has not been changed for this design.
