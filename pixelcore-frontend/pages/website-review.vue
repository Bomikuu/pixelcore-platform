<template>
  <div ref="host" class="min-h-screen">
    <StatePanel v-if="error" kind="error" title="Review unavailable" :message="error" />
    <p v-else class="p-6 text-sm text-muted-foreground">Opening the saved website preview…</p>
  </div>
</template>
<script setup>
definePageMeta({ layout: false })
useHead({ title: 'Website review', meta: [{ name: 'robots', content: 'noindex,nofollow' }, { name: 'referrer', content: 'no-referrer' }] })
const { apiFetch } = useApiClient()
const host = ref(null)
const error = ref('')
let viewer
let disposed = false
onMounted(async () => {
  try {
    const { mountReview } = await import('@sitebuilder/review')
    if (!disposed) viewer = mountReview(host.value, { baseUrl: 'website-builder/', request: apiFetch })
  } catch (failure) { if (!disposed) error.value = failure.message || 'This review could not be opened.' }
})
onBeforeUnmount(() => { disposed = true; viewer?.destroy() })
</script>
