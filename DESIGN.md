# PixelCore Design Brief

Status: active hybrid-business system with a DineEase-derived admin workspace
Last reviewed: 2026-09-06

## Product direction

PixelCore is the neutral operating layer beneath a business's own identity. The interface should feel dependable, precise, and configurable. PixelCore is visible as the platform provider, while the active business name, logo, colors, locale, and enabled capabilities lead the workspace.

## Design system

- Voice: direct, calm, operational, and free of industry assumptions.
- Typography: Manrope carries the authenticated admin interface, including headings and data. Newsreader is reserved for public/editorial surfaces where it adds meaning.
- Platform palette: deep green ink, practical teal, warm paper, and a small amber signal color.
- Business palette: `--brand-primary`, `--brand-secondary`, and `--brand-accent` come from validated Django identity data.
- Shape: compact `0.625rem` default radius, light borders, and minimal shadows.
- Layout: a persistent business-branded sidebar, compact utility header, dense data surfaces, and full-page task workspaces. Use bordered panels to group real controls or data, not as a generic page-filling card grid.
- Component boundary: `pixelcore-frontend/components/ui` is the canonical Shadcn layer. Application pages and feature components must consume its `Button`, `Input`, `Textarea`, `Checkbox`, `Select`, `Dialog`, `Table`, `Tabs`, `Toast`, and related primitives instead of styling raw interactive HTML independently.
- Native adapters: browser-specific behavior that cannot be represented safely by a Radix primitive—array-valued checkboxes, boolean radios, and select controls that require the original DOM change event—must use the thin adapters in `components/ui/native-*`. Raw interactive tags are allowed only inside `components/ui`.
- Enforcement: run `npm run check:ui` for frontend work. New raw form, action, or table primitives outside `components/ui` fail this check.

## Centralized business identity

- `Settings → Appearance & branding` is the authority for business name, public contact details, logo, favicon, cover image, palette, typography, global component shape, storefront background, global hero, banner, popup, footer, social links, and restrained workspace branding.
- The settings surface uses an Operate-mode layout: one section navigator, one focused editor, and one sticky live preview. It is not a CMS page builder or a wall of equal cards. Narrow screens use a horizontally scrollable section selector and stack the preview after the editor.
- The storefront and workspace consume the same validated identity record. Storefronts use the full expressive range; authenticated workspace colors are constrained to readable shell roles so branding cannot obscure navigation or actions.
- Global heroes support color, gradient, image, video, and approved GLB-backed Three.js media. Enabling a global hero hides published CMS hero blocks at render time without deleting or rewriting those page revisions.
- Identity JSON import and export represent the same versioned schema used by the visual editor. Imported values stay unsaved until the user explicitly saves the identity.
- Business HTML/CSS customization is an explicit, narrow exception to the normal structured-content rule. Django sanitizes the markup and validates the CSS; Nuxt renders it only in a sandboxed frame with no JavaScript, forms, remote fetches, parent selectors, or access to PixelCore controls.

## Authenticated admin workspace

- The useful DineEase admin model is the baseline: a persistent sidebar, visible active business, quick operational summaries, visual catalogs, and dedicated create/manage pages.
- PixelCore generalizes the vocabulary and records; it does not discard the established admin workflows or reduce them to generic module links.
- Navigation has one hierarchy. Do not repeat the same destinations as both shell tabs and page tabs.
- Dashboard and analytics use actual orders, payments, bookings, inventory, and expense records. Empty periods still show truthful axes and zero-state context; never manufacture demo performance.
- The sidebar leads with Live dashboard, Orders, and Product requests. Analytics and business tracking are separate from these live queues; configuration and catalog destinations follow below.
- The live sales desk shows period-based paid order value alongside all-time attention queues. Its series is aggregated on the server in the business timezone, not calculated from a paginated order list. Fully paid order value is labeled distinctly from net revenue or cash receipts.
- Order and product-request desks use server pagination, URL-backed queues and search, readable compact rows that stack on mobile, and explicit review actions. Thirty-second polling pauses while a review is open or the tab is hidden. Overdue rentals carry an explicit text label; contact, agreed extension, and physical return are separate actions.
- Product and service records are visual. Show uploaded media wherever available and an honest type-based placeholder where it is not.
- Creating or substantially editing a product, promotion, supplier, invoice, or other business entity belongs on a dedicated route when the task has multiple sections. Narrow side editors are for small adjustments only.
- The business's secondary color owns the sidebar; its primary color owns active actions and chart series; its accent is used sparingly for highlights. This keeps PixelCore recognizable while making the tenant identity visible.

