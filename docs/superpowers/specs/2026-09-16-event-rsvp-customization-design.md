# Event RSVP Customization and Garden Vow Invitation Design

## Scope

Add a dedicated RSVP customization tab to the existing event workspace and use its settings across every event template. Redesign only the existing `wedding_garden` public template as an elegant botanical invitation. Preserve the current event, guest, website, media, schedule, map, wish, and RSVP APIs.

This work does not add or modify Django models. Customization is stored in the existing `VenueEvent.sections_config` JSON field and returned through the existing event website serializer.

## Goals

- Make RSVP presentation and optional fields configurable from a clearly named event tab.
- Keep guest management separate from guest-facing RSVP presentation.
- Preserve private guest links and the existing RSVP endpoint.
- Give Garden Vow a continuous botanical stationery composition while retaining its existing theme colors and font controls.
- Keep every other event template visually unchanged except for consuming the shared RSVP configuration.
- Preserve responsive behavior, keyboard access, reduced-motion behavior, and clear loading, saved, and error states.

## Workspace Information Architecture

Add `rsvp` to the existing URL-backed event tab set and place **RSVP customization** after **Guests & seating**.

The new `EventRsvpCustomizationTab` component owns guest-facing RSVP configuration. It loads the existing event website endpoint, edits only RSVP-related values inside `sections_config`, merges those values with the latest server response, and saves through the existing website PATCH endpoint.

The tab contains four focused groups:

1. **Response experience**
   - RSVP section heading and script subtitle
   - Optional response deadline
   - Submit-button label
   - Accepted and declined labels
   - Optional `Maybe` response
2. **Guest fields**
   - Party-size field toggle
   - Dietary and accessibility notes toggle
   - Guest message toggle
   - Maximum party size, constrained by the configured limit and remaining event capacity
3. **Dress code**
   - Section visibility
   - Heading, script subtitle, and description
   - Ordered color swatches
   - Optional image selected from existing event media
4. **Details and confirmation**
   - Ordered event notes with title and body
   - Attending confirmation title and message
   - Declining confirmation title and message

All controls use the existing Shadcn primitives, workspace spacing, and event editor language. Reorderable items use explicit up/down icon buttons rather than drag-only behavior.

## Configuration Contract

Extend the existing `sections_config` object with three nested objects. Existing section visibility booleans and the section order remain unchanged.

```json
{
  "event_detail": true,
  "participants": true,
  "story": true,
  "quote": true,
  "wish": true,
  "gallery": true,
  "order": ["hero", "event_detail", "participants", "story", "quote", "wish", "gallery"],
  "rsvp": {
    "heading": "RSVP",
    "subtitle": "Will you celebrate with us?",
    "deadline": null,
    "submit_label": "Send RSVP",
    "accept_label": "Joyfully accept",
    "decline_label": "Regretfully decline",
    "allow_maybe": false,
    "show_party_size": true,
    "show_dietary_notes": true,
    "show_guest_message": true,
    "max_party_size": 10,
    "attending_title": "Thank you",
    "attending_message": "We are so happy you will celebrate with us.",
    "declining_title": "Thank you for letting us know",
    "declining_message": "We will be thinking of you on our special day."
  },
  "dress_code": {
    "enabled": false,
    "heading": "Dress code",
    "subtitle": "Color palette and style",
    "description": "",
    "colors": [],
    "media_public_id": null
  },
  "event_notes": {
    "enabled": false,
    "heading": "Details",
    "subtitle": "A few thoughtful notes",
    "items": []
  }
}
```

The serializer accepts these keys, normalizes missing nested values to defaults, validates dates, lengths, color values, media ownership, and numeric limits, and rejects unsupported nested keys. Existing events receive complete frontend defaults without requiring a data migration.

## RSVP Behavior

The private RSVP page remains token-based. Known guest information remains prefilled and read-only where appropriate.

Attendance uses elegant button choices instead of a select. Accepted and declined are always available. Maybe appears only when enabled. Attendance-specific fields appear only for accepted responses and only when enabled. The optional guest message may remain available for declined responses.

