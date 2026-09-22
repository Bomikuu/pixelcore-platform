export function useStorefrontContext(slug) {
  const config = useRuntimeConfig()
  const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
  const { data: identity, pending, error } = useAsyncData(`identity:${slug}`, () => $fetch(`public/businesses/${slug}/identity/`, { baseURL }))
  const { data: home } = useAsyncData(`navigation:${slug}`, () => $fetch(`public/${slug}/site/`, { baseURL }).catch(() => null))
  const navigation = computed(() => home.value?.site?.navigation || [{ id: 'shop', label: 'Shop', path: '/shop' }, { id: 'services', label: 'Services', path: '/services' }])
  const requestUrl = useRequestURL()
  const hostname = requestUrl.hostname.toLowerCase()
  const isCustomHost = !['localhost', '127.0.0.1', config.public.platformDomain].includes(hostname) && !hostname.endsWith(`.${config.public.platformDomain}`)
  const siteBase = isCustomHost ? '' : `/site/${slug}`
  return { identity, navigation, pending, error, baseURL, siteBase }
}
