<template>
  <section class="mx-auto flex min-h-[calc(100vh-4rem)] max-w-2xl items-center px-4 py-16 sm:px-6">
    <div class="w-full border-y py-10">
      <MailCheck class="h-9 w-9 text-primary" aria-hidden="true" />
      <h1 class="display-face mt-5 text-4xl font-semibold">Verify your email</h1>
      <p class="mt-3 leading-7 text-muted-foreground">Enter the six-digit code sent to <strong class="text-foreground">{{ email || 'your email' }}</strong>. It expires after 15 minutes.</p>
      <form class="mt-8 space-y-5" @submit.prevent="verify">
        <div><label class="field-label" for="verification-code">Verification code</label><Input id="verification-code" v-model.trim="code" class="text-center text-xl tracking-[0.35em]" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" required /></div>
        <p v-if="message" :class="messageTone" aria-live="polite" class="text-sm">{{ message }}</p>
        <Button class="min-h-12 w-full" :disabled="auth.loading || code.length !== 6">{{ auth.loading ? 'Verifying…' : 'Verify and continue' }}</Button>
      </form>
      <Button variant="ghost" class="mt-5 text-sm font-bold underline underline-offset-4 disabled:opacity-50" type="button" :disabled="resending" @click="resend">{{ resending ? 'Sending…' : 'Send a new code' }}</Button>
    </div>
  </section>
</template>

<script setup>
import { MailCheck } from 'lucide-vue-next'

const auth = useAuthStore()
const config = useRuntimeConfig()
const route = useRoute()
const email = ref(String(route.query.email || ''))
const code = ref('')
const message = ref('')
const messageTone = ref('text-destructive')
const resending = ref(false)

onMounted(() => { if (!email.value) email.value = sessionStorage.getItem('pixelcore_verification_email') || '' })
async function verify() {
  message.value = ''
  try {
    const response = await auth.verifyEmail({ email: email.value, code: code.value })
    sessionStorage.removeItem('pixelcore_verification_email')
    await navigateTo(response.needs_onboarding ? '/onboarding' : '/workspace')
  } catch (error) { message.value = error?.data?.error?.message || 'The code could not be verified.' }
}
async function resend() {
  resending.value = true
  try {
    const response = await $fetch('auth/resend-verification/', { baseURL: config.public.apiBaseUrl, method: 'POST', body: { email: email.value } })
    message.value = response.message
    messageTone.value = 'text-primary'
  } catch { message.value = 'A new code could not be sent.'; messageTone.value = 'text-destructive' } finally { resending.value = false }
}
</script>
