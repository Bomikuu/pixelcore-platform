---
version: 1
slug: "pixelcore-frontend-pages-event-eventid-rsvp-token-vue"
primary_target: "pixelcore-frontend/pages/event/[eventId]/rsvp/[token].vue"
related_targets: ["pixelcore-frontend/pages/event/[eventId]/index.vue","pixelcore-frontend/components/event/WeddingInvitationPage.vue","pixelcore-frontend/components/event/EventRsvpResponsePage.vue","pixelcore-frontend/components/scheduling/EventWebsiteEditor.vue","pixelcore-frontend/components/scheduling/EventRsvpWorkspace.vue"]
---

SCOPE: Public event invitation and its event-detail website editor. Persuade mode for invited guests; Operate mode for organizers.

THESIS: Every invitation unfolds as an authored event world, not a generic microsite or stack of cards. Wedding, birthday, and general-event families each offer three compositions while preserving editable identity tokens.

OWN-WORLD: Each saved template retains its authored palette, typography, and imagery. Editorial Noir keeps near-black fields and grayscale photography. Garden Vow alone uses airy botanical framing, fine accent-colored rules, floral geometry, softer imagery, and its existing Cormorant-led theme without overwriting organizer color or font choices.

STORY: The public landing page remains the complete event story: a guest enters through a cinematic image, recognizes whose celebration and when, follows the schedule, people, guidance, story, gallery, approved wishes, and deliberate footer. The private token link opens a separate task-focused response page with a clear return to the full invitation.

FIRST VIEWPORT: One full-viewport photograph holds a centered personalized invitation; a translucent date spans the lower edge while a full-width header centers either the business logo or a configurable Playball event mark such as Alex × Jamie. Compact section links, the date, and one save-the-date action remain readable. An optional live countdown sits within a thin ruled band and yields to a calm event-started message when time reaches zero.

ENTRY: An optional on-brand welcome dialog introduces the event and supplies the user gesture required for background audio. Audio never autoplays without consent and remains controllable from the landing page.

MEDIA ROLES: Hero, welcome popup, and closing each own one replaceable image slot and never appear in the generic placement selector. Wedding participants each accept an independently assigned portrait through direct upload or replacement beside that person; participant media never appears as a Gallery destination or chooser. Story passages support an in-context upload or selection from the reusable story library; an unassigned story remains intentionally text-only. Gallery photographs are an always-visible ordered collection that never depends on reveal-state JavaScript. The closing image owns a full-viewport chapter independent of gallery visibility.

LOCATION: Organizers search Mapbox by address or venue, choose a suggestion, and review the resulting map pin instead of entering latitude and longitude. Coordinates remain internal schedule data, while the published directions link remains available when the static preview is unavailable.

SCHEDULE: The event programme is a tall alternating timeline built around one continuous central line, large times, clear titles, venue context, and restrained event icons. Selecting a step updates the focused time, venue, directions, and map without navigating away, while the ordered sequence remains keyboard accessible.

RSVP: The response form never appears inside the public landing page. `/event/:eventId/rsvp/:token` is a dedicated, no-index private surface that carries the saved event palette, fonts, Garden Vow decoration, hero image, event date, time, and venue beside the form. A dedicated organizer tab controls headings, response labels, Maybe availability, party size, dietary/accessibility notes, guest messages, deadline, and post-submit copy for every template. The server enforces the same deadline and party limit shown to the guest. A submitted response becomes an elegant confirmation state with a summary, Edit response action, and return link to the full invitation.

GUEST GUIDANCE: Optional dress-code guidance combines concise copy, up to eight color swatches, and one event-owned image. Ordered event notes cover practical details such as parking, gifts, accommodation, food, or arrival. Both remain on the public landing page and disappear without leaving gaps when disabled; separating RSVP must never remove event information from the invitation.

GARDEN VOW: Only `wedding_garden` receives the botanical composition: framed opening and closing chapters, restrained generated floral accents, an accent-led timeline, quiet guidance panels, and a framed RSVP moment. Decoration uses CSS geometry and Lucide motifs, is ignored by assistive technology, never blocks interaction, and never replaces real event media.

WISHES: Organizers choose whether approved messages appear as they are approved or remain server-withheld until the event start time. The event-day state carries its own live countdown and unlocks automatically; released wishes refresh in-place and move through a continuous horizontal carousel with richer attribution, an explicit pause/play control, hover and focus pausing, and a complete reduced-motion fallback.

STORY JUMP: Before the story is reached, a compact Shadcn action floats at the bottom of the viewport with a clear hover lift. It leaves the interface as the story enters view and returns only when the guest scrolls back above it.

MOTION: As the guest scrolls, editorial copy rises while photographs reveal through a vertical mask. One IntersectionObserver coordinates the landing sequence. The dedicated RSVP page opens with one clipped image reveal and a delayed form-panel entrance; confirmation uses one short blur-and-rise transition. Reduced-motion visitors receive both compositions immediately.

EMPTY STATE: Missing schedules, people, story, quote, map, wishes, and gallery media retain the full composition with restrained, public-safe editorial placeholders; absence never looks like a broken template.

FORM: Direct brief-pinned editorial composition; no concept seed was required because the supplied reference fixes the visual world, content sequence, and signature motion.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
