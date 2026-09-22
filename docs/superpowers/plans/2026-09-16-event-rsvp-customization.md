# Event RSVP Customization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated RSVP customization tab for every event template and give only the Garden Vow wedding template an elegant botanical invitation presentation, while preserving the event's current colors, typography, media, guest links, and RSVP data contract.

**Architecture:** Keep all new configuration inside `VenueEvent.sections_config` so this feature requires no migration. Validate and normalize the nested configuration at the website API boundary, enforce the configured RSVP deadline in the public response endpoint, expose the settings through one Shadcn-based workspace editor, and render them through the existing public invitation component. Use a Garden Vow-specific presentation branch for botanical composition; every other template consumes the same RSVP fields without changing its visual identity.

**Tech Stack:** Django, Django REST Framework, Nuxt 3, Vue 3 Composition API, Tailwind CSS, Shadcn Vue primitives, Lucide icons.

**Spec:** `docs/superpowers/specs/2026-09-16-event-rsvp-customization-design.md`

## Global Constraints

- Work only in `/home/bomiku1/projects/pixelcore-platform`; do not edit the protected DineEase checkout.
- Preserve all unrelated and untracked work. Stage only files named in the active task.
- Do not add a Django model field or migration; use the existing `sections_config` JSON field.
- Keep the current Garden Vow theme colors, heading font, body font, images, and user overrides authoritative.
- Use the existing Shadcn primitives and Lucide icons; do not add hand-authored SVG icons.
- Keep all files readable and formatted; do not minify Vue, JavaScript, or Python.
- Run one focused verification pass after implementation, in accordance with the project verification budget.

---

## Task 1: Define and validate the RSVP customization contract

**Files:**

- Create: `pixelcore-frontend/utils/eventRsvpConfig.js`
- Modify: `pixelcore-backend/scheduling/serializers.py:927-1115`
- Modify: `pixelcore-backend/scheduling/test_event_website.py`

- [ ] Add serializer tests that PATCH the website endpoint with complete `rsvp`, `dress_code`, and `event_notes` objects and assert that the exact normalized objects are returned.
- [ ] Add serializer tests for invalid nested data: malformed deadline, `max_party_size` outside `1..50`, non-hex dress-code colors, more than eight colors, more than eight notes, blank note titles, and a dress-code image belonging to another event.
- [ ] Repair only the malformed extra `{` already present in `test_event_images_have_single_slots_and_story_assignments` so the existing untracked test module remains executable; do not rewrite or discard the user's other tests.
- [ ] Extend `VenueEventWebsiteSerializer` with nested validators that return field-specific `sections_config` errors. Keep existing top-level section booleans and `order` validation intact.
- [ ] Resolve `dress_code.media_public_id` against an `EventMedia` record owned by `self.instance`; reject cross-event identifiers and serialize the public image URL as `dress_code.media_url` without storing a host-specific URL in JSON.
- [ ] Add the frontend normalization utility with immutable defaults and defensive parsing:

```js
export const defaultRsvpConfig = () => ({
  heading: 'RSVP',
  subtitle: 'Will you celebrate with us?',
  deadline: null,
  submit_label: 'Send RSVP',
  accept_label: 'Joyfully accept',
  decline_label: 'Regretfully decline',
  allow_maybe: false,
  show_party_size: true,
  show_dietary_notes: true,
  show_guest_message: true,
  max_party_size: 10,
  attending_title: 'Thank you',
  attending_message: 'We are so happy you will celebrate with us.',
  declining_title: 'Thank you for letting us know',
  declining_message: 'We will be thinking of you on our special day.',
})

export function normalizeEventSectionsConfig(value = {}) {
  const source = value && typeof value === 'object' ? value : {}
  return {
    event_detail: source.event_detail !== false,
    participants: source.participants !== false,
    story: source.story !== false,
    quote: source.quote !== false,
    wish: source.wish !== false,
    gallery: source.gallery !== false,
    order: Array.isArray(source.order) ? [...source.order] : [...DEFAULT_SECTION_ORDER],
    rsvp: { ...defaultRsvpConfig(), ...(source.rsvp || {}) },
    dress_code: { ...defaultDressCodeConfig(), ...(source.dress_code || {}) },
    event_notes: { ...defaultEventNotesConfig(), ...(source.event_notes || {}) },
  }
}
```

