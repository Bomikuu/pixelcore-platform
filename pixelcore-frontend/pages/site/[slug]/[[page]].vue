<template>
  <div>
    <StatePanel v-if="pending" kind="loading" title="Loading site" message="Preparing the latest published page." />
    <StatePanel v-else-if="error" kind="error" title="Page not found" message="This page is unavailable or has not been published." />
    <StorefrontPage v-else-if="manifest" :manifest="manifest" :offerings="offerings || []" :base="siteBase" />
  </div>
</template>

<script setup>
definePageMeta({ layout: 'storefront' })
const route = useRoute()
const pageSlug = computed(() => Array.isArray(route.params.page) ? route.params.page.join('/') : route.params.page || '')
const { manifest, pending, error } = usePublicSite(route.params.slug, pageSlug.value)
const config = useRuntimeConfig()
const requestUrl = useRequestURL()
const host = requestUrl.hostname.toLowerCase()
const customHost = !['localhost', '127.0.0.1', config.public.platformDomain].includes(host) && !host.endsWith(`.${config.public.platformDomain}`)
const siteBase = customHost ? '' : `/site/${route.params.slug}`
const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const { data: offerings } = useAsyncData(`catalog:${route.params.slug}`, () => $fetch(`public/${route.params.slug}/catalog/`, { baseURL }))
useHead(() => manifest.value ? { title: manifest.value.seo.title, meta: [{ name: 'description', content: manifest.value.seo.description }, { name: 'robots', content: manifest.value.seo.robots }, { property: 'og:title', content: manifest.value.seo.title }, { property: 'og:description', content: manifest.value.seo.description }], link: [{ rel: 'canonical', href: manifest.value.seo.canonical }], script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(manifest.value.seo.json_ld).replaceAll('<', '\\u003c') }] } : {})
</script>