## POS operational surfaces

- `Sell → POS` is configuration only: administrators create devices, issue one-time codes, link customer displays, select promotional content, and launch each dedicated screen.
- Counter, customer, fulfillment, and delivery work are separate full-screen surfaces. A user should never need to switch roles inside one crowded terminal.
- Pairing codes use eight individually focused character cells with complete keyboard, paste, and error behavior.
- Counter screens prioritize product imagery, rapid search and category selection, the server-priced basket, payment, and receipt completion.
- Counter screens expose distinct New sale and Deliveries modes. Delivery mode may collect an outstanding in-person payment but remains read-only for fulfillment progress.
- Each counter can use standard controls or strict register controls. Strict controls require a short-lived owner, admin, or manager PIN approval before item reductions, voids, or promotions, and every approval is audited.
- Customer screens prioritize business promotions and the live order from one explicitly linked counter.
- Fulfillment screens use a three-stage new, in-progress, and ready queue for packing, production, inventory, or service teams. Delivery screens use incoming, packing, and ready-to-dispatch stages.
- Order tickets show elapsed time, fulfillment, payment state, quantities, modifiers, product imagery, and the minimum customer information required by that role.

## Workforce and attendance surfaces

- Workforce owns employee records and team access. Do not create a second Team & access
  destination in Settings; old links redirect to `Operate → Workforce → Team access`.
- Employee creation opens directly to the manual profile form with a visible submit
  action. A top-level Send email invite action opens a focused Shadcn dialog with its
  own submit button. Both create a pending workforce record and
  send a secure registration link; email-only invitations defer work details to the
  employee's public onboarding form.
- Employee registration names the inviting business, invited role, work email, and
  pending-approval outcome before collecting account credentials.
- The employee portal is a focused workday surface, not a reduced admin dashboard. Lead
  with approval and shift state, then one-use attendance actions, factual 30-day work stats,
  leave and vacation requests, attendance history, and document status.
- Employee details open as a full workspace page with overview, attendance, leave, and
  document tabs. Managers may approve records and requests there, but attendance codes
  remain employee-owned and are never rendered in administrative views.
- Owners and administrators can open Edit employee from the profile header. The dialog
  edits identity, photo, emergency contacts, employment, and schedule fields. Photos
  appear in Workforce and the employee portal, with initials when no photo exists.
- Tab icons and labels share one inline flex row with an explicit gap. Employee detail
  tabs use two columns on narrow screens and one row when space permits.
- Attendance terminals use the same two-column pairing composition, eight segmented code
  cells, state language, and device-session rules as POS screens. After pairing, the
  six-digit action-code task sits within a centered, width-bounded terminal. Business,
  time, and instructions share the supporting pane; the keypad has a compact maximum
  width and code cells can shrink. Panes stack on mobile without horizontal scrolling.
  The live clock includes seconds and updates every second.
- Application UI uses the canonical Shadcn layer with Tailwind utilities and Lucide icons.
  Keep icon-label spacing explicit and source files formatted as readable multiline code;
  do not introduce minified feature files or hand-authored SVG icons.

## Interaction rules

1. Always show which business context is active before presenting business-scoped actions.
2. Identity forms expose real persisted values and a live preview.
3. Loading, empty, error, saved, and unauthorized states must be explicit.
4. Color is never the only carrier of state; pair it with text.
5. Public identity pages expose only presentation-safe fields.
6. Owner/admin-only actions must be enforced by Django, not only hidden in Nuxt.
7. Logo uploads explain accepted formats and size limits before submission.
8. External calendar consent remains separate from account login.
9. Workspace navigation is organized around Home, Site, Sell, Schedule, Operate, and Settings, with visible section navigation for restored workflows.
10. Lists preserve filters and pagination in the URL; destructive and money-moving actions require explicit confirmation.
11. The CMS editor uses outline, canvas, and selected-block settings on desktop and sequential panels on mobile.
12. Draft, published, conflict, saving, and saved states are labeled in text rather than implied by color.

