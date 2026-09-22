<template><StorefrontFrame v-if="identity" :identity="identity" :navigation="navigation" :base="base"><StatePanel kind="loading" title="Returning to your order" message="Opening the protected confirmation page." /></StorefrontFrame></template>
<script setup>
definePageMeta({ layout: 'storefront' })
const route = useRoute()
const { identity, navigation, siteBase: base } = useStorefrontContext(route.params.slug)
onMounted(() => { const orderId = localStorage.getItem(`pixelcore-pending-order:${route.params.slug}`); navigateTo(orderId ? `${base}/order/${orderId}` : `${base}/cart`, { replace: true }) })
</script>