- [ ] Ensure the utility never mutates the API payload and always returns fresh arrays for `order`, dress-code colors, and note items.
- [ ] Commit only the contract files:

```bash
git add pixelcore-backend/scheduling/serializers.py \
  pixelcore-backend/scheduling/test_event_website.py \
  pixelcore-frontend/utils/eventRsvpConfig.js
git commit -m "feat: define event RSVP customization contract"
```

## Task 2: Enforce the configured RSVP deadline on public responses

**Files:**

- Modify: `pixelcore-backend/scheduling/views.py:1145-1195`
- Modify: `pixelcore-backend/scheduling/test_event_website.py`

- [ ] Add a public RSVP test that stores a deadline in the past, PATCHes the token endpoint, and expects HTTP `409` with `error.code == "RSVP_CLOSED"`.
- [ ] Add a companion test with a future deadline and assert that the same response payload is accepted and saved.
- [ ] Add a small backend helper beside `PublicEventRsvpView` that reads only a valid ISO-8601 deadline from `sections_config.rsvp.deadline`, converts naive values using Django's current timezone, and returns `None` for absent values.
- [ ] Extend `PublicEventRsvpView.patch` so RSVP closes when any existing rule fails or the deadline has passed:

```python
deadline = event_rsvp_deadline(event)
if (
    not event.public_rsvp_enabled
    or event.status != "open"
    or (deadline and timezone.now() >= deadline)
):
    return Response(rsvp_closed_error(), status=status.HTTP_409_CONFLICT)
```

- [ ] Preserve the existing capacity validation, audit record, guest serialization, and error response shape.
- [ ] Commit the endpoint behavior:

```bash
git add pixelcore-backend/scheduling/views.py \
  pixelcore-backend/scheduling/test_event_website.py
git commit -m "feat: enforce event RSVP deadlines"
```

## Task 3: Add the URL-backed RSVP customization workspace tab

**Files:**

- Create: `pixelcore-frontend/components/scheduling/EventRsvpCustomizationTab.vue`
- Modify: `pixelcore-frontend/components/scheduling/EventRsvpWorkspace.vue:323-570,888-925,1410-1420`
- Modify: `pixelcore-frontend/components/scheduling/EventWebsiteEditor.vue:740-810,845-975`

- [ ] Add `rsvp` to the URL-backed `eventTabs` list immediately after `guests`, render a Shadcn `TabsTrigger` with a `MailCheck` icon, and mount `EventRsvpCustomizationTab` in a matching `TabsContent`.
- [ ] Pass `businessId` and `selectedEvent.public_id` to the new component and forward `updated` to the existing refresh handler so `?tab=rsvp` survives reloads and browser navigation.
- [ ] In the new component, load the current website record from `businesses/${businessId}/venue-events/${eventId}/website/`, normalize `sections_config`, and show distinct loading, error, save-error, and saved states.
- [ ] Build a readable, responsive Shadcn form with these groups:
  - RSVP copy: heading, subtitle, submit label, accept label, decline label, optional Maybe toggle.
  - Response fields: party size, dietary/accessibility notes, guest message, and maximum party size.
  - Deadline: date-time input, current-timezone hint, and clear action.
  - Confirmation: accepted and declined titles/messages.
  - Dress code: enable toggle, heading, subtitle, description, up to eight hex swatches, and a media selector filtered to this event's images.
  - Event notes: enable toggle and up to eight ordered note cards with icon, title, and body fields plus explicit up/down/remove controls.
- [ ] Use `Card`, `Alert`, `Button`, `Input`, `Label`, `Select`, `Switch`, `Textarea`, `Badge`, `Separator`, `Tooltip`, and `ScrollArea` from the existing shared UI library. Keep touch targets at least `h-10`; include visible labels and `aria-label` text on icon-only controls.
- [ ] Save by PATCHing only a merged `sections_config` object, leaving all unrelated website fields unchanged:

```js
await apiFetch(endpoint.value, {
  method: 'PATCH',
  body: {
    sections_config: {
      ...loadedSections.value,
      rsvp: cloneConfig(form.rsvp),
      dress_code: cloneConfig(form.dress_code),
      event_notes: cloneConfig(form.event_notes),
    },
  },
})
```

