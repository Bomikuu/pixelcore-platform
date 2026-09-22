<template><StatePanel v-if="pending" kind="loading" title="Loading site" message="Resolving the published page for this domain." /><StatePanel v-else-if="error || !manifest" kind="error" title="Page not found" message="This path is not published for the current domain." /><StorefrontPage v-else :manifest="manifest" :offerings="offerings || []" base="" /></template>

<script setup>
definePageMeta({ layout: 'storefront' })
const route = useRoute()
const config = useRuntimeConfig()
const requestUrl = useRequestURL()
const hostname = requestUrl.hostname.toLowerCase()
const isCustomHost = !['localhost', '127.0.0.1', config.public.platformDomain].includes(hostname) && !hostname.endsWith(`.${config.public.platformDomain}`)
if (!isCustomHost) throw createError({ statusCode: 404, statusMessage: 'Page not found' })
const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
const pagePath = Array.isArray(route.params.path) ? route.params.path.join('/') : route.params.path || ''
const { data: manifest, pending, error } = useAsyncData(`custom-domain:${hostname}:${pagePath}`, () => $fetch('public/site/resolve/', { baseURL, query: { host: hostname, path: pagePath } }))
const { data: offerings } = useAsyncData(`custom-domain-catalog:${hostname}`, () => manifest.value ? $fetch(`public/${manifest.value.identity.slug}/catalog/`, { baseURL }) : [])
useHead(() => manifest.value ? { title: manifest.value.seo.title, meta: [{ name: 'description', content: manifest.value.seo.description }, { name: 'robots', content: manifest.value.seo.robots }, { property: 'og:title', content: manifest.value.seo.title }, { property: 'og:description', content: manifest.value.seo.description }], link: [{ rel: 'canonical', href: manifest.value.seo.canonical }], script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(manifest.value.seo.json_ld).replaceAll('<', '\\u003c') }] } : {})
</script>
