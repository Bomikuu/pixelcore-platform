# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

PixelCore serves Philippine small and medium business owners and their teams who sell physical or digital products, deliver bookable services, or combine both. Customers use the public storefront to browse, buy, book, and pay without requiring a PixelCore account.

## Product Purpose

PixelCore gives a business one branded operating core for publishing its site, selling offerings, scheduling work, and understanding day-to-day operations. Success means the same catalog, customer, payment, booking, inventory, and document records drive both the public experience and the private workspace without industry-specific assumptions.

## Positioning

PixelCore treats products and services as one configurable offering system. A business can publish a branded site, sell an item, take a booking, collect a Philippine payment, and carry the result into inventory and operational reporting without stitching together separate tools.

## Operating Context

- Owners and administrators configure identity, capabilities, sites, payments, domains, and team access.
- Managers and staff operate catalogs, customers, orders, bookings, inventory, suppliers, quotations, invoices, expenses, and reports according to their role.
- Public customers browse server-rendered storefronts on a PixelCore subdomain or verified custom domain, and may use a business-specific portal for their saved profile, addresses, orders, bookings, and receipts.
- Philippine businesses default to PHP, Asia/Manila, and en-PH while the platform remains usable in other single-currency markets.
- Merchant-owned PayMongo accounts receive online payments; PixelCore never pools merchant funds.

## Capabilities and Constraints

- Core capabilities are centralized business identity, branding, membership, tenant isolation, locations, assets, audit history, notifications, and integrations. One versioned identity record drives the workspace, storefront, displays, receipts, and other customer-facing surfaces, and can be edited visually or moved as validated JSON.
- Release capabilities are Site/CMS, Sell, Schedule, and Operate.
- The CMS uses versioned, validated JSON blocks and supports SEO, drafts, previews, publishing, and audited Three.js blocks. CMS blocks never accept arbitrary JavaScript, shaders, CSS, URLs, or raw HTML. The separate business identity system permits a deliberately limited HTML/CSS extension rendered in a sandbox; JavaScript, forms, remote resources, and workspace-level selector access remain forbidden.
- Sell supports physical products, digital products, services, guest checkout, PayMongo, COD, manual payments, delivery, pickup, digital fulfillment, and service-linked checkout.
- Commerce storefronts are product-led and business-branded. Each business can choose a Brand storefront or Marketplace storefront without changing its catalog, cart, checkout, CMS, or inventory records. Brand storefront retains Default and Luxury modes for image-led launches and editorial collections. Marketplace storefront is a search-first, category-dense presentation for larger single-business catalogs; it does not create a multi-vendor marketplace. Both support collections, generic option dimensions, variant-level merchandising, ordered photography, one validated GLB product model, URL-backed discovery, tenant-scoped wishlists, editable carts, and token-protected order confirmation without exposing private costs or inventory balances.
- Schedule supports appointments and capacity-limited groups, staff and resource availability, an explicit public-booking switch, and reusable multi-purpose venue layouts for restaurant dining, events, weddings, rooms, and studios. Multiple venues may operate on one date, and tasks, functions, or projected booking events can reference a floor plan. Plans combine reservable seating or rooms with non-bookable stages, dance floors, bars, buffets, entrances, booths, custom elements, service zones, decor, and Mapbox-backed saved locations while retaining reminders, payments, stable confirmation codes, live public resource selection, and the existing business-level Google Calendar bridge.
- Guest events can publish a reusable, event-scoped invitation site without changing the business storefront. The first template is a wedding-focused editorial experience driven by structured participants, schedule entries, story passages, optional quotation, ordered photographs, moderated wishes, and the existing private guest RSVP links.
- Operate supports inventory, suppliers, purchasing, quotations, operational invoices, expenses, and actual-data reporting.
- Each business uses one operating currency. Currency becomes locked after the first financial transaction.
- Operational invoices may carry configurable Philippine tax fields but are not represented as BIR-authorized invoices or receipts.
- Customer portals are scoped to a single business and do not form a PixelCore-wide discovery marketplace.
- Automated couriers, live Stripe, multi-currency transactions, marketplace fund splitting, full accounting, tax filing, cross-business customer accounts, and BIR certification are outside this release.
- Restaurants are a supported business preset. Restaurant vocabulary, food metadata,
  table resources, poster-menu templates, and counter workflows appear only when the
  preset or feature is selected; the underlying records remain industry-neutral.
- Workforce is the single home for employee profiles, workspace access, invitations,
  approval, documents, attendance, leave, and dedicated attendance terminals. Managers
  may create a complete pending employee record or send an email-only invitation. The
  employee uses the secure public form to create their account and complete or review
  their workforce profile before manager approval.
- Signed-in employees use a dedicated employee portal rather than the administrative
  workspace. It exposes only their own schedule, attendance, leave history, documents,
  and factual work summaries. Employees generate separate short-lived, one-use clock-in
  and clock-out codes from this portal. A paired terminal derives both the employee and
  action from the code, so it never asks for an employee identifier or reusable PIN.
- Attendance and POS screens use role-limited device sessions. A setup code can pair only
  the intended device type, and reopening a terminal must validate its saved session
  before showing operational controls.
- Every active business member can maintain one business-scoped digital card. It begins
  with their account, membership, and business identity, but card edits stay independent.
  Publishing is explicit, public output is field-allowlisted, and a website QR appears
  automatically when business identity contains a website URL. Generated brand patterns
  are the default background; members may optionally select or upload one validated
  business image with bounded placement and readability controls.

## Brand Commitments

- The product name is PixelCore.
- PixelCore is the neutral operating layer beneath each business's identity; the active business name, logo, colors, locale, and enabled capabilities lead the workspace and storefront.
- The voice is direct, calm, operational, and free of industry assumptions.
- Existing PixelCore design direction remains authoritative and is expanded rather than replaced.

## Evidence on Hand

- The repository contains a working Django/Nuxt foundation for authentication, business identity, membership roles, public identity, generic business events, and one-way Google Calendar synchronization.
- There are no approved testimonials, customer logos, commercial metrics, pricing claims, or production usage claims. Future surfaces must not invent them.

## Product Principles

1. One business truth powers every channel.
2. Products and services work together without forcing an industry template.
3. Businesses control their identity and merchant relationships; PixelCore does not hold their funds.
4. Flexible configuration stays bounded, validated, portable, and safe.
5. Every operational record is tenant-scoped, attributable, and useful downstream.
6. General-purpose software does not mean fewer capabilities: industry presets adapt
   vocabulary and defaults without fencing businesses into a reduced product.

## Accessibility & Inclusion

PixelCore targets WCAG 2.1 AA. Public and private interfaces must be keyboard accessible, responsive from 320 pixels upward, explicit about loading and failure states, and usable with reduced motion. Three-dimensional content is progressive enhancement and always has a non-motion fallback.