## Business card surfaces

- `Workspace → Business card` is an editor-and-live-preview workspace for the signed-in
  member. It starts from existing account, membership, and business identity data rather
  than creating a second profile system.
- Signature, Editorial, Studio, and Luxury are bounded compositions that inherit the business
  logo and validated theme colors. Each owns a distinct generated geometric pattern and
  a distinct treatment for optional imagery. Landscape and portrait use the same data
  contract.
- Luxury is a dedicated black-and-metallic print composition, not an alias for Signature.
  It uses a thin generated frame, symmetrical CSS ornaments, a centered brand-only front,
  and a contact-led reverse. Every composition can use either its authored palette or a
  shared custom palette with independent background, text, accent, border, and ornament
  colors; choosing custom colors never changes the selected composition.
- Generated Pattern is the default and permanent fallback. It uses deliberate geometry,
  restrained gradients, and business color shades without depending on decorative image
  files. Image Background accepts validated business assets with only side, fit, position,
  overlay, and overlay-strength controls; it is not an image editor.
- Image-backed fronts remain brand-only. Contact details stay on a clean controlled panel
  on the back, and generated accents reduce automatically when imagery is present.
- Front and contact sides are distinct; the card itself is the keyboard-accessible flip
  control, with no detached rotation button. The shared renderer owns workspace preview,
  public display, and print output so those surfaces do not drift.
- Contact visibility is opt-in per field, and an explicit Published state gates the public
  URL. Public API output removes internal visibility flags and timestamps.
- Every style can retain its authored typography or use separate heading, readable body,
  and accent faces. Curated expressive options include Great Vibes, Allura, Parisienne,
  Alex Brush, Playball, and Lobster alongside the established serif and sans families. A tenant-scoped
  custom font may be uploaded as a validated self-contained WOFF2 file only; arbitrary CSS,
  remote font URLs, and other font containers are rejected. The QR is created
  locally and prefers the website saved under Appearance & branding; on a published card,
  its public card URL is the safe fallback. Members may hide it from the contact side.
- Card typography remains deliberately larger than conventional print-card microtype so
  it stays legible in the digital preview. Members may add up to four validated HTTPS
  social profiles; compact handles appear on the contact side and icon links remain
  available beside the public card without turning the card face into nested controls.
- Print output uses physical 3.5 × 2 inch or 2 × 3.5 inch faces with exact business colors
  and one face per sheet for dependable duplex or manual two-sided printing.

## Scheduling surfaces

- `Schedule` is a PixelCore Venue Schedule command center rather than a configuration
  table or a restaurant-only floor plan. The public-form state is visible and editable
  in the opening panel, followed by the live month, selected-day work, and Venue Studio.
  Availability and capacity setup remain present but visually secondary to live work.
- Venue Studio supports restaurant dining, event or wedding, room or studio, and general
  layouts. Reservable tables, rooms, and booths share the plan with non-bookable venue
  features such as stages, dance floors, bars, buffets, entrances, service areas, and
  decor. Every element has a shape, dimensions, rotation, position, visibility, and
  optional guest capacity. State uses both color and text and preserves keyboard
  selection and drag persistence.
- Venue layouts are reusable templates, not date-owned snapshots. Multiple layouts may
  host work on the same day, while the selected date only previews bookings and remaining
  capacity. Tasks, functions, and projected booking events can reference one layout.
- The Calendar workspace uses Shadcn tabs for Month and Day views, places Calendar
  connection state before schedule content, and shows a Mapbox location preview for the
  saved business location attached to the selected venue layout.
- The public booking form uses a calm three-step sequence: visit details, live resource
  selection, then contact information. Restaurant presets use reservation and table
  vocabulary; every other preset uses generic booking and resource vocabulary. A stable
  confirmation code is visible after submission, and pending requests are never described
  as confirmed.
