// Poll visible workspaces only. Never replace an open review or a newer request's data.
export function useLiveWorkspaceResource(resource, query = () => ({}), paused = ref(false)) {
  const business = useBusinessStore()
  const { apiFetch } = useApiClient()
  const data = ref(null), loading = ref(true), refreshing = ref(false), error = ref(''), updatedAt = ref(null), live = ref(true)
  let mounted = false, disposed = false, timer, generation = 0
  async function refresh() {
    if (!business.activeBusiness) return
    const current = ++generation
    refreshing.value = true; error.value = ''
    try {
      const params = new URLSearchParams(Object.entries(query()).filter(([, value]) => value !== undefined && value !== '').map(([key, value]) => [key, String(value)]))
      const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/${resource()}?${params}`)
      if (current !== generation || !mounted) return
      data.value = response; updatedAt.value = new Date()
    } catch (exception) {
      if (current === generation) error.value = exception?.data?.error?.message || 'Could not refresh this workspace. Check your connection or access and try again.'
    } finally { if (current === generation) { loading.value = false; refreshing.value = false } }
  }
  watch(() => `${business.activeBusiness?.public_id}:${JSON.stringify(query())}`, () => {
    if (!mounted) return
    data.value = null; loading.value = true; refresh()
  })
  onMounted(async () => {
    try { if (!business.activeBusiness) await business.loadBusinesses() }
    catch { error.value = 'Your business could not be loaded.'; loading.value = false; return }
    if (disposed) return
    mounted = true; refresh()
    timer = setInterval(() => { if (live.value && !document.hidden && !toValue(paused) && !refreshing.value) refresh() }, 30000)
  })
  onBeforeUnmount(() => { disposed = true; mounted = false; generation++; clearInterval(timer) })
  return { data, loading, refreshing, error, updatedAt, live, refresh }
}
