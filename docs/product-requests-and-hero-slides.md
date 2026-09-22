# Product requests and custom hero slides

## Enable and use

1. Open **Settings → Reservations & rentals** (`/settings/commerce`). Both modes default off. Stock holds expire after 24 hours by default; choose 1–168 hours.
2. Edit a physical product in **Products & services → Merchandising**. Enable reservation and/or rental, enter customer-facing terms, and save. Inventory tracking, an active variant, and location stock are required for stock allocation.
3. On the public product page, customers choose a variant and use **Reserve for pickup** or **Request a rental**. Each opens its own contact/location/terms dialog. Rentals also collect dates.
4. Review requests at **Commerce → Product requests** (`/workspace/sell/requests`). Owner, admin, and manager roles can review and change state. Staff-only accounts cannot approve requests or access customer request details.

## Stock and payment semantics

- Reservations immediately increase the existing inventory balance's reserved quantity. Cancellation and expiry release it once. The existing scheduled stock-expiry task also processes product holds.
- Rental submissions are pending and do not promise or reserve stock. Approval checks current stock and sets units aside **immediately**, through collection until staff records return. This is conservative allocation, not interval-based back-to-back rental scheduling. Overdue collected rentals never auto-release.
- Agree rental price, deposit, and collection arrangements with the customer separately. The rental request does not collect payment or create a financial transaction.
- A held reservation can convert once into an unpaid, manual-payment pickup order using current catalog prices. Its units transfer atomically to the existing order reservation. Complete payment through the existing order/counter flow; its normal 30-minute stock deadline applies.
- Conversion also applies the regular cart validator. Products with mandatory modifiers need those choices in the normal checkout flow; conversion will not silently bypass them. Cancel/release the hold and use the counter for that case.
- Disabling a business or product mode stops new submissions, not management of existing requests.
- Guest confirmations show the request reference and deadline/dates. They do not imply an email was sent. Staff uses the submitted contact details for follow-up.
- Settings are operational records, separate from visual branding. Per-product flags and terms extend `product_profile`; existing cart and service-booking endpoints are unchanged.

## Additive API

- `GET/PUT /api/businesses/{id}/product-request-settings/`: `reservation_enabled`, `rental_enabled`, `hold_hours`.
- `POST /api/public/{slug}/product-requests/`: UUID `idempotency_key`, offering/variant/location public IDs, `kind` (`reservation` or `rental`), integer quantity 1–20, first/last name, email, phone, optional notes, `accepts_terms`; rentals require `starts_on` and `ends_on` in the business timezone.
- Public product responses add `request_options`, with effective mode flags, hold duration, terms and allowlisted active collection locations. No private stock balances are exposed.
- `GET /api/businesses/{id}/product-requests/`: paginated, filter by `kind` and `status`.
- `POST /api/businesses/{id}/product-requests/{id}/transition/`: `action` and optional `note`. Actions: approve, reject, cancel, collect, return, convert. Reject/cancel require a reason. Invalid or stale transitions return a conflict.
- A repeated public submission with the same key and normalized payload returns the existing result; changing the payload with that key returns 409. Submission rate is limited to 10/hour per business and IP, with at most five active requests per email/business. An authenticated-contact verification flow is not introduced here; consider stricter anti-abuse controls before exposing scarce high-value stock publicly.

## Custom hero slides

- **Collections → Edit → Hero & carousel** or **Site builder → Page → Commerce hero block**: add up to five custom slides. Custom slides take precedence over automatic product photography; remove them to restore product slides.
- Each slide supports a heading, description, internal storefront CTA, background color, and an image, MP4/WebM video, approved GLB model, or built-in Three.js particles. Video and model slides require a poster image. Three.js motion is bounded to static, subtle, or pointer response. No arbitrary animation code is accepted.
- Media must belong to the business and pass existing asset validation. Page publication revalidates custom media. Collection preview shows the first custom image or poster and its copy.
- Copy and links remain server-rendered. Video/Three.js pause offscreen, in hidden tabs, and using the pause control. Reduced motion uses static fallbacks. Only Three.js slides dynamically load Three.js.

## Focused verification

Run against the existing Docker stack, without rebuilding:

```sh
docker compose exec -T backend python manage.py migrate --noinput
docker compose exec -T backend python manage.py test commerce.test_product_requests content.test_hero --keepdb
docker compose exec -T frontend npm run check:ui
```

Restart the existing worker after deploying the task change (`docker compose restart worker`); no dependency rebuild is needed. Keep the existing beat service running.

Manual checks: enable each business mode, save an eligible product's terms, submit both dialogs, expire/cancel a hold, approve/collect/return a rental, and convert a hold to an unpaid order. For heroes, save image/video/3D slides and inspect a collection and CMS home at desktop/mobile widths with reduced motion and keyboard navigation.

### This implementation pass

- Applied catalog 0008 and commerce 0009 to the running development database.
- The 11 product-request tests passed. A subsequent conversion guard now also calls the existing cart validator; that final guard has not been rerun.
- The four hero tests stopped during setup because their synthetic assets lacked `size_bytes`. The fixtures are corrected; rerunning them is left to the user as requested:

```sh
docker compose exec -T backend python manage.py test content.test_hero --keepdb
```

- `npm run check:ui` passed. The scoped Impeccable detector returned no findings. No production build, Docker rebuild, or browser sweep was run for this change.
