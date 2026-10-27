export const clearSmokeyConversations = () => {
  try {
    const storage = window.sessionStorage
    Object.keys(storage)
      .filter((key) => key.startsWith('smokey.conversation.v1:'))
      .forEach((key) => storage.removeItem(key))
  } catch {
    // Session cleanup must not prevent logout when storage is unavailable.
  }
}
