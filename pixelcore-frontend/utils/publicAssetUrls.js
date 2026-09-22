function replaceInternalAssetUrl(value, publicOrigin, internalOrigin) {
  if (typeof value !== 'string' || !value.includes('/media/')) return value

  try {
    const url = new URL(value)
    if (url.origin !== internalOrigin || !url.pathname.startsWith('/media/')) {
      return value
    }
    return new URL(`${url.pathname}${url.search}${url.hash}`, publicOrigin).toString()
  } catch {
    return value
  }
}

/**
 * Prevent Docker-only API origins from leaking into server-rendered payloads.
 * Django still owns the media path; only its internal origin is replaced.
 */
export function normalizePublicAssetUrls(payload, options) {
  const publicOrigin = new URL(options.publicOrigin).origin
  const internalOrigin = new URL(options.internalApiBaseUrl, publicOrigin).origin

  function normalize(value) {
    if (Array.isArray(value)) return value.map(normalize)
    if (value && typeof value === 'object') {
      return Object.fromEntries(
        Object.entries(value).map(([key, nestedValue]) => [key, normalize(nestedValue)]),
      )
    }
    return replaceInternalAssetUrl(value, publicOrigin, internalOrigin)
  }

  return normalize(payload)
}