- [ ] Update `EventWebsiteEditor` to use `normalizeEventSectionsConfig` when loading and saving so saving the Website tab cannot erase settings authored in the RSVP tab.
- [ ] Keep `Wishes & RSVP` as an existing section visibility control; the new tab customizes its content rather than duplicating the visibility toggle.
- [ ] Commit the workspace UI:

```bash
git add pixelcore-frontend/components/scheduling/EventRsvpCustomizationTab.vue \
  pixelcore-frontend/components/scheduling/EventRsvpWorkspace.vue \
  pixelcore-frontend/components/scheduling/EventWebsiteEditor.vue
git commit -m "feat: add event RSVP customization tab"
```

## Task 4: Apply RSVP settings to every public event template

**Files:**

- Modify: `pixelcore-frontend/components/event/WeddingInvitationPage.vue:311-406,550-725,850-890`

- [ ] Import `normalizeEventSectionsConfig` and derive `rsvpConfig`, `dressCodeConfig`, and `eventNotesConfig` computed values from the public website payload.
- [ ] Replace the hard-coded RSVP heading, labels, maximum party size, button text, and field visibility with normalized configuration values while retaining the current `PublicRsvpSerializer` payload keys.
- [ ] Derive `rsvpClosed` from event status, `public_rsvp_enabled`, and the deadline. Show the deadline in the event timezone and explain why the form is closed.
- [ ] Render Maybe only when `allow_maybe` is true. If an existing guest already answered Maybe after the setting is disabled, keep that current choice visible so the guest can review or replace it.
- [ ] Constrain `party_size` to the configured maximum and the remaining event capacity already represented by the guest/event payload; never silently increase an existing party size.
- [ ] Add the configured dress-code panel and ordered event-note cards before the RSVP form for all templates. Render the event media URL only when present and maintain readable contrast over the current theme.
- [ ] Replace the simple `saved` label change with an elegant confirmation panel keyed to accepted or declined copy, including the guest's response summary and an `Edit response` action that restores the form.
- [ ] Keep the existing PATCH endpoint, save error presentation, wish carousel, attendance values, dietary field, message field, and audit behavior unchanged.
- [ ] Ensure the public form remains usable with JavaScript motion disabled and honors `prefers-reduced-motion` for its transition.
- [ ] Commit shared public behavior:

```bash
git add pixelcore-frontend/components/event/WeddingInvitationPage.vue
git commit -m "feat: customize public event RSVP experience"
```

## Task 5: Give Garden Vow its botanical invitation composition

**Files:**

- Create: `pixelcore-frontend/components/event/GardenBotanicalDecoration.vue`
- Modify: `pixelcore-frontend/components/event/WeddingInvitationPage.vue`
- Modify: `pixelcore-frontend/utils/eventTemplates.js`

- [ ] Add an `isGardenVow` computed flag based on the exact template value `wedding_garden`; do not infer the style from event type or color values.
- [ ] Build a decorative component from CSS borders, pseudo-elements, and restrained Lucide leaf/flower motifs. It must use `currentColor`, remain `aria-hidden`, avoid pointer events, and never become a required image asset.
- [ ] For Garden Vow only, compose a continuous invitation flow with:
  - an airy framed hero with centered couple names and date,
  - a botanical event timeline with clear time/title/location hierarchy,
  - a location/map block that retains existing Mapbox behavior,
  - a dress-code swatch and optional-image section,
  - elegant event-note cards,
  - a framed RSVP panel and confirmation state,
  - a restrained closing flourish and current footer content.
- [ ] Keep the existing media priority rules: configured hero, popup, participant, story, gallery, and closing assets remain authoritative and blank optional slots stay blank.
- [ ] Use only CSS variables sourced from the current `theme_background`, `theme_text`, and `theme_accent`. Do not reset Garden Vow to a hard-coded palette when a user has customized the theme.
- [ ] Scope all botanical CSS under `.template-garden` and confirm the editorial, modern, birthday, and general template markup/classes receive no layout regression.
- [ ] Preserve keyboard navigation, focus visibility, reduced-motion behavior, and mobile readability; no sideways scroll at 320px.
- [ ] Update Garden Vow's template description in `eventTemplates.js` to describe the botanical invitation without changing its saved value or default color/font preset.
- [ ] Commit the template presentation:

```bash
git add pixelcore-frontend/components/event/GardenBotanicalDecoration.vue \
  pixelcore-frontend/components/event/WeddingInvitationPage.vue \
  pixelcore-frontend/utils/eventTemplates.js
git commit -m "feat: add Garden Vow botanical invitation"
```

