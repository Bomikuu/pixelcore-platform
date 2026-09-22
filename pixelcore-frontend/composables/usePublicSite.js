export function usePublicSite(slug, pageSlug = '') {
  const config = useRuntimeConfig()
  const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
  const manifestPath = pageSlug ? `public/${slug}/site/${pageSlug}/` : `public/${slug}/site/`
  const { data: manifest, pending, error, refresh } = useAsyncData(
    `site:${slug}:${pageSlug || 'home'}`,
    () => $fetch(manifestPath, { baseURL }),
  )
  return { manifest, pending, error, refresh }
}
