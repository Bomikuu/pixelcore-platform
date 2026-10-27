# Smokey business assistant

Smokey is an optional reporting module maintained in the sibling
`SmokeyChatbot/python` package. Open `/workspace/smokey` to enable it for the active
business. Package installation alone does not enable business access.

The module supports OpenAI, Anthropic, Gemini and OpenRouter connections. Each
business supplies its own credentials. The first successful connection check selects
that connection as default when none is selected; later checks preserve the existing
choice. Saving an untested key alone never enables generation. Migration
`0004_verified_default` repairs earlier setups only when a business has exactly one
ready connection with a permitted model and no default. Ambiguous setups still
require an explicit selection. There is no platform API-key fallback. See the sibling project's
`docs/PIXELCORE-INTEGRATION.md` for installation, encryption and host contracts.

## Deployment configuration

- Install `smokey-assistant` in the host environment, or use the development source
  path `SMOKEY_PYTHON_PATH` / `SMOKEY_ROOT/python`.
- Configure `SMOKEY_ENCRYPTION_KEYS` using deployment secrets. The first key writes;
  additional keys support decryption during rotation. Retain backups of these keys.
- Apply `businesses` and `smokey_assistant` migrations before enabling the module.
- Restart Celery worker/beat processes after installing the package. The current
  Compose source mounts require recreating affected services to take effect; no
  application build is needed for the development mount.
- Use PostgreSQL for production transactional quota and duplicate-worker protection.

## UI and behavior

The dashboard is white-first and reuses the workspace's theme controller with
Light/Dark/System choices. In module mode, AI connections, Appearance, Usage and Reports are mounted directly
from the shared Smokey React/Tailwind v4/shadcn source through isolated Shadow DOM
surfaces. PixelCore owns the host shell and resolved theme. Standalone Smokey keeps
its independent login and Light/Dark/System preference. Temporary legacy mode
retains the earlier Nuxt screens until the gated production cutover.

The header's **Ask Smokey** action opens a right drawer or modal according to
business settings. Both share one request state. On narrow screens the surface is
full height. The mascot pairs genuine searching/generation state with text,
accessible announcements and a reduced-motion fallback. Closing preserves a
request; Stop explicitly cancels publication. Switching business clears its UI.

Reports include business-local dates/timezone, authoritative totals, an AI summary,
immutable paginated detail and source links. A missing clock-in is not treated as
proof of absence. Sales value is distinct from collected invoice payments.
Reading existing reports never sends an AI request. Regeneration explicitly does.

Usage counts provider calls, not just saved reports. It includes connection
checks, classification, failed calls and unknown token outcomes. Reservations may
include potentially billed calls whose usage could not be recovered. This is not
the provider's exact invoice, remaining balance or an employee attendance judgment.

## Targeted checks

The test settings use a test-only encryption key and isolate PostgreSQL tests in
`test_smokey_assistant`. Never point checks at a production database. Run the seven
`businesses.test_smokey_*` modules, the three frontend `utils/smokey*.test.mjs`
modules, and `npm run check:ui`. Standalone validation is `npm run typecheck`.
Provider transport is mocked; real paid calls are opt-in. Builds and browser/visual
inspections remain outside the current verification authorization.

## Canonical UI map and behavior contract

The approved design spec is the authority for permission, billing, report retention
and cancellation behavior. The following map records UI consequences, not a new
platform-wide design system.

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | `components/ui/select` | Existing workspace shadcn layer | Authored Radix popup | Template compilation; browser geometry unverified |
| Date | `components/ui/input` | Business ISO local-date API contract | Browser-native date input and popup | API boundary tests; native popup locale unverified |
| Form | `smokeySettings.js`, shared Label/Input/Textarea, backend serializers | Assistant settings API | Explicit local guards plus server validation; no native bubbles | Utility tests and API tests |
| Scrollbar | Existing workspace stylesheet and semantic theme tokens | Workspace design system | Native overflow for saved tables and bounded conversation | Static source inspection; computed styles unverified |
| Toast | Shared live status and inline alert regions | Approved feedback contract | Persistent errors and transition-only status text | Source contract and controller checks |
| CRUD | Business-scoped API and `useSmokeyResource` | Approved permissions and snapshot lifecycle | Paginated list/detail; explicit delete confirmation | PostgreSQL API tests |

Theme ownership stays in `useWorkspaceTheme`; the assistant reads the actual Nuxt
storage key and defaults to light only on first use without an existing choice.
Provider credentials remain component memory until sent to the authenticated API;
they never enter URLs or persistent browser storage. Owner/admin mutations have
pending feedback; Stop and failed-network recovery preserve the original request
identity. Drawer and modal use the same controller and canonical overlay semantics.

The broad Premium static audit is not a clean project-wide result: it flags
existing application forms/ownership contracts and also treats capitalized shadcn
`Select` components as native selects. Those authored controls are confirmed by
their imports. The scoped Impeccable detector reported no issues for the new
PixelCore surfaces. Neither audit proves rendered appearance or keyboard behavior.


## Shared module rollout — 2026-10-27

