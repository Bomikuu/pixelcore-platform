const DEFAULT_SECTION_ORDER = [
  'hero',
  'event_detail',
  'participants',
  'story',
  'quote',
  'wish',
  'gallery',
]

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

export const defaultDressCodeConfig = () => ({
  enabled: false,
  heading: 'Dress code',
  subtitle: 'Color palette and style',
  description: '',
  colors: [],
  media_public_id: null,
  media_url: null,
})

export const defaultEventNotesConfig = () => ({
  enabled: false,
  heading: 'Details',
  subtitle: 'A few thoughtful notes',
  items: [],
})

function cloneNotes(items) {
  if (!Array.isArray(items)) return []
  return items.map(item => ({
    icon: String(item?.icon || 'info'),
    title: String(item?.title || ''),
    body: String(item?.body || ''),
  }))
}

export function normalizeEventSectionsConfig(value = {}) {
  const source = value && typeof value === 'object' && !Array.isArray(value)
    ? value
    : {}
  const rsvp = source.rsvp && typeof source.rsvp === 'object' ? source.rsvp : {}
  const dressCode = source.dress_code && typeof source.dress_code === 'object'
    ? source.dress_code
    : {}
  const eventNotes = source.event_notes && typeof source.event_notes === 'object'
    ? source.event_notes
    : {}

  return {
    event_detail: source.event_detail !== false,
    participants: source.participants !== false,
    story: source.story !== false,
    quote: source.quote !== false,
    wish: source.wish !== false,
    gallery: source.gallery !== false,
    order: Array.isArray(source.order) ? [...source.order] : [...DEFAULT_SECTION_ORDER],
    rsvp: {
      ...defaultRsvpConfig(),
      ...rsvp,
    },
    dress_code: {
      ...defaultDressCodeConfig(),
      ...dressCode,
      colors: Array.isArray(dressCode.colors) ? [...dressCode.colors] : [],
    },
    event_notes: {
      ...defaultEventNotesConfig(),
      ...eventNotes,
      items: cloneNotes(eventNotes.items),
    },
  }
}

export function cloneEventSectionsConfig(value = {}) {
  const normalized = normalizeEventSectionsConfig(value)
  return {
    ...normalized,
    order: [...normalized.order],
    rsvp: { ...normalized.rsvp },
    dress_code: {
      ...normalized.dress_code,
      colors: [...normalized.dress_code.colors],
    },
    event_notes: {
      ...normalized.event_notes,
      items: normalized.event_notes.items.map(item => ({ ...item })),
    },
  }
}

export function resolveRsvpAvailability({
  eventStatus,
  publicRsvpEnabled,
  deadline,
  now = Date.now(),
}) {
  const parsedDeadline = deadline ? Date.parse(deadline) : Number.NaN
  const deadlineAt = Number.isNaN(parsedDeadline) ? null : parsedDeadline
  const deadlinePassed = deadlineAt !== null && now >= deadlineAt

  if (deadlinePassed) {
    return { isClosed: true, reason: 'deadline', deadlineAt }
  }
  if (eventStatus !== 'open') {
    return { isClosed: true, reason: 'status', deadlineAt }
  }
  if (!publicRsvpEnabled) {
    return { isClosed: true, reason: 'disabled', deadlineAt }
  }
  return { isClosed: false, reason: null, deadlineAt }
}

export function buildRsvpPreviewPath({ eventId, businessId }) {
  return `/workspace/schedule/events/${encodeURIComponent(eventId)}/rsvp-preview?business=${encodeURIComponent(businessId)}`
}

export function createRsvpPreviewPayload({ event, website }) {
  return {
    event: {
      ...event,
      website: { ...website },
    },
    guest: {
      full_name: 'Preview guest',
      response: 'pending',
      party_size: 1,
      dietary_notes: '',
      guest_message: '',
    },
  }
}
