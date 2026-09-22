export function useApiClient() {
  const config = useRuntimeConfig()
  const accessToken = useState('pixelcore-access-token', () => null)
  const refreshPromise = useState('pixelcore-refresh-promise', () => null)

  async function refreshAccess() {
    if (!refreshPromise.value) {
      refreshPromise.value = $fetch('auth/refresh/', {
        baseURL: config.public.apiBaseUrl,
        method: 'POST',
        credentials: 'include',
      }).then((response) => {
        accessToken.value = response.access
        return response.access
      }).finally(() => {
        refreshPromise.value = null
      })
    }
    return refreshPromise.value
  }

  async function apiFetch(path, options = {}, retry = true) {
    const headers = new Headers(options.headers || {})
    if (accessToken.value) {
      headers.set('Authorization', `Bearer ${accessToken.value}`)
    }

    try {
      return await $fetch(path, {
        ...options,
        baseURL: config.public.apiBaseUrl,
        headers,
        credentials: 'include',
      })
    } catch (error) {
      if (retry && error?.response?.status === 401) {
        await refreshAccess()
        return apiFetch(path, options, false)
      }
      throw error
    }
  }

  return { accessToken, apiFetch, refreshAccess }
}
