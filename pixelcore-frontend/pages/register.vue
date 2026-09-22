<template>
  <section class="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl lg:grid-cols-[0.82fr_1.18fr]">
    <aside class="relative hidden overflow-hidden border-r bg-[var(--brand-secondary)] p-10 text-white lg:flex lg:flex-col lg:justify-between">
      <div class="absolute inset-x-0 top-24 h-px bg-white/15" />
      <div class="absolute -right-28 top-28 h-80 w-80 rounded-full border border-white/10" />
      <p class="max-w-sm text-sm leading-6 text-white/70">One account can own, operate, or join multiple businesses without locking any of them into one industry.</p>
      <div class="relative max-w-md">
        <h2 class="display-face text-5xl font-semibold leading-[1.02]">Create the account. Shape the business next.</h2>
        <p class="mt-6 max-w-sm leading-7 text-white/70">Verify your identity first, then choose a restaurant, retail, service, hybrid, or general starting point.</p>
      </div>
    </aside>

    <div class="flex items-center px-4 py-12 sm:px-8 lg:px-14 lg:py-16">
      <div class="mx-auto w-full max-w-2xl">
        <h1 class="display-face text-4xl font-semibold tracking-[-0.025em] sm:text-5xl">Create your PixelCore account</h1>
        <p class="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">Your business, locations, and capabilities are configured after email verification.</p>

        <form class="mt-8 space-y-6" novalidate @submit.prevent="submit">
          <div class="grid gap-5 sm:grid-cols-2">
            <div><label class="field-label" for="first-name">First name</label><Input id="first-name" v-model.trim="form.first_name" autocomplete="given-name" required /></div>
            <div><label class="field-label" for="last-name">Last name</label><Input id="last-name" v-model.trim="form.last_name" autocomplete="family-name" required /></div>
            <div><label class="field-label" for="email">Email</label><Input id="email" v-model.trim="form.email" type="email" autocomplete="email" required /><p v-if="fieldError('email')" class="mt-1 text-xs text-destructive">{{ fieldError('email') }}</p></div>
            <div><label class="field-label" for="phone">Phone</label><Input id="phone" v-model.trim="form.phone" type="tel" autocomplete="tel" placeholder="+63 917 123 4567" required /><p v-if="fieldError('phone')" class="mt-1 text-xs text-destructive">{{ fieldError('phone') }}</p></div>
            <div class="sm:col-span-2"><label class="field-label" for="username">Username <span class="font-normal text-muted-foreground">(optional)</span></label><Input id="username" v-model.trim="form.username" autocomplete="username" /><p class="mt-1 text-xs text-muted-foreground">Sign in with this, your email, or your phone.</p></div>
            <div><label class="field-label" for="password">Password</label><Input id="password" v-model="form.password" type="password" autocomplete="new-password" required /></div>
            <div><label class="field-label" for="confirm-password">Confirm password</label><Input id="confirm-password" v-model="form.password_confirm" type="password" autocomplete="new-password" required /><p v-if="passwordMismatch" class="mt-1 text-xs text-destructive">Passwords do not match.</p></div>
          </div>

          <div v-if="form.password" class="border-y py-4" aria-live="polite">
            <div class="flex items-center justify-between gap-4 text-sm"><span class="font-semibold">Password strength</span><span>{{ strengthLabel }}</span></div>
            <div class="mt-2 h-1.5 overflow-hidden bg-muted"><div class="h-full bg-primary transition-[width]" :style="{ width: `${strengthPercent}%` }" /></div>
            <ul class="mt-3 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
              <li v-for="rule in passwordRules" :key="rule.label" class="flex items-center gap-2" :class="rule.met ? 'text-foreground' : ''"><Check v-if="rule.met" class="h-3.5 w-3.5 text-primary" aria-hidden="true" /><Circle v-else class="h-3.5 w-3.5" aria-hidden="true" />{{ rule.label }}</li>
            </ul>
          </div>

          <p v-if="error" role="alert" class="border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{{ error }}</p>
          <Button class="min-h-12 w-full" :disabled="auth.loading || !canSubmit" type="submit">{{ auth.loading ? 'Creating account…' : 'Create account' }}</Button>
        </form>

        <div class="my-6 flex items-center gap-3 text-xs text-muted-foreground"><span class="h-px flex-1 bg-border" /><span>or</span><span class="h-px flex-1 bg-border" /></div>
        <Button variant="outline" class="min-h-12 w-full" type="button" :disabled="auth.loading" @click="continueWithGoogle"><svg class="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M21.6 12.2c0-.7-.1-1.4-.2-2.1H12v4h5.4a4.6 4.6 0 0 1-2 3v2.6h3.3c1.9-1.8 2.9-4.4 2.9-7.5Z"/><path fill="#34A853" d="M12 22c2.7 0 5-.9 6.7-2.3l-3.3-2.6c-.9.6-2.1 1-3.4 1a5.9 5.9 0 0 1-5.5-4.1H3.1v2.7A10 10 0 0 0 12 22Z"/><path fill="#FBBC05" d="M6.5 14a6 6 0 0 1 0-3.9V7.4H3.1a10 10 0 0 0 0 9.3L6.5 14Z"/><path fill="#EA4335" d="M12 6c1.5 0 2.8.5 3.9 1.5l2.9-2.8A9.7 9.7 0 0 0 3.1 7.4l3.4 2.7A5.9 5.9 0 0 1 12 6Z"/></svg>Continue with Google</Button>
        <p class="mt-6 text-center text-sm text-muted-foreground">Already have an account? <NuxtLink class="font-bold text-foreground underline underline-offset-4" to="/login">Sign in</NuxtLink></p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Check, Circle } from 'lucide-vue-next'

const auth = useAuthStore()
const { requestCredential } = useGoogleIdentity()
const form = reactive({ first_name: '', last_name: '', email: '', phone: '', username: '', password: '', password_confirm: '' })
const error = ref('')
const details = ref({})
const passwordRules = computed(() => [
  { label: 'At least 10 characters', met: form.password.length >= 10 },
  { label: 'One uppercase letter', met: /[A-Z]/.test(form.password) },
  { label: 'One number', met: /\d/.test(form.password) },
  { label: 'One symbol', met: /[^A-Za-z0-9]/.test(form.password) },
])
const strength = computed(() => passwordRules.value.filter((rule) => rule.met).length)
const strengthPercent = computed(() => strength.value * 25)
const strengthLabel = computed(() => ['Too weak', 'Weak', 'Fair', 'Good', 'Strong'][strength.value])
const passwordMismatch = computed(() => Boolean(form.password_confirm && form.password !== form.password_confirm))
const canSubmit = computed(() => form.first_name && form.last_name && form.email && form.phone && strength.value >= 3 && !passwordMismatch.value)
const fieldError = (field) => details.value?.[field]?.[0] || details.value?.[field] || ''

async function submit() {
  error.value = ''
  details.value = {}
  try {
    await auth.register(form)
    sessionStorage.setItem('pixelcore_verification_email', form.email)
    await navigateTo(`/verify-email?email=${encodeURIComponent(form.email)}`)
  } catch (exception) {
    details.value = exception?.data?.error?.details || {}
    error.value = exception?.data?.error?.message || 'The account could not be created. Review the form and try again.'
  }
}

async function continueWithGoogle() {
  error.value = ''
  try {
    const credential = await requestCredential()
    const response = await auth.google(credential)
    await navigateTo(response.needs_onboarding ? '/onboarding' : '/workspace')
  } catch (exception) {
    error.value = exception?.data?.error?.message || exception?.message || 'Google sign-in could not be completed.'
  }
}
</script>
