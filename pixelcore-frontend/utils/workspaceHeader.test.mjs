import assert from 'node:assert/strict'
import test from 'node:test'

let workspaceHeader = {}
try {
  workspaceHeader = await import('./workspaceHeader.js')
} catch {
  workspaceHeader = {}
}

test('formatWorkspaceClock displays the active business timezone', () => {
  const clock = workspaceHeader.formatWorkspaceClock?.(
    new Date('2026-09-16T08:05:00.000Z'),
    'Asia/Manila',
  )

  assert.deepEqual(clock, {
    time: '4:05 PM',
    date: 'Wed, Sep 16',
    dateTime: '2026-09-16T08:05:00.000Z',
    timezone: 'Asia/Manila',
  })
})

test('workspaceUserPresentation derives a readable name and initials', () => {
  const identity = workspaceHeader.workspaceUserPresentation?.({
    first_name: 'Mico',
    last_name: 'Ang',
    username: 'mico',
    email: 'mico@example.com',
  })

  assert.deepEqual(identity, {
    displayName: 'Mico Ang',
    initials: 'MA',
    email: 'mico@example.com',
  })
})
