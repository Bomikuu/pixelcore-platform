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