- Guest events have a distinct public invitation surface. The first template is Wedding
  Editorial: a near-black, photographic sequence with grayscale media, oversized display
  dates, thin utility rules, compact fixed navigation, and deliberate scroll motion. It
  avoids ornamental wedding graphics, gradients, elevated cards, and invented claims.
- Event identity is configured inside the dedicated event workspace, not global business
  appearance. Organizers can publish the site, choose allowlisted display and body fonts,
  set readable theme colors, edit participants, schedules, story passages, an optional
  quote, and ordered event media. Public output contains approved wishes only; guest names,
  table assignments, and RSVP updates remain protected by invitation tokens.
- The same wedding page serves public and personalized contexts. A public URL presents the
  event but never an RSVP form; a private invitation adds the named guest, their current
  response, and the existing token-authorized RSVP action without exposing other guests.

## CMS and storefront rules

- Public pages inherit only validated business identity tokens and render CMS content as structured data. The identity system's optional custom section, popup, and footer markup are sanitized and isolated in sandboxed frames rather than injected into the application DOM.
- Storefront composition may be expressive, but checkout, booking, and account-adjacent surfaces remain calm and operational.
- Commerce uses an editorial retail rhythm: large real product media, decisive product naming, visible price and option state, compact filters, and restrained motion. Tenant identity colors lead accents while the warm paper foundation preserves readability. Do not imitate another retailer's brand, layout, claims, or assets.
- Storefront layout is a two-level choice. `Brand storefront` contains the existing Default and Luxury modes. `Marketplace storefront` is a separate search-first family with a utility header, persistent catalog search, category navigation, department imagery, compact shelves, comparison-friendly product grids, and a clear purchase panel. Marketplace here describes information density and navigation—not multiple sellers or pooled commerce.
- Marketplace implementation lives in `components/marketplace` and consumes the same public catalog, collection, cart, checkout, wishlist, identity, and CMS contracts as Brand storefront. Switching layout must never fork business data or silently replace published CMS content.
- Storefront headers span the viewport. Desktop catalog discovery opens as a square-edged, full-width plane; only categories explicitly curated by the business appear, using their chosen image and grid or carousel presentation.
- Storefront search is a full-screen discovery surface with useful pictured suggestions before typing. Catalog filters are on-demand in a right-side drawer launched by a persistent floating control, leaving the product field visually uninterrupted.
- A business may designate exactly one published product as the screen-scale shop highlight. Product cards may use an explicitly selected alternate hover image and optional previous/next gallery controls; these behaviors are configured on the full product editor.
- Site-wide announcements span the viewport above the storefront header and are always dismissible. A changed message is treated as a new announcement so an earlier dismissal cannot hide it. Banner and popup settings must include an honest preview before save.
- Storefront heroes and commerce hero blocks use edge-to-edge media and may occupy the available first viewport; server-rendered copy remains legible before media or Three.js is ready.
- 3D is progressive enhancement: load Three.js only for a 3D block, retain poster fallbacks, cap complexity, and respect reduced motion.
- Product, service, Organization, canonical, Open Graph, robots, and sitemap output must derive from published data.
- Do not compress the desktop CMS into three unusable mobile columns; preserve the editing sequence as stacked panels.

## Accessibility

- Follow WCAG 2.1 AA contrast and keyboard expectations.
- Use visible labels for every field.
- Preserve native button, input, link, fieldset, and heading semantics.
- Use `aria-live` or `role=alert` for asynchronous save/authentication errors.
- Keep navigation usable at 320 px without hiding required actions behind pointer-only interaction.

## Definition of done for UI work

- The route and authorization boundary are explicit.
- Narrow and wide layouts are intentional.
- Keyboard focus is visible and follows reading order.
- Loading, empty, failure, and success states are present.
- Business-provided text is rendered as text. The only HTML exception is the sanitized, sandboxed identity customization described above.
- API mutations reliably refresh the active identity.
- Restaurant terminology is allowed inside the restaurant preset and restaurant-specific templates, but never as the global platform vocabulary.
