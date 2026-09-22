import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    initialized: false,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
  },
  actions: {
    async login(credentials) {
      const { accessToken } = useApiClient()
      const config = useRuntimeConfig()
      this.loading = true
      try {
        const response = await $fetch('auth/login/', {
          baseURL: config.public.apiBaseUrl,
          method: 'POST',
          body: credentials,
          credentials: 'include',
        })
        accessToken.value = response.access
        await this.loadUser()
        return response
      } finally {
        this.loading = false
      }
    },
    async register(payload) {
      const config = useRuntimeConfig()
      return await $fetch('auth/register/', {
        baseURL: config.public.apiBaseUrl,
        method: 'POST',
        body: payload,
        credentials: 'include',
      })
    },
    async verifyEmail(payload) {
      return await this.completeAuthentication('auth/verify-email/', payload)
    },
    async google(credential) {
      return await this.completeAuthentication('auth/google/', { credential })
    },
    async completeAuthentication(endpoint, body) {
      const { accessToken } = useApiClient()
      const config = useRuntimeConfig()
      this.loading = true
      try {
        const response = await $fetch(endpoint, {
          baseURL: config.public.apiBaseUrl,
          method: 'POST',
          body,
          credentials: 'include',
        })
        accessToken.value = response.access
        await this.loadUser()
        return response
      } finally {
        this.loading = false
      }
    },
    async forgotPassword(identifier) {
      const config = useRuntimeConfig()
      return await $fetch('auth/password/forgot/', {
        baseURL: config.public.apiBaseUrl,
        method: 'POST',
        body: { identifier },
      })
    },
    async resetPassword(payload) {
      const config = useRuntimeConfig()
      return await $fetch('auth/password/reset/', {
        baseURL: config.public.apiBaseUrl,
        method: 'POST',
        body: payload,
      })
    },
    async loadUser() {
      const { apiFetch } = useApiClient()
      this.user = await apiFetch('auth/me/')
      this.initialized = true
      return this.user
    },
    async restoreSession() {
      if (this.initialized) return this.user
      const { refreshAccess } = useApiClient()
      try {
        await refreshAccess()
        return await this.loadUser()
      } catch {
        this.user = null
        this.initialized = true
        return null
      }
    },
    async logout() {
      const { accessToken } = useApiClient()
      const config = useRuntimeConfig()
      try {
        await $fetch('auth/logout/', {
          baseURL: config.public.apiBaseUrl,
          method: 'POST',
          credentials: 'include',
        })
      } finally {
        accessToken.value = null
        this.user = null
        this.initialized = true
      }
    },
  },
})