The server remains authoritative for capacity. It additionally treats the configured RSVP deadline as closed once the deadline has passed. The frontend reflects the same state for immediate feedback, but the backend check prevents late direct API submissions.

While saving, the submit button retains its width and shows a compact loader. Validation errors appear below the relevant form area. A successful response transitions the form to a botanical confirmation state based on accepted or declined status. An **Edit response** action restores the form when the existing backend still permits changes.

## Garden Vow Public Composition

Only `wedding_garden` receives the new botanical visual composition. The implementation branches from the existing public invitation component through the current template class instead of creating a second RSVP implementation.

Garden Vow retains its current defaults:

- background: `#162019`
- text/paper: `#F4EFE4`
- accent: `#C7A77A`
- heading font: Cormorant Garamond
- body font: Manrope

User-configured theme values remain authoritative. Paper, subdued ink, botanical strokes, and soft surface variations are derived with CSS `color-mix()` and transparent layers rather than adding more model fields.

The Garden Vow reading sequence is:

1. Short personalized reveal
2. Paper-style hero with date watermark and participant names
3. Welcome copy
4. Interactive vertical schedule timeline
5. Venue and restrained Mapbox map
6. Configured dress code
7. Configured event notes
8. Personalized RSVP
9. Approved wishes
10. Closing image and message

The page reads as one continuous invitation rather than a stack of dashboard cards. Ivory paper surfaces, generous whitespace, fine champagne dividers, and botanical linework separate sections. Decorative botanical assets are code-native CSS/SVG geometry, stay outside readable copy, and reuse a small set of intentional variations.

The current Editorial Noir, Modern Ceremony, birthday, and general templates retain their present composition. They consume the shared RSVP labels, field visibility, deadline, notes, dress-code content, and confirmation copy without receiving Garden Vow's botanical page treatment.

## Motion and Accessibility

- Use the existing intersection-observer reveal system.
- Garden Vow adds restrained line growth, divider reveal, image settling, and botanical parallax.
- Motion uses slow ease-out timing with no bounce or spring behavior.
- `prefers-reduced-motion` disables parallax and reveals content immediately.
- Decorative botanical elements are hidden from assistive technology and never intercept pointer events.
- Form controls retain visible focus states, real labels, and sufficient contrast.
- Timeline and response controls remain keyboard operable.

## Empty and Error States

- Missing dress-code imagery still produces a complete color-and-type composition.
- Missing swatches hide the swatch row rather than showing placeholders publicly.
- Empty event notes hide the details section.
- Missing location coordinates retain the venue address and directions link without rendering a broken map.
- Public RSVP without a guest token displays the existing private-link guidance.
- Closed or expired RSVP displays the configured deadline and a concise organizer-contact message.
- Failed settings saves preserve unsaved form values and show an inline recovery message.

## Files and Boundaries

Expected implementation targets:

- `pixelcore-frontend/components/scheduling/EventRsvpWorkspace.vue`
- `pixelcore-frontend/components/scheduling/EventRsvpCustomizationTab.vue` (new)
- `pixelcore-frontend/components/event/WeddingInvitationPage.vue`
- `pixelcore-frontend/components/event/GardenBotanicalDecoration.vue` (new, if separation improves readability)
- `pixelcore-frontend/components/scheduling/EventWebsiteEditor.vue`
- `pixelcore-frontend/utils/eventRsvpConfig.js` (new shared defaults and normalization)
- `pixelcore-backend/scheduling/serializers.py`
- `pixelcore-backend/scheduling/views.py`
- focused scheduling website and RSVP tests

No Django model or migration file is part of this implementation.

## Verification

Run one focused verification pass:

- frontend Vue syntax check
- Shadcn boundary check
- backend Django system check
- focused event website and RSVP backend tests
- Impeccable detector for the affected public invitation and workspace components
- `git diff --check`

Runtime visual verification is a separate optional pass because it requires signed-in workspace state and a personalized public guest link.
