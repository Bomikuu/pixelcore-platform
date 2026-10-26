# PixelCore

PixelCore is a configurable business-operations foundation built from the proven Django, Nuxt, PostgreSQL, Redis, and Docker technology used by DineEase. It is a separate project: the DineEase source repository is not modified by PixelCore development.

PixelCore is a functional superset of the reusable DineEase workflows. Restaurants are supported through an optional preset; the shared domain remains generic so retail, services, and hybrid businesses are not forced into restaurant terminology.

- Django-managed business identity and branding.
- Business-scoped owner, administrator, manager, and staff memberships.
- Structured Site/CMS pages with immutable revisions, signed previews, publishing, reusable assets, bounded 3D blocks, SEO metadata, platform subdomains, and verified custom domains.
- Sell workflows for physical, digital, and service offerings, guest carts, orders, fulfillment, COD/manual payment, and merchant-owned PayMongo checkout.
- Schedule workflows for staff, availability, capacity-limited sessions, bookings, reminders, and the existing Google Calendar bridge.
- Operate workflows for multi-location inventory, purchasing, quotations, invoices, expenses, and actual-record reporting.
- Display Studio for catalog boards, promotional posters, information screens, QR catalogs, and the restaurant-oriented Poster Menu template.
- Generic resources and layouts for tables, rooms, equipment, and other reservable capacity.
- Workforce records for employee codes, documents, attendance, leave, flags, and paired attendance terminals.
- Counter POS, customer displays, modifier groups, promotions, customer portals, and optional food nutrition/cost profiles.
- Background work through Celery and Redis, local development media, and S3-compatible production storage.

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for architecture and [DESIGN.md](DESIGN.md) for product/UI rules.

## Current product surfaces

PixelCore connects customer-facing experiences with the records and workflows
used to run the business behind them.

### Site and brand

- Structured page builder with draft revisions, private previews, publishing,
  domains, SEO settings, reusable media, banners, popups, and hero carousels.
- Luxury and marketplace storefront layouts that share the same catalog and
  business identity.
- Public digital business cards with generated or uploaded backgrounds,
  typography controls, social profiles, QR sharing, and print-ready sides.
- Poster and display studio for promotional screens, information boards, QR
  catalogs, and restaurant-oriented menu displays.

### Commerce

- One catalog for physical products, digital products, bookable services,
  variants, categories, collections, media, inventory rules, and promotions.
- Product detail pages with gallery media, pricing, discount percentages,
  reviews, wishlists, customer accounts, delivery details, reservations,
  rentals, requests, and cart actions.
- Customer records, orders, product requests, live sales reporting, and
  role-specific POS, customer-display, fulfillment, and delivery screens.

### Scheduling and events

- Public booking requests, monthly and daily calendars, staff availability,
  capacity, resources, and reusable venue layouts.
- Restaurant seating and event layouts with tables, stages, entrances, bars,
  dance floors, service areas, and custom elements.
- Dedicated event workspaces for details, staff, products, tasks, venue plans,
  guests, seating, organizer access, and RSVP automation.
- Public wedding and event websites with invitation popups, countdowns,
  participants, stories, timelines, maps, galleries, wishes, music, and
  standalone RSVP pages.

### Operations and workforce

- Inventory by variant and location, suppliers and their catalogs, purchase
  orders and receiving, quotations, invoices, expenses, attachments, reports,
  due-date attention, and connected-record workflows.
- Employee profiles, email invitations, onboarding, attendance terminals,
  generated clock codes, leave, vacation, documents, team access, and event or
  service assignments.

The main workspace starts at `/workspace`. Published customer experiences use
`/site/{business-slug}`, `/card/{public-id}`, `/event/{event-id}`, and
`/display/{share-key}` routes.

## Repository structure

```text
pixelcore-frontend/   Nuxt 3 client application
pixelcore-backend/    Django REST API and admin
nginx/                Local development proxy templates
Caddyfile              Production custom-domain/TLS edge
docker-compose.yml    Local service topology
```

## Local setup

### Lightweight development (no Docker)

From the repository root, run:

```bash
npm run dev
```

Requires Node.js 20.19 or newer, npm, and Python 3.11 or newer with `venv`
and pip (or `uv`, which the command uses when available). On Debian/Ubuntu,
install the matching `python3-venv` package if `ensurepip` is unavailable
and you do not use `uv`. Set `PYTHON=/path/to/python3` to choose the
interpreter used to create `pixelcore-backend/venv` on the first run.

