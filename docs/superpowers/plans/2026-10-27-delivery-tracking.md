# Delivery Tracking Implementation Plan

> Execution: native in this session, as requested by the user. Preserve all unrelated working changes; do not build.

**Goal:** Owner, rider, and customer delivery tracking with GPS updates every 30 seconds.
**Architecture:** Dedicated deliveries app links tracked trips to commerce orders and scoped rider grants. Shared frontend polling/map/detail components serve three authorized views.
**Tech stack:** Django/DRF, Nuxt/Vue, Shadcn, Mapbox GL JS.
**Spec:** docs/superpowers/specs/2026-10-27-delivery-tracking-design.md

## Global constraints

30-second automatic snapshots and location uploads; no overlapping requests. No independent-rider workspace membership. Customer UUID alone never grants access. Existing stock/payment services remain authoritative. Canonical UI primitives only. No builds.

## Review focus

Revoked/suspended rider; reassignment racing location upload; terminal state changed through an existing terminal; GPS unavailable/invalid/stale; hidden/offline page and business switch.

## Tasks

- [x] Add deliveries models/migration/signals and services: Delivery, RiderAccess, DeliveryEvent; transactional lock order → delivery, coordinate validation, lifecycle synchronization.
- [x] Add owner, rider and customer endpoints plus tests in deliveries/test_api.py. Test cross-tenant/ownership denial, independent invitation acceptance, revoked access, transition/stock rollback, latest-point privacy and 30-second gating. Extend auth/me with delivery access, preserving current membership routing.
- [x] Add shared delivery polling utility/composable and tests in utils/deliveryTracking.test.mjs; test timers, no overlap, visibility/offline and cleanup. Add lazy shared interactive Mapbox component and detail/timeline components.
- [x] Add owner desk/rider management, rider portal and customer tracking route. Add discoverable links from workspace navigation, employee portal, storefront confirmation/account. Add destination coordinate editing through existing address picker. Preserve public/workspace theme boundaries.
- [x] Run targeted Django and Node tests, migration drift check for deliveries, npm run check:ui; inspect mocked desktop/mobile if applicable. Update docs with setup, endpoints and browser GPS limitations. Record results; no builds.

## Results

39 targeted Django tests, 18 Node tests, migration drift check and check:ui passed. Browser synthetic preview confirmed one additional GPS upload during a 31-second window and no narrow-layout overflow. A fresh review scored all three material fixes resolved and returned ship. Production Mapbox tiles and physical-device GPS were not exercised; the map token is unset locally. No builds were run.
