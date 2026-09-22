import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', {
  state: () => ({ slug: '', cart: null, token: '', loading: false, error: '', drawerOpen: false }),
  getters: {
    itemCount: (state) => (state.cart?.items || []).reduce((total, item) => total + Number(item.quantity || 0), 0),
  },
  actions: {
    hydrate(slug) {
      if (!import.meta.client) return
      this.slug = slug
      try {
        const saved = JSON.parse(localStorage.getItem(`pixelcore-cart:${slug}`) || '{}')
        this.cart = saved.cart || null
        this.token = saved.token || ''
      } catch { this.cart = null; this.token = '' }
    },
    persist() {
      if (import.meta.client && this.slug) localStorage.setItem(`pixelcore-cart:${this.slug}`, JSON.stringify({ cart: this.cart, token: this.token }))
    },
    async ensure(slug) {
      if (this.slug !== slug) this.hydrate(slug)
      if (this.cart?.status === 'open' && this.token) return this.cart
      const config = useRuntimeConfig()
      const response = await $fetch(`public/${slug}/carts/`, { baseURL: config.public.apiBaseUrl, method: 'POST' })
      this.slug = slug; this.token = response.cart_token; delete response.cart_token; this.cart = response; this.persist(); return this.cart
    },
    async load(slug) {
      this.loading = true; this.error = ''
      try { await this.ensure(slug); const config = useRuntimeConfig(); this.cart = await $fetch(`public/${slug}/carts/${this.cart.public_id}/`, { baseURL: config.public.apiBaseUrl, headers: { 'X-Cart-Token': this.token } }); this.persist() } catch (error) { this.error = error?.data?.error?.message || 'Cart could not be loaded.' } finally { this.loading = false }
    },
    async add(slug, offeringPublicId, variantPublicId = null, quantity = 1, optionPublicIds = []) {
      await this.ensure(slug); const config = useRuntimeConfig(); this.cart = await $fetch(`public/${slug}/carts/${this.cart.public_id}/items/`, { baseURL: config.public.apiBaseUrl, method: 'POST', headers: { 'X-Cart-Token': this.token }, body: { offering_public_id: offeringPublicId, variant_public_id: variantPublicId, quantity, option_public_ids: optionPublicIds } }); this.persist()
    },
    async remove(itemId) {
      const config = useRuntimeConfig(); await $fetch(`public/${this.slug}/carts/${this.cart.public_id}/items/${itemId}/`, { baseURL: config.public.apiBaseUrl, method: 'DELETE', headers: { 'X-Cart-Token': this.token } }); await this.load(this.slug)
    },
    async updateItem(itemId, updates) {
      const config = useRuntimeConfig()
      this.cart = await $fetch(`public/${this.slug}/carts/${this.cart.public_id}/items/${itemId}/`, { baseURL: config.public.apiBaseUrl, method: 'PATCH', headers: { 'X-Cart-Token': this.token }, body: updates })
      this.persist()
    },
    async applyDiscount(discountCode) {
      const config = useRuntimeConfig()
      this.cart = await $fetch(`public/${this.slug}/carts/${this.cart.public_id}/`, { baseURL: config.public.apiBaseUrl, method: 'PATCH', headers: { 'X-Cart-Token': this.token }, body: { discount_code: discountCode } })
      this.persist()
    },
    async checkout(payload) {
      const config = useRuntimeConfig(); const response = await $fetch(`public/${this.slug}/carts/${this.cart.public_id}/checkout/`, { baseURL: config.public.apiBaseUrl, method: 'POST', headers: { 'X-Cart-Token': this.token, 'Idempotency-Key': crypto.randomUUID() }, body: payload }); this.cart.status = 'converted'; this.persist(); return response
    },
  },
})