The command creates the backend virtual environment and installs backend
and frontend dependencies on the first run, then refreshes them when the
requirements or frontend package files change. No root `npm install` is needed.
It runs Django system checks, rejects model changes missing migration files,
applies pending migrations, and verifies the database is up to date before
starting Django and Nuxt with hot reload. A failed check stops startup.

- Frontend: `http://localhost:3001`
- API: `http://localhost:8000/api/`
- Admin: `http://localhost:8000/admin/`

Press Ctrl+C to stop both servers. If either server exits, the command also
stops the other. Ports 3001 and 8000 must be available.
Stop an existing Compose stack with `docker compose down` before switching
to the default local ports (this preserves named database volumes). To use
other ports, set `PIXELCORE_FRONTEND_PORT` and `PIXELCORE_BACKEND_PORT` in
`.env.local` or the shell; API URLs and allowed origins follow those ports.

This mode uses `pixelcore-backend/db.sqlite3`, local media storage, and
synchronous Celery tasks. Verification and reset emails print in the same
terminal. It starts no PostgreSQL, Redis, worker, scheduler, proxy, or Docker
services. Scheduled reminder and reservation-cleanup jobs do not run
automatically; use the Compose stack when developing those jobs or testing
PostgreSQL behavior. SQLite has separate data from the Docker database.
Django warns that SQLite skips the `nulls_distinct` unique constraints on
`OfferingMedia` and `CartItem`; validate those constraints against PostgreSQL.

Optional integration values and the Django secret are read from root `.env`,
then `.env.local`, then the shell environment. These files are parsed as
dotenv data. The command overrides database, task, email, storage, debug,
and local URL settings for this mode, so an existing Docker `.env` can be
reused. If no Django secret is configured, a temporary development secret
is generated for that run. Keep a secret in `.env.local` for stable sessions
across restarts. Docker and production settings are unaffected.

To set up dependencies and run the same checks and migrations without
starting either server:

```bash
npm run dev:check
```

### One month of sample data

Run this from the repository root to populate the local SQLite database:

```bash
npm run seed:demo
```

The command sets up backend dependencies, checks and applies migrations,
and imports the current month in `Asia/Manila`. It does not build either
application, start servers, install frontend dependencies, or start Docker.
Start the apps separately with `npm run dev`.

Default demo access:

- Email: `monthly.demo@example.test`
- Initial password: `PixelCoreDemo123!`
- Business: **Northline Supply Co. — Demo**
- Storefront: `http://localhost:3001/site/northline-monthly-demo`

To select another month or attach the separate demo business to an existing
account without changing that account's password:

```bash
npm run seed:demo -- --month 2026-10
npm run seed:demo -- --owner-email your-existing-account@example.com
```

Choose the current month or a past month. Reimporting a month refreshes its
generated records using stable identifiers; it does not create duplicates,
reset existing account passwords, or adopt an unrelated business. Importing
another month adds that month's history while reusing the catalog and team.
An existing demo business must be imported with its original owner. Staff
accounts have unusable passwords; the owner account is the demo login.

The [monthly fixture](pixelcore-backend/businesses/fixtures/monthly_demo/dataset.json)
includes six products with eleven variants, three services, 24 customers,
eight staff members, three suppliers, 120 retail orders, eight purchase
orders, twelve service invoices, six quotations, twelve expenses, forty
bookings, four events with guests, attendance and leave, a published
storefront, and two display publications. Retail payments, invoice payments,
receipts, reservations, returns, and stock balances are connected and
reconciled. Transaction dates are distributed over the elapsed portion of
the chosen month; bookings and events span the whole month. Future bookings
are pending or confirmed. Attendance includes only elapsed scheduled days.

Eight original AI-generated PNG photographs are bundled beside the fixture,
with their prompts in `image-prompts.json`. They are copied into local media
on import and reused on subsequent imports. No external image URLs, email,
payment requests, or calendar integrations are used. All identities,
products, suppliers, transactions, and imagery are fictional. This importer
is restricted to development environments with `DEBUG=True`.

This is an application JSON fixture rather than a raw `loaddata` dump: the
importer resolves references, dates and media while avoiding primary-key
collisions. See its [fixture guide](pixelcore-backend/businesses/fixtures/monthly_demo/README.md).

Docker uses its own PostgreSQL database and named media volume. To populate
that environment, run `docker compose exec backend python manage.py seed_month_demo --month 2026-10`.
If records already exist there but images are missing, run
`docker compose exec backend python manage.py seed_month_demo --media-only`
to restore only the images without refreshing activity. Files in the host's
`pixelcore-backend/media` folder are not automatically copied into Docker's
named media volume.

### Docker development

