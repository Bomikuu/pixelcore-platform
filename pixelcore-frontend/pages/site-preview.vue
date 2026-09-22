<template><StatePanel v-if="pending" kind="loading" title="Preparing preview" message="Opening the signed draft revision." /><StatePanel v-else-if="error" kind="error" title="Preview unavailable" message="This preview link is invalid or has expired." /><StorefrontPage v-else-if="manifest" :manifest="manifest" :offerings="offerings || []" base="" /></template>

<script setup>
definePageMeta({ layout: 'storefront' })
const route = useRoute()
const config = useRuntimeConfig()
const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const { data: manifest, pending, error } = useAsyncData('site-preview', () => $fetch('public/site-preview/', { baseURL, query: { token: route.query.token } }))
const { data: offerings } = useAsyncData('site-preview-catalog', () => manifest.value ? $fetch(`public/${manifest.value.identity.slug}/catalog/`, { baseURL }) : [])
useHead({ title: 'Private page preview', meta: [{ name: 'robots', content: 'noindex,nofollow' }] })
</script>
