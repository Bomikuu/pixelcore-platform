<template>
  <section class="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl lg:grid-cols-2">
    <div class="flex items-center px-4 py-16 sm:px-8 lg:px-12">
      <div class="w-full max-w-md">
        <h1 class="display-face text-4xl font-semibold">Sign in to your workspace</h1>
        <p class="mt-3 text-sm leading-6 text-muted-foreground">Your access is scoped to the businesses and roles assigned to your account.</p>

        <form class="mt-8 space-y-5" @submit.prevent="submit">
          <label class="block space-y-2"><span class="text-sm font-semibold">Email, username, or phone</span><Input v-model.trim="form.identifier" required autocomplete="username" /></label>
          <label class="block space-y-2"><span class="text-sm font-semibold">Password</span><Input v-model="form.password" required type="password" autocomplete="current-password" class="w-full rounded-md border bg-background px-3 py-2.5" /></label>
          <p v-if="error" role="alert" class="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{{ error }}</p>
          <Button class="w-full rounded-md px-4 py-3 text-sm font-bold disabled:opacity-60" :disabled="auth.loading" type="submit">{{ auth.loading ? 'Signing in…' : 'Sign in' }}</Button>
        </form>
        <div class="my-6 flex items-center gap-3 text-xs text-muted-foreground"><span class="h-px flex-1 bg-border" /><span>or</span><span class="h-px flex-1 bg-border" /></div>
        <Button variant="outline" class="min-h-12 w-full" type="button" :disabled="auth.loading" @click="continueWithGoogle">Continue with Google</Button>
        <div class="mt-6 flex flex-wrap justify-between gap-3 text-sm text-muted-foreground"><NuxtLink to="/forgot-password" class="font-bold text-foreground underline underline-offset-4">Forgot password?</NuxtLink><span>New to PixelCore? <NuxtLink to="/register" class="font-bold text-foreground underline underline-offset-4">Create an account</NuxtLink></span></div>
      </div>
    </div>
    <div class="hidden border-l bg-secondary/40 p-12 lg:flex lg:items-end">
      <div class="max-w-lg"><h2 class="display-face text-3xl font-semibold">One active business context.</h2><p class="mt-4 leading-7 text-muted-foreground">Move between Site, Sell, Schedule, and Operate without losing the identity, role, location, or currency that scopes the work.</p></div>
    </div>
  </section>
</template>

<script setup>
import { accountHome } from '@/utils/accountHome'

const auth = useAuthStore()
const { requestCredential } = useGoogleIdentity()
const route = useRoute()
const form = reactive({ identifier: '', password: '' })
const error = ref('')

async function submit() {
  error.value = ''
  try {
    const response = await auth.login(form)
    const requested = String(route.query.next || '')
    const fallback = accountHome(auth.user)
    await navigateTo(requested.startsWith('/') && !requested.startsWith('//') ? requested : fallback)
  } catch (exception) {
    error.value = exception?.data?.error?.message || 'The account details are incorrect.'
  }
}

async function continueWithGoogle() {
  error.value = ''
  try {
    const response = await auth.google(await requestCredential())
    const requested = String(route.query.next || '')
    const fallback = accountHome(auth.user)
    await navigateTo(requested.startsWith('/') && !requested.startsWith('//') ? requested : fallback)
  } catch (exception) {
    error.value = exception?.data?.error?.message || exception?.message || 'Google sign-in could not be completed.'
  }
}
</script>
