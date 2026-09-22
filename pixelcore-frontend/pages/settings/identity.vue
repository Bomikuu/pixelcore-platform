<template>
  <section class="workspace-page space-y-5">
    <PageHeader title="Appearance & branding" description="Control one reusable business identity across your storefront, workspace, displays, and customer-facing surfaces." />
    <StatePanel v-if="business.loading" kind="loading" title="Loading business identity" message="Retrieving the saved appearance and media references." />
    <StatePanel v-else-if="business.error" kind="error" title="Identity unavailable" message="PixelCore could not load this business. Refresh the page or choose another active business." />
    <BusinessIdentityForm v-else-if="business.activeBusiness" :business="business.activeBusiness" />
    <StatePanel v-else title="No active business" message="Create or select a business before configuring its appearance." />
  </section>
</template>

<script setup>
const business = useBusinessStore()
onMounted(async () => { if (!business.activeBusiness) await business.loadBusinesses() })
</script>
