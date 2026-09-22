function safeTimezone(timezone) {
  try {
    new Intl.DateTimeFormat('en-US', { timeZone: timezone }).format()
    return timezone
  } catch {
    return 'UTC'
  }
}

export function formatWorkspaceClock(value, timezone = 'UTC') {
  const date = value instanceof Date ? value : new Date(value)
  const resolvedTimezone = safeTimezone(timezone || 'UTC')

  return {
    time: new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      timeZone: resolvedTimezone,
    }).format(date),
    date: new Intl.DateTimeFormat('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      timeZone: resolvedTimezone,
    }).format(date),
    dateTime: date.toISOString(),
    timezone: resolvedTimezone,
  }
}

export function workspaceUserPresentation(user = {}) {
  const fullName = [user.first_name, user.last_name]
    .map(value => String(value || '').trim())
    .filter(Boolean)
    .join(' ')
  const email = String(user.email || '').trim()
  const displayName = fullName
    || String(user.username || '').trim()
    || email.split('@')[0]
    || 'Account'
  const words = displayName.split(/\s+/).filter(Boolean)
  const initials = words.length > 1
    ? `${words[0][0]}${words.at(-1)[0]}`.toUpperCase()
    : displayName.slice(0, 2).toUpperCase()

  return {
    displayName,
    initials,
    email,
  }
}
