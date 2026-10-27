# Delivery tracking

## Surfaces

- Workspace → Live operations → Deliveries (`/workspace/deliveries`): owner/admin/manager delivery desk, status filters and pagination, rider access, assignment, destination pin, timeline, and completion/cancellation.
- `/rider/deliveries`: employee and independent riders see only assigned active deliveries. Employee portal links here. Independent riders have no business workspace membership.
- `/site/:slug/track/:orderId`: customer tracking, linked from checkout confirmation and account order lists. Requires the exact linked customer account or the original `X-Cart-Token`; order UUIDs never grant access.

## Setup and rider access

Run `python manage.py migrate` in the backend when deploying. The deliveries migrations create tracking records for existing delivery orders. Signals track newly created orders and changes made through the existing order/POS/dispatch workflows.

The existing `NUXT_PUBLIC_MAPBOX_ACCESS_TOKEN` config enables the interactive map. Install frontend dependencies from the updated lockfile. Mapbox GL JS is lazy-loaded only for a delivery map with a point; map markers move on updates without replacing the map. A missing/failed map leaves the textual delivery status, address, rider and timeline usable. No Directions/ETA or per-tick geocoding calls are made. Owners can find and save a destination pin once using the existing Mapbox address picker; it does not change the written shipping address.

Managers add riders by account email. Employees require an active membership in the same business. Independent invitations can be created before registration: share the rider portal link with the rider, who registers/signs in with the invited email, verifies it, and explicitly accepts. No invitation email is sent automatically. Revoking access clears assignments and GPS; active jobs return to ready. Suspended employees immediately lose rider access and their location is withheld.

Guest checkout retains the original cart token per order on the checkout device, using the existing local-storage trust boundary. Retention is capped at 20 orders and 30 days; expired entries are pruned. Tokens never enter links, analytics, logs, or SSR HTML. Starting another cart cannot overwrite earlier order access. Blocked storage never prevents checkout; account ownership remains available.

## Behavior contract and canonical owners

Visual language and semantic tokens remain owned by root `DESIGN.md`, businessTheme.js and the shared Shadcn layer. Controls, Input, Label, Dialog, authored Select/Listbox, Badge, Alert, and ButtonLink reuse `components/ui`. `DeliveryMap`, `DeliveryDetail`, `DeliveryRefresh`, `useDeliveryResource`, and `useRiderLocation` own the repeated delivery behaviors. Mapbox owns its generated navigation controls and attribution, with an equivalent text view outside the canvas.

The owner list uses URL-backed stage/page/selection state and 30 rows per snapshot. A dialog captures its exact order, tenant and revision; a refresh cannot redirect a confirmation to another order. Failures preserve context and entered fields; revision conflicts require reviewing current data. Confirming delivery or cancellation is explicit. Payment collection/refunds stay in the existing payment workflows.

Automatic snapshots and rider GPS uploads run at most once every 30 seconds, with one in-flight request per resource. Initial/manual refresh and explicit status actions can fetch immediately. Polling pauses hidden/offline, cancels superseded business/route requests and cleans up when leaving. Customer polling ends for delivered/cancelled orders. Temporary refresh failures preserve previous data and show an error. GPS age is evaluated locally; after 90 seconds it is labeled a last-known/stale position.

GPS starts only on the rider's explicit action after permission and a fresh fix. It needs HTTPS (or localhost) and an active, open browser page; locked-screen/background reliability requires native mobile support. No localStorage GPS or breadcrumb history is recorded. The server validates coordinate bounds/finite values/accuracy, timestamps (max 120 seconds old, max 15 seconds ahead), monotonic fixes, ownership, active assignment revision and a 30-second receipt interval. Reassignment, revocation, stop, completion and cancellation clear the latest point. Customer output never includes rider email or unrelated orders.

## API

All responses are private/no-store. Owner routes require an active owner/admin/manager membership in the supplied business.

- `GET businesses/:businessId/deliveries/?stage=active&page=1`: paginated results, counts, rider choices, server receipt time.
- `PATCH businesses/:businessId/deliveries/:id/`: `revision`, `action` (`assign`, `stage`, `destination`) and corresponding data.
- `POST businesses/:businessId/delivery-riders/`: email, display_name, kind (`employee` or `independent`).
- `DELETE businesses/:businessId/delivery-riders/:id/`: revoke.
- `GET rider/deliveries/`: active assignments and invitations.
- `POST rider/access/:id/accept/`: verified, matching independent account only.
- `PATCH rider/deliveries/:id/`: `revision`, `action=stage` (`out_for_delivery` or `delivered`) or `action=sharing`, `sharing` boolean.
- `POST rider/deliveries/:id/location/`: revision, latitude, longitude, accuracy in metres, captured_at ISO timestamp. A point within the receipt interval returns `accepted:false`, `refresh_after:30` without replacing the point.
- `GET public/:slug/orders/:orderId/tracking/`: customer-scoped delivery snapshot.

The lifecycle is preparing → ready → out_for_delivery → delivered, with cancellation by management. Only an active assigned rider can depart. Completion commits stock inside the same database transaction and updates the existing Order/Fulfillment. Financial totals and payments are not changed by tracking.

The order confirmation uses client-only token-authorized loading. Its existing pending-payment refresh stays at 2.5 seconds, starts when client data arrives, prevents overlapping requests, and stops when paid or on navigation. This payment confirmation behavior is separate from the 30-second delivery tracking cadence.

## Verification

Targeted tests live in `deliveries/test_api.py`, `utils/deliveryTracking.test.mjs`, `utils/orderAccess.test.mjs`, `composables/useRiderLocation.test.mjs`, and `composables/useOrderPaymentRefresh.test.mjs`. Run them plus `npm run check:ui`; do not use production builds as verification. Browser fixtures under ignored `output/playwright/delivery-tracking` use synthetic records and mocked GPS; no real rider/customer data or map API requests are needed for these checks.
