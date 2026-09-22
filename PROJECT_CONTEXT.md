# PixelCore Project Context

Status: hybrid-business platform implementation
Last reviewed: 2026-09-05

## Product boundary

PixelCore is a general business platform and a functional superset of DineEase. Restaurant workflows are supported through an optional preset that supplies vocabulary and starter templates without restricting capabilities. There is no PixelCore-wide restaurant discovery marketplace.

The project was created as a sibling clone so committed and intentional uncommitted engineering could be evaluated and reused without writing to `/home/bomiku1/projects/dineEase-web`. Reusable workflows are rebuilt on generic business, location, offering, resource, workforce, and device abstractions.

## Architecture

| Area | Location | Responsibility |
| --- | --- | --- |
| Nuxt frontend | `pixelcore-frontend/` | SSR storefront/CMS output and CSR business workspace |
| Django backend | `pixelcore-backend/` | Tenant-safe APIs for identity, Site, Sell, Schedule, Operate, payments, and Calendar |
| PostgreSQL | Compose `db` | Authoritative business and account data |
| Redis | Compose `redis` | Celery broker/results and future cache coordination |
| Celery | Compose `worker`/`beat` | Confirmation, reminders, digital delivery, and reservation expiry |
| Nginx | `nginx/` | Local frontend/API/admin proxy and static/media delivery |
| Caddy | `Caddyfile` | Production verified-domain edge and on-demand TLS authorization |

## Domain model

- `Business`: identity, brand assets, contact data, PH-first locale/timezone/currency, and tax preferences.
- `BusinessMembership`: a user-to-business role and status. Roles are owner, admin, manager, and staff.
- `BusinessCapability`: source of truth for Site, Sell, Schedule, and Operate. `enabled_modules` is derived for compatibility.
- `BusinessLocation`, `BusinessAsset`, `BusinessInvitation`, and `AuditEvent`: reusable tenant foundation.
- `BusinessEvent`: generic task, meeting, appointment, deadline, or other calendar record.
- `GoogleCalendarConnection`: one encrypted, business-scoped Google Calendar connection.
- `Site`, `SitePage`, `PageRevision`, and `SiteDomain`: versioned publishing and host resolution.
- `Offering` and `OfferingVariant`: one product/service catalog shared by commerce and scheduling.
- Commerce, scheduling, and operations models retain snapshots and ledgers rather than relying on mutable catalog values.

Django is the source of truth. JSON is used only for validated branding, versioned CMS blocks, bounded metadata, and external-provider snapshots.

## API contract

```text
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/refresh/
POST   /api/auth/logout/
GET    /api/auth/me/

GET    /api/businesses/
POST   /api/businesses/
GET    /api/businesses/{public_id}/
PATCH  /api/businesses/{public_id}/
GET    /api/businesses/{public_id}/identity/
PATCH  /api/businesses/{public_id}/identity/
GET    /api/businesses/{public_id}/members/

GET    /api/public/businesses/{slug}/identity/

GET    /api/businesses/{public_id}/events/
POST   /api/businesses/{public_id}/events/
GET    /api/businesses/{public_id}/events/{event_id}/
PATCH  /api/businesses/{public_id}/events/{event_id}/
DELETE /api/businesses/{public_id}/events/{event_id}/

GET    /api/businesses/{public_id}/google-calendar/
DELETE /api/businesses/{public_id}/google-calendar/
POST   /api/businesses/{public_id}/google-calendar/sync/
GET    /api/google-calendar/callback/
```

New API errors use `{ "error": { "code", "message", "details" } }`. DRF field names remain snake_case to keep one convention throughout the Django boundary.

## Authentication and authorization

- Registration creates an account and expiring email-verification challenge; onboarding later creates the business, initial location, capabilities, and owner membership transactionally.
- Login accepts email, username, or phone, returns a short-lived access token, and writes the refresh token to an HttpOnly cookie.
- The Nuxt client retains the access token in memory and restores a session through the refresh endpoint.
- Business querysets are filtered by active membership before object lookup, preventing cross-business enumeration.
- Identity updates and Google Calendar management require owner/admin membership.
- Active managers and staff may work with business events.

## API organization

Existing auth, identity, memberships, events, and Calendar routes remain compatible. New authenticated resources live under `/api/businesses/{public_id}/` and include capabilities, locations, assets, invitations, site/pages/domains, offerings, customers, orders, payments, staff, availability, bookings, inventory, suppliers, purchase orders, quotations, invoices, expenses, and reports. Public routes expose published manifests/catalog/availability, bearer-token carts and checkout, signed quotation acceptance, provider callbacks, and protected digital downloads.

Internal Caddy authorization is network-restricted in deployment and performs an indexed exact-host lookup against active, verified domains.

## Current frontend routes

- `/`: public PixelCore product page.
- `/login`, `/register`, `/verify-email`, and `/onboarding`: account entry and business setup.
- `/workspace`: active-business home.
- `/workspace/site`, `/workspace/sell`, `/workspace/schedule`, `/workspace/operate`: focused module workspaces.
- `/workspace/site/displays`, `/workspace/sell/pos`, and `/workspace/operate/workforce`: restored Display Studio, POS, and workforce operations.
- `/poster-menu`, `/attendance-terminal`, `/pos-terminal`, and `/customer-display`: paired device surfaces.
- `/settings/identity`, `/settings/team`, `/settings/integrations`: business administration.
- `/site/:slug/**`: local published storefront fallback.
- Custom-domain `/`, CMS paths, `/shop`, `/product/:slug`, `/services`, `/booking`, `/cart`, and `/checkout`: public storefront.

## Deliberate release boundaries

Courier APIs, live Stripe, a PixelCore-wide discovery marketplace, marketplace fund splitting, multi-currency transactions, full accounting, tax filing, BIR certification, and fabricated forecast data are not part of this release.

## Verification policy

Use the smallest relevant check. Run at most one focused verification pass for a scoped change. Ask before production builds, full test suites, Docker rebuilds, dependency audits, or broad browser sweeps.
