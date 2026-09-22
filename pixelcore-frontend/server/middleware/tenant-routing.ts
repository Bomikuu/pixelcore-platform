export default defineEventHandler(async (event) => {
  const url = getRequestURL(event)
  const hostname = url.hostname.toLowerCase()
  const config = useRuntimeConfig(event)
  const platformDomain = String(config.public.platformDomain || 'pixelcore.localhost')
  const platformHost = ['localhost', '127.0.0.1', platformDomain].includes(hostname) || hostname.endsWith(`.${platformDomain}`)
  const internalPath = url.pathname.startsWith('/_nuxt/') || url.pathname.startsWith('/api/') || url.pathname.startsWith('/site/') || url.pathname === '/favicon.ico'
  if (platformHost || internalPath) return
  try {
    const manifest = await $fetch<any>('public/site/resolve/', {
      baseURL: config.apiInternalBaseUrl,
      query: { host: hostname, path: '/' },
    })
    const rewritten = `/site/${manifest.identity.slug}${url.pathname}${url.search}`
    event.node.req.url = rewritten
  } catch {
    // The regular Nuxt 404 path handles unknown or inactive domains.
  }
})
