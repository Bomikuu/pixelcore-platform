import assert from 'node:assert/strict'
import test from 'node:test'

import * as rsvpConfig from './eventRsvpConfig.js'

test('resolveRsvpAvailability closes responses after the configured deadline', () => {
  const availability = rsvpConfig.resolveRsvpAvailability?.({
    eventStatus: 'open',
    publicRsvpEnabled: true,
    deadline: '2026-09-20T10:00:00.000Z',
    now: Date.parse('2026-09-20T10:00:01.000Z'),
  })

  assert.deepEqual(availability, {
    isClosed: true,
    reason: 'deadline',
    deadlineAt: Date.parse('2026-09-20T10:00:00.000Z'),
  })
})

test('resolveRsvpAvailability keeps an open event available without a deadline', () => {
  const availability = rsvpConfig.resolveRsvpAvailability?.({
    eventStatus: 'open',
    publicRsvpEnabled: true,
    deadline: null,
    now: Date.parse('2026-09-16T10:00:00.000Z'),
  })

  assert.deepEqual(availability, {
    isClosed: false,
    reason: null,
    deadlineAt: null,
  })
})

test('buildRsvpPreviewPath targets the authenticated workspace preview', () => {
  const path = rsvpConfig.buildRsvpPreviewPath?.({
    eventId: 'event-123',
    businessId: 'business-456',
  })

  assert.equal(
    path,
    '/workspace/schedule/events/event-123/rsvp-preview?business=business-456',
  )
})

test('createRsvpPreviewPayload combines event website data with a sample guest', () => {
  const payload = rsvpConfig.createRsvpPreviewPayload?.({
    event: {
      public_id: 'event-123',
      title: 'Alex and Jamie',
      status: 'open',
      max_guests: 120,
    },
    website: {
      website_template: 'wedding_garden',
      invitation_text: 'Celebrate with us.',
    },
  })

  assert.deepEqual(payload, {
    event: {
      public_id: 'event-123',
      title: 'Alex and Jamie',
      status: 'open',
      max_guests: 120,
      website: {
        website_template: 'wedding_garden',
        invitation_text: 'Celebrate with us.',
      },
    },
    guest: {
      full_name: 'Preview guest',
      response: 'pending',
      party_size: 1,
      dietary_notes: '',
      guest_message: '',
    },
  })
})