Local development defaults to the shared module. Production base configuration
retains `legacy` / `release` until actual artifact and browser acceptance pass.
`NUXT_PUBLIC_SMOKEY_UI_MODE`, `NUXT_PUBLIC_SMOKEY_UI_SOURCE` and
`NUXT_PUBLIC_SMOKEY_UI_MANIFEST` are forwarded to the frontend by Compose. There is
no iframe or separate generation controller in module mode. One persistent React
runtime serves all seven existing routes, the floating lower-right mascot and the
header chat toggle. Ordinary compatible UI changes are authored in Smokey.

The always-registered authenticated `smokey-integration/` descriptor reports package
presence, enablement, supported reports and current member permissions without
reading private settings or importing optional models. The host adapter maps
named operations to scoped APIs and rejects late results after context changes.

From this repository, start only the optional module service:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.smokey-ui.yml up -d --no-build smokey-ui
```

Open [PixelCore Smokey](http://localhost/workspace/smokey), or the standalone
[Smokey login](http://localhost:5173) when its usual Vite service is running.
Nginx proxies `/smokey-assets/dev/` to the optional internal Vite service and mounts
`../SmokeyChatbot/releases/ui` read-only for versioned production assets. Nuxt also
bridges asset GET/HEAD requests for direct port 3001 development access.

Canonical guides in the sibling repository:
[setup](/home/micxsz/projects/SmokeyChatbot/docs/SHARED-FRONTEND.md),
[release and rollback](/home/micxsz/projects/SmokeyChatbot/docs/SHARED-FRONTEND-RELEASES.md),
[verification / pending gates](/home/micxsz/projects/SmokeyChatbot/docs/SHARED-FRONTEND-VERIFICATION.md).

The legacy form/CRUD ownership map above describes the earlier implementation;
in module mode these features and overlays live in Smokey `src/features/business`
and `src/sdk`, using the backend as authority. Do not maintain parallel feature UI.
Remove legacy Vue components/helpers only after the approved cutover gates pass.

### Shared dashboard audit and refinement — 2026-10-27

The canonical shared UI now includes real-data overview summaries, quota/model/token
charts, provider marks and connection badges, card-based provider/model selection
in a scoped add/edit dialog, supported report suggestions, and standalone footer
account/theme controls. Model prices are dated exact-ID references with labeled
single-call examples and unavailable-price fallbacks, not invoice totals.

A shared Shadow DOM focus bridge fixes dialog Tab containment and nested focus
return in the embedded module. PixelCore retains its existing account/theme footer.
See the sibling [audit and verification report](/home/micxsz/projects/SmokeyChatbot/docs/SMOKEY-UI-AUDIT.md)
and [canonical UI contract](/home/micxsz/projects/SmokeyChatbot/docs/SMOKEY-UI-CONTRACT.md).
Focused type/insights/render/surface checks and synthetic desktop/mobile/embedded
browser flows passed; no build or live paid-provider request was run. The scoped
Premium static report retains one documented false positive for the authored
React Select wrapper.

### Manual credits and compact surfaces — 2026-10-27

AI connections support a manually recorded total of funded USD credits. The optional
package's `0003_connection_credits` migration adds the nullable decimal field.
Connection reads return tenant-scoped lifetime model usage; the shared UI estimates
recorded token costs against the entered total and flags incomplete data. This is
manual tracking rather than a provider balance or enforced spending cap. Credit-only
PATCH requests preserve verification/default readiness and connection revision.
Visible, idle connection lists refresh every 30 seconds using the host API.

Smokey content now uses the available main width with a single gutter. PixelCore
opts into the SDK's optional `pageHeader: "host"` so WorkspaceShell owns section
breadcrumbs/descriptions; standalone and other SDK hosts use their shared header.
Overlay suggestions use compact rows, while the full page retains descriptions.
Mascot cards show appearance previews and keep save explicit. A Shadow DOM-only
Tailwind property fallback restores embedded borders, spacing and modal centering.

The additive migration was applied locally. Three targeted API tests, the focused
shared UI checks, six host-loader/lifecycle checks, UI boundary checks and synthetic
desktop/mobile/embedded browser checks passed. No builds or paid provider calls ran.

### Session conversations and report layout — 2026-10-27

The shared UI retains the last 30 chat turns and current draft in scoped tab-session
storage. User and Smokey messages have circular avatars. Navigating between full
chat, reports and overlays keeps the conversation; refresh restores it without
new provider calls. Business/access changes and logout clear the relevant private
state. Report summaries continue to load through authenticated report endpoints.

New report snapshots include sales/attendance daily series and payment-status
aggregates computed on the server, plus product transaction rows and image
references where available. Older reports remain valid and explain when chart
data is absent; explicit regeneration adds new snapshot fields. No comparisons
or unavailable categories are invented. Saved-row APIs accept a scoped search
and page_size of 20, 50 or 100; both adapters forward these validated fields.
The report UI uses consistent icon tiles, hover transitions, image fallbacks and
explicit current-page CSV export. No database migration is needed for these JSON
snapshot additions.
