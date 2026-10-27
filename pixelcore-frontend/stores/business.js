import { defineStore } from "pinia";

export const useBusinessStore = defineStore("business", {
  state: () => ({
    businesses: [],
    activeBusiness: null,
    loading: false,
    error: null,
  }),
  actions: {
    async loadBusinesses() {
      const { apiFetch } = useApiClient();
      this.loading = true;
      this.error = null;
      try {
        const response = await apiFetch("businesses/");
        this.businesses = response.results || [];
        const selectedId = useCookie("pixelcore_business_id").value;
        const selected = this.businesses.find(
          (business) => business.public_id === selectedId,
        );
        this.setActiveBusiness(selected || this.businesses[0] || null);
      } catch (error) {
        this.error = error;
        throw error;
      } finally {
        this.loading = false;
      }
    },
    setActiveBusiness(business) {
      this.activeBusiness = business;
      useCookie("pixelcore_business_id", { sameSite: "lax" }).value =
        business?.public_id || null;
    },
    async updateIdentity(payload) {
      const { apiFetch } = useApiClient();
      const updated = await apiFetch(
        `businesses/${this.activeBusiness.public_id}/identity/`,
        {
          method: "PATCH",
          body: payload,
        },
      );
      const index = this.businesses.findIndex(
        (business) => business.public_id === updated.public_id,
      );
      if (index !== -1) this.businesses[index] = updated;
      this.setActiveBusiness(updated);
      return updated;
    },
  },
});
