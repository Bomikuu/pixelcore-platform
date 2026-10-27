# Delivery tracking

The owner manages delivery orders, assigns employee or independent riders, and views GPS positions. Riders use a delivery-only portal; customers track only their own order. The user directed implementation after confirming this design, including live GPS refreshed every 30 seconds.

## Domain and access

A Delivery is one tracked trip per delivery Order. Existing Order and Fulfillment records retain payment and inventory authority. Stages are preparing, ready, out_for_delivery, delivered, and cancelled. Assignment is independent of preparation. Only ready deliveries with an active rider can depart. Delivery completion uses the existing stock commitment service transactionally.

RiderAccess grants one business-specific delivery role. Employee grants require an active business membership. Independent grants require explicit acceptance by the invited email's verified account and never create a workspace membership. Owners/admins/managers manage grants and assignments; revocation removes assignments and GPS. No UUID alone authorizes customer tracking: use exact Customer.user ownership or the original cart token.

## GPS and refresh

The browser requests permission only after Start sharing. It samples and uploads current GPS immediately, then at most once every 30 seconds. Server validation rejects invalid, stale, future, or out-of-order coordinates and suppresses uploads within 30 seconds. Assignment revision prevents an old rider upload reaching a reassigned trip. Store only the latest point, never a breadcrumb history. Stop, revocation, reassignment, cancellation, and completion clear GPS. A point older than 90 seconds is labeled stale. Customers see rider location only while out for delivery.

Each active page fetches one aggregate snapshot every 30 seconds using a non-overlapping timer. Pause hidden/offline and clean up on navigation. Keep previous data on transient failure, show error and last received time, allow manual retry, and stop customer polling for terminal deliveries. Explicit actions may refresh immediately. Browser GPS does not guarantee locked-screen background updates.

## Interface and map

Owner: Live operations → Deliveries, URL-backed status filter, delivery list, selected detail/map/timeline, rider management and assignment. Rider: /rider/deliveries, invitations, assigned jobs, departure/completion actions, location-sharing controls. Customer: /site/:slug/track/:orderId, linked from confirmation/account orders.

Reuse Mapbox's configured public token. A shared lazy-loaded interactive map initializes once and updates markers on snapshots; no routing, geocoding, or static-image refresh per poll. Save destination coordinates through a deliberate address picker in owner delivery details. Existing text addresses remain usable without a pin. No fabricated ETA or route line. Missing map configuration/WebGL/GPS leaves all status and address information usable.

Use canonical Shadcn controls, semantic theme tokens, Lucide icons, visible focus, reduced motion, narrow layouts, and explicit loading/empty/error states. Map is progressive enhancement with a textual equivalent.

## Implementation refinements

Guest checkout retains the original cart token by order under the existing device local-storage trust boundary (20 orders, 30 days), keeping later shopping carts from replacing earlier tracking access. Tokens never enter URLs or SSR HTML. Changing selection/revision/stage invalidates pending initial GPS permission requests as well as active sharing. Client-only order confirmation retains its existing serial 2.5-second pending-payment refresh independently of delivery tracking.

## Verification

Targeted Django tests cover tenant/role isolation, customer ownership/cart token, independent acceptance, suspended employees, transitions and stock rollback, revocation/reassignment, upload validation/rate/order, and legacy order synchronization. Node tests cover polling lifecycle, no overlap, stale point handling, and rider account routing. Run check:ui. No builds. Use mocked browser fixtures for visual inspection if exercised; no actual GPS or chargeable Mapbox requests.
