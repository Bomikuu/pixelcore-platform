import { defineStore } from 'pinia'

export const useWishlistStore = defineStore('wishlist', {
  state: () => ({ slug: '', ids: [], merged: false }),
  getters: {
    has: (state) => (id) => state.ids.includes(id),
    count: (state) => state.ids.length,
  },
  actions: {
    hydrate(slug) {
      if (!import.meta.client || this.slug === slug) return
      this.slug = slug
      try { this.ids = JSON.parse(localStorage.getItem(`pixelcore-wishlist:${slug}`) || '[]') } catch { this.ids = [] }
    },
    persist() {
      if (import.meta.client && this.slug) localStorage.setItem(`pixelcore-wishlist:${this.slug}`, JSON.stringify(this.ids))
    },
    toggle(slug, id) {
      this.hydrate(slug)
      this.ids = this.ids.includes(id) ? this.ids.filter((item) => item !== id) : [...this.ids, id]
      this.persist()
    },
    async mergeIfSignedIn(slug) {
      this.hydrate(slug)
      if (this.merged || !this.ids.length) return
      const auth = useAuthStore()
      if (!auth.isAuthenticated) return
      const { apiFetch } = useApiClient()
      const saved = await apiFetch(`public/${slug}/portal/saved/merge/`, { method: 'POST', body: { offering_public_ids: this.ids } })
      this.ids = [...new Set(saved.map((item) => item.offering.public_id))]
      this.merged = true
      this.persist()
    },
  },
})