1. Copy `.env.example` to `.env`.
2. Replace both secret placeholders.
3. Start the development stack:

```bash
docker compose up --build
```

Compose automatically merges `docker-compose.override.yml` for local development. `dc.dev.yml` contains the equivalent explicit development overrides for environments or scripts that select Compose files with `-f`:

```bash
docker compose -f docker-compose.yml -f dc.dev.yml up --build
```

Local endpoints:

- Nuxt: `http://localhost:3001`
- Django API: `http://localhost:8000/api/`
- Django admin: `http://localhost:8000/admin/`
- Nginx: `http://localhost`
- PostgreSQL: `localhost:5433`
- Redis: `localhost:6379`

Celery workers and the reminder/reservation beat scheduler start with the Compose stack. Production uses `dc.prod.yml` and Caddy; configure the domain authorization token and storage credentials before deployment.

During local account registration, verification and reset codes are sent through the console email backend. Read the `worker` service logs to retrieve the six-digit code:

```bash
docker compose logs -f worker
```

After onboarding, restored workflows are visible under `Site → Displays`, `Sell → POS`, `Schedule → Calendar/Resources`, and `Operate → Workforce`. Dedicated paired screens are available at `/poster-menu`, `/pos-terminal`, `/customer-display`, and `/attendance-terminal`.

## Storefront and payments

Published sites are available locally at `/site/{business-slug}`. Production resolves platform subdomains and verified custom domains, while authenticated workspace routes remain client-rendered. Public storefront pages are server-rendered for discoverability.

PayMongo credentials belong to each merchant, are encrypted at rest, and are never returned by the API. Checkout totals are recalculated by Django, and fulfillment waits for a verified, replay-windowed, idempotent webhook. COD and manual bank payments are supported without a provider connection.

Invoices, quotations, receipts, and reports created by PixelCore are operational/commercial records. They are not represented as substitutes for BIR-authorized invoices or receipts, tax filing, or accounting certification.

## Google Calendar

Google Calendar is optional. Configure a Google OAuth web client with this local callback:

```text
http://localhost:8000/api/google-calendar/callback/
```

Then set `GOOGLE_CALENDAR_CLIENT_ID`, `GOOGLE_CALENDAR_CLIENT_SECRET`, and `GOOGLE_CALENDAR_REDIRECT_URI` in `.env`. Tokens are encrypted before database storage. Synchronization is currently one-way from PixelCore business events to Google Calendar.

## Security baseline

- Secrets are required from environment variables.
- Access tokens stay in browser memory; refresh tokens use an HttpOnly cookie.
- Private business queries are membership-scoped.
- Identity changes require owner or administrator access.
- Branding JSON is allowlisted and validated.
- Logo, favicon, and cover uploads accept JPG, PNG, or WebP up to 5 MB.
- Public identity responses exclude legal business names and internal membership data.
- CMS content is versioned JSON with allowlisted block settings; arbitrary HTML, JavaScript, CSS, shaders, and remote URLs are rejected.
- Public tenant responses are explicit serializers rather than private model dumps.
- PayMongo signatures are verified against the raw request body with replay and duplicate-event protection.

## Shared visual website builder

The separate `../website-builder` checkout of [PixelCore Studio](https://github.com/Bomikuu/pixelcore-studio) supplies PixelCore's Vue studio and shared Django revision/review service. From this repository root, clone it into the sibling directory expected by the package links and Docker contexts:

```bash
git clone https://github.com/Bomikuu/pixelcore-studio.git ../website-builder
```

Keep the two checkouts beside each other, install frontend dependencies with `npm install --ignore-scripts`, then use the normal root `npm run dev`; its migration check includes the shared package. No extra service or Docker container is needed. See [the builder README](https://github.com/Bomikuu/pixelcore-studio#readme) for standalone setup and adapter documentation.

Open **Workspace → Site → Visual studio**, a page editor's **Visual studio**, or an event's **Website → Visual studio**. The first open creates a visual draft from existing content. Actual catalog and event fields are connected through the host adapter. Saving changes the draft; explicit **Publish** selects the shared layout on the existing public URL. Publishing from the older editor selects its renderer again without deleting the visual draft. Advanced legacy music/3D features remain available through that editor.

Guest review links show an immutable saved revision and data snapshot. Reviewers enter a name to pin comments and reply; account holders with management access can resolve threads. Expired/revoked links and withdrawn assets are rejected.

The shared React adapter is ready for a later Medframe rollout; this pass activates PixelCore only. Free-form layout remains experimental and disabled pending the planned browser performance checks. Automated checks are the default; no builds or visual inspections should be run without an explicit request.