## Task 6: Update the design brief and run one focused verification pass

**Files:**

- Modify: `.impeccable/surfaces/pixelcore-frontend-pages-event-eventid-rsvp-token-vue.md`
- Modify: `.impeccable/surfaces/pixelcore-frontend-components-scheduling-eventrsvpworkspace-vue.md`

- [ ] Record the new RSVP customization information architecture, Garden Vow-only botanical exception, continuous invitation flow, responsive rules, and preserved theme contract in the two existing surface briefs.
- [ ] Scan all task files for placeholders and accidental debug residue:

```bash
rg -n "TBD|TODO|FIXME|console\.log|debugger" \
  pixelcore-backend/scheduling/serializers.py \
  pixelcore-backend/scheduling/views.py \
  pixelcore-backend/scheduling/test_event_website.py \
  pixelcore-frontend/components/scheduling/EventRsvpCustomizationTab.vue \
  pixelcore-frontend/components/scheduling/EventRsvpWorkspace.vue \
  pixelcore-frontend/components/scheduling/EventWebsiteEditor.vue \
  pixelcore-frontend/components/event/GardenBotanicalDecoration.vue \
  pixelcore-frontend/components/event/WeddingInvitationPage.vue \
  pixelcore-frontend/utils/eventRsvpConfig.js \
  pixelcore-frontend/utils/eventTemplates.js
```

Expected: no newly introduced placeholders, debug logging, or debugger statements.

- [ ] Run the single focused verification pass:

```bash
cd /home/bomiku1/projects/pixelcore-platform
docker compose exec backend python manage.py test scheduling.test_event_website.EventWebsiteApiTests
docker compose exec frontend npm run check:vue
docker compose exec frontend npm run check:ui
git diff --check -- \
  pixelcore-backend/scheduling/serializers.py \
  pixelcore-backend/scheduling/views.py \
  pixelcore-backend/scheduling/test_event_website.py \
  pixelcore-frontend/components/scheduling/EventRsvpCustomizationTab.vue \
  pixelcore-frontend/components/scheduling/EventRsvpWorkspace.vue \
  pixelcore-frontend/components/scheduling/EventWebsiteEditor.vue \
  pixelcore-frontend/components/event/GardenBotanicalDecoration.vue \
  pixelcore-frontend/components/event/WeddingInvitationPage.vue \
  pixelcore-frontend/utils/eventRsvpConfig.js \
  pixelcore-frontend/utils/eventTemplates.js \
  .impeccable/surfaces/pixelcore-frontend-pages-event-eventid-rsvp-token-vue.md \
  .impeccable/surfaces/pixelcore-frontend-components-scheduling-eventrsvpworkspace-vue.md
```

Expected: targeted Django tests pass, both frontend checks exit `0`, and `git diff --check` prints no errors.

- [ ] Manually inspect the code paths without launching a broad browser sweep:
  - `?tab=rsvp` survives reload and browser back/forward.
  - Saving the Website tab preserves nested RSVP, dress-code, and event-note settings.
  - Garden Vow receives the botanical composition; other templates retain their layout.
  - Deadline, Maybe visibility, optional fields, success state, and Edit response behave from payload state.
  - Empty dress-code media and empty event notes do not create blank visual gaps.
- [ ] Commit the briefs and any focused verification repairs:

```bash
git add .impeccable/surfaces/pixelcore-frontend-pages-event-eventid-rsvp-token-vue.md \
  .impeccable/surfaces/pixelcore-frontend-components-scheduling-eventrsvpworkspace-vue.md
git commit -m "docs: update event RSVP experience brief"
```

## Final Self-Review

- [ ] Confirm every approved spec requirement is represented by a task: universal RSVP settings, deadline enforcement, dress code, ordered notes, confirmation states, Garden Vow-only botanical presentation, preserved theme/media values, accessibility, and no migration.
- [ ] Confirm frontend and backend use the same nested keys and limits (`rsvp`, `dress_code`, `event_notes`; 8 colors; 8 notes; max party size 1–50).
- [ ] Confirm no implementation file contains unfinished placeholder markers, placeholder interfaces, or invented API routes.
- [ ] Confirm the task did not modify DineEase or stage unrelated PixelCore work.
