<template>
  <main class="mx-auto max-w-lg p-8">
    <h1 class="text-xl font-semibold">Connect PixelCore Studio</h1>
    <p class="mt-3 text-sm text-muted-foreground">{{ message }}</p>
    <ButtonLink v-if="signedOut" to="/login" class="mt-4" target="_blank">Sign in to PixelCore</ButtonLink>
  </main>
</template>

<script setup>
import { ButtonLink } from '@/components/ui/button-link'
const message = ref('Checking your PixelCore session…')
const signedOut = ref(false)
const route = useRoute()
const config = useRuntimeConfig()
let cleanup = () => {}
onMounted(async () => {
  const audience = String(route.query.audience || '')
  const state = String(route.query.state || '')
  const trusted = config.public.studioOrigin || 'http://localhost:4173'
  const peer = window.opener || window.parent
  if (peer === window || audience !== trusted || !/^[A-Za-z0-9_-]{32,128}$/.test(state)) {
    message.value = 'Open this connection from your trusted Studio workspace.'
    return
  }
  const send = (value) => peer.postMessage({ type: 'studio:connect', version: 1, state, ...value }, trusted)
  const auth = useAuthStore()
  try {
    await auth.restoreSession()
    if (!auth.isAuthenticated) {
      signedOut.value = true
      message.value = 'Sign in to PixelCore, then choose Connect in Studio.'
      send({ status: 'signed-out' })
      return
    }
    const businesses = (auth.user.businesses || []).filter(b => ['owner', 'admin', 'manager'].includes(b.role)).slice(0, 100)
    let busy = false
    async function choose(id) {
      if (busy || !businesses.some(b => b.public_id === id)) return
      busy = true
      try {
        const { apiFetch } = useApiClient()
        const result = await apiFetch(`businesses/${id}/studio/handoffs/`, { method: 'POST', body: { state, audience } })
        send({ status: 'connected', code: result.code })
        message.value = 'Your business workspace is connected.'
      } catch { send({ status: 'unavailable' }); message.value = 'Connection unavailable. Return to Studio to retry.' }
    }
    const receive = (event) => {
      if (event.origin === trusted && event.source === peer && event.data?.type === 'studio:select' && event.data.state === state) choose(event.data.businessId)
    }
    window.addEventListener('message', receive)
    cleanup = () => window.removeEventListener('message', receive)
    if (businesses.length === 1) await choose(businesses[0].public_id)
    else send({ status: 'choices', businesses: businesses.map(b => ({ id: b.public_id, name: b.display_name })) })
  } catch { send({ status: 'unavailable' }); message.value = 'PixelCore could not restore this session.' }
})
onBeforeUnmount(() => cleanup())
</script>
