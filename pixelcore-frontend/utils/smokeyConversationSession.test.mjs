import test from 'node:test'
import assert from 'node:assert/strict'
import { clearSmokeyConversations } from './smokeyConversationSession.js'

test('logout clears scoped Smokey sessions while preserving unrelated preferences', () => {
  const original = globalThis.window
  const storage = {
    'smokey.conversation.v1:business-a': 'private draft',
    'smokey.conversation.v1:business-b': 'other draft',
    theme: 'dark',
    removeItem: (key) => { delete storage[key] },
  }
  try {
    globalThis.window = { sessionStorage: storage }
    clearSmokeyConversations()
    assert.equal(storage['smokey.conversation.v1:business-a'], undefined)
    assert.equal(storage['smokey.conversation.v1:business-b'], undefined)
    assert.equal(storage.theme, 'dark')
    globalThis.window = { get sessionStorage() { throw new Error('Blocked') } }
    assert.doesNotThrow(clearSmokeyConversations)
  } finally {
    globalThis.window = original
  }
})
