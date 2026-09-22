---
version: 1
slug: "pixelcore-frontend-components-scheduling-eventrsvpworkspace-vue"
primary_target: "pixelcore-frontend/components/scheduling/EventRsvpWorkspace.vue"
related_targets: ["pixelcore-frontend/pages/workspace/schedule/events/[eventId].vue","pixelcore-frontend/components/scheduling/EventOverviewTab.vue","pixelcore-frontend/components/scheduling/EventProductsTab.vue","pixelcore-frontend/components/scheduling/EventVenueLayoutTab.vue","pixelcore-frontend/components/scheduling/ResourceFloorPlan.vue"]
---

SCOPE: Authenticated event operations workspace. Operate mode for owners, managers, and event staff.

THESIS: One event record should make accountability, guests, catalog commitments, the physical venue, and the public invitation immediately legible without turning the page into one overwhelming form.

OWN-WORLD: PixelCore’s warm neutral workspace, precise Shadcn controls, restrained emerald state color, readable sans-serif hierarchy, and venue-plan geometry inherited from Scheduling.

STORY: The organizer identifies the event and accountable handler, manages guests and seating, shapes the private RSVP experience, attaches the products and services needed for delivery, edits the shared venue plan, then publishes the event website.

FIRST VIEWPORT: The event header is the single identity and operational summary. The URL-backed tab bar starts with Event details, followed by Guests & seating, RSVP customization, Staff, Products & services, Venue layout, and Event website without repeating header information.

GUESTS AND SEATING: Event-wide seating cards stay accurate while the guest table is filtered and paginated server-side. Table cards show assigned seats and a concise guest preview; rows use initials, editable RSVP and table controls, clear invitation actions, and a 20-record page boundary that remains practical for large events.

RSVP CUSTOMIZATION: One focused Shadcn form controls RSVP language, response choices, optional fields, party limits, a server-enforced deadline, and accepted or declined confirmation copy. A prominent preview action opens the published invitation while drafts explain why preview is unavailable. Dress-code guidance supports an event-owned image and a restrained palette. Practical event notes are explicit ordered records with accessible move and remove controls. Saving this tab merges only its nested `sections_config` values so website editing cannot erase them.

ACCOUNTABILITY: Staff distinguishes one accountable primary handler from the wider multi-person event team. The handler is always included in the team, and staff portraits and job titles make assignments scannable.

CATALOG: Products and services come from the business catalog, retain their real image, type, publication state, summary, and price, and use a searchable paginated selector with an explicit save state.

VENUE: Venue layout edits the same ResourceLayout and Resource records as Venue Studio. Organizers can select, create, rename, and compose a plan from either entry point; no event-only duplicate is created. The in-page canvas and fullscreen editor both retain layout selection and element creation controls. Dragging saves positions, and element editing covers type, capacity, shape, dimensions, and rotation.

STATES: Empty staff, empty catalog, missing layout, loading RSVP settings, load failure, save failure, saved confirmation, and disabled actions all explain the next useful step. Horizontal tab overflow remains available at narrow widths.

FORM: Extension of the established scheduling workspace; no replacement visual world or concept seed is needed.
