<template>
  <section class="mx-auto flex min-h-[calc(100vh-4rem)] max-w-xl items-center px-4 py-16 sm:px-6"><div class="w-full border-y py-10"><KeyRound class="h-9 w-9 text-primary" aria-hidden="true" /><h1 class="display-face mt-5 text-4xl font-semibold">Find your account</h1><p class="mt-3 leading-7 text-muted-foreground">Use the email, username, or phone connected to your account.</p><form class="mt-8 space-y-5" @submit.prevent="submit"><div><label class="field-label" for="identifier">Account identifier</label><Input id="identifier" v-model.trim="identifier" autocomplete="username" required /></div><p v-if="message" class="text-sm" :class="sent ? 'text-primary' : 'text-destructive'" aria-live="polite">{{ message }}</p><Button class="min-h-12 w-full" :disabled="loading">{{ loading ? 'Sending…' : 'Send reset code' }}</Button></form><ButtonLink variant="outline"  v-if="sent" :to="`/reset-password?identifier=${encodeURIComponent(identifier)}`" class="mt-5 w-full">Enter reset code</ButtonLink></div></section>
</template>
<script setup>
import { KeyRound } from 'lucide-vue-next'
const auth = useAuthStore(); const identifier = ref(''); const message = ref(''); const loading = ref(false); const sent = ref(false)
async function submit() { loading.value = true; message.value = ''; try { const response = await auth.forgotPassword(identifier.value); message.value = response.message; sent.value = true } catch (error) { message.value = error?.data?.error?.message || 'The reset request could not be completed.' } finally { loading.value = false } }
</script>
