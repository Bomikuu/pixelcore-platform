<template>
  <section class="login-page grid min-h-dvh bg-background text-foreground lg:grid-cols-2">
    <div class="flex min-w-0 items-center px-6 py-8 sm:px-10 sm:py-12 lg:px-12 xl:px-16">
      <div class="mx-auto w-full max-w-[496px]">
        <NuxtLink to="/" class="inline-flex rounded-md" aria-label="PixelCore home">
          <PixelCoreMark />
        </NuxtLink>

        <header class="mt-12 lg:mt-16">
          <h1 class="max-w-[14ch] text-4xl font-extrabold leading-[1.12] tracking-[-0.03em] sm:text-5xl">
            Sign in to your workspace
          </h1>
          <p class="mt-4 max-w-[44ch] text-sm leading-7 text-muted-foreground sm:text-base">
            Your access is scoped to the businesses and roles assigned to your account.
          </p>
        </header>

        <form class="mt-7 space-y-5" novalidate :aria-busy="busy" @submit.prevent="submit">
          <div>
            <Label for="login-identifier" class="text-sm font-semibold">Email, username, or phone</Label>
            <div class="relative mt-2">
              <Mail class="pointer-events-none absolute left-4 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-foreground" aria-hidden="true" />
              <Input
                id="login-identifier"
                v-model.trim="form.identifier"
                class="h-12 rounded-lg bg-card pl-11 text-sm shadow-none"
                placeholder="you@example.com"
                required
                autocomplete="username"
                autocapitalize="none"
                :spellcheck="false"
                :disabled="busy"
                :aria-invalid="!!fieldErrors.identifier"
                :aria-describedby="fieldErrors.identifier ? 'login-identifier-error' : error ? 'login-error' : undefined"
                @input="clearError('identifier')"
              />
            </div>
            <p v-if="fieldErrors.identifier" id="login-identifier-error" class="mt-2 text-sm text-destructive">
              {{ fieldErrors.identifier }}
            </p>
          </div>

          <div>
            <Label for="login-password" class="text-sm font-semibold">Password</Label>
            <div class="relative mt-2">
              <LockKeyhole class="pointer-events-none absolute left-4 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-foreground" aria-hidden="true" />
              <Input
                id="login-password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                class="h-12 rounded-lg bg-card pl-11 pr-12 text-sm shadow-none"
                placeholder="Enter your password"
                required
                autocomplete="current-password"
                :disabled="busy"
                :aria-invalid="!!fieldErrors.password"
                :aria-describedby="fieldErrors.password ? 'login-password-error' : error ? 'login-error' : undefined"
                @input="clearError('password')"
              />
              <Button
                variant="ghost"
                size="icon"
                type="button"
                class="absolute right-1 top-1 h-10 w-10 text-foreground hover:bg-secondary"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                :aria-pressed="showPassword"
                :disabled="busy"
                @click="showPassword = !showPassword"
              >
                <EyeOff v-if="showPassword" class="h-4 w-4" aria-hidden="true" />
                <Eye v-else class="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
            <p v-if="fieldErrors.password" id="login-password-error" class="mt-2 text-sm text-destructive">
              {{ fieldErrors.password }}
            </p>
          </div>

          <div v-if="error" id="login-error" role="alert" class="flex items-start gap-3 rounded-lg bg-destructive/10 p-3 text-sm leading-6 text-destructive">
            <CircleAlert class="mt-1 h-4 w-4 shrink-0" aria-hidden="true" />
            <p>{{ error }}</p>
          </div>
          <Button class="login-submit h-12 w-full gap-2 rounded-lg text-sm font-bold" :disabled="busy" type="submit">
            <LoaderCircle v-if="pendingAction === 'password'" class="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
            {{ pendingAction === 'password' ? 'Signing in…' : 'Sign in' }}
            <ArrowRight v-if="pendingAction !== 'password'" class="h-4 w-4" aria-hidden="true" />
          </Button>
        </form>

        <div class="my-6 flex items-center gap-4 text-xs text-muted-foreground" aria-hidden="true">
          <span class="h-px flex-1 bg-border" />
          <span>or</span>
          <span class="h-px flex-1 bg-border" />
        </div>
        <Button variant="outline" class="h-12 w-full gap-3 rounded-lg bg-card text-sm font-semibold" type="button" :disabled="busy" @click="continueWithGoogle">
          <LoaderCircle v-if="pendingAction === 'google'" class="h-5 w-5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
          <img v-else src="/images/brand/google.svg" alt="" width="20" height="20" />
          {{ pendingAction === 'google' ? 'Connecting to Google…' : 'Continue with Google' }}
        </Button>
        <div class="mt-6 flex flex-wrap items-center justify-between gap-x-5 gap-y-4 text-xs leading-6 text-muted-foreground sm:text-sm">
          <NuxtLink to="/forgot-password" class="font-semibold text-foreground underline underline-offset-4 hover:text-primary">Forgot password?</NuxtLink>
          <span>
            New to PixelCore?{{ ' ' }}
            <NuxtLink to="/register" class="ml-1 font-semibold text-foreground underline underline-offset-4 hover:text-primary">Create an account</NuxtLink>
          </span>
        </div>
      </div>
    </div>

    <aside class="login-story hidden min-w-0 flex-col overflow-hidden border-l border-border/40 lg:flex" aria-labelledby="login-story-title">
      <div class="login-art relative isolate min-h-[360px] flex-1 overflow-hidden" aria-label="Illustration of a business owner managing a shop, with sample activity">
        <div class="login-art-shapes pointer-events-none absolute inset-0 -z-20" aria-hidden="true" />
        <img
          src="/images/login/workspace-illustration.png"
          alt=""
          class="login-illustration pointer-events-none absolute inset-0 -z-10 h-full w-full object-cover object-center"
          decoding="async"
          fetchpriority="high"
        />
        <div class="login-activity login-sales" aria-hidden="true">
          <p class="text-xs font-semibold">Today's sales</p>
          <div class="mt-3 flex h-10 items-end gap-1.5">
            <span v-for="(height, index) in salesBars" :key="index" class="w-3 rounded-sm bg-primary/70" :style="{ height: `${height}%`, opacity: 1 - index * 0.07 }" />
          </div>
          <p class="mt-2 text-right text-sm font-bold">₱12,430</p>
        </div>
        <div class="login-activity login-orders flex items-center gap-3" aria-hidden="true">
          <ShoppingBag class="h-7 w-7 text-primary" />
          <div>
            <p class="text-xs font-semibold">Orders</p>
            <p class="mt-1 flex items-center gap-2 text-xl font-extrabold">28 <TrendingUp class="h-4 w-4 text-primary/60" /></p>
          </div>
        </div>
        <div class="login-activity login-inventory flex items-center gap-3" aria-hidden="true">
          <Package class="h-7 w-7 text-primary" />
          <div>
            <p class="text-xs font-semibold">Inventory</p>
            <p class="mt-2 flex items-center gap-2 text-xs text-muted-foreground">Low stock <CircleAlert class="h-3.5 w-3.5 text-destructive/70" /></p>
          </div>
        </div>
        <p class="absolute bottom-3 right-5 text-[11px] text-muted-foreground">Illustrative workspace · Sample data</p>
      </div>

      <div class="px-8 pb-10 pt-8 xl:px-14 xl:pb-14">
        <h2 id="login-story-title" class="text-2xl font-extrabold leading-tight tracking-[-0.02em] xl:text-3xl">
          One active business context.
        </h2>
        <p class="mt-3 max-w-[60ch] text-sm leading-7 text-muted-foreground xl:text-base">
          Move between Site, Sell, Schedule, and Operate without losing the identity, role, location, or currency that scopes the work.
        </p>
        <ul class="mt-8 grid grid-cols-2 gap-x-4 gap-y-5 xl:grid-cols-4" aria-label="Workspace capabilities">
          <li v-for="feature in features" :key="feature.title" class="flex items-start gap-3">
            <component :is="feature.icon" class="mt-0.5 h-6 w-6 shrink-0 text-foreground" aria-hidden="true" />
            <div class="min-w-0">
              <p class="text-sm font-semibold">{{ feature.title }}</p>
              <p class="mt-1 text-xs leading-5 text-muted-foreground">{{ feature.description }}</p>
            </div>
          </li>
        </ul>
      </div>
    </aside>
  </section>
</template>

<script setup>
import {
  ArrowRight,
  CalendarDays,
  ChartNoAxesCombined,
  CircleAlert,
  Eye,
  EyeOff,
  LoaderCircle,
  LockKeyhole,
  Mail,
  Package,
  ShoppingBag,
  ShoppingCart,
  TrendingUp,
} from 'lucide-vue-next'
import { accountHome } from '@/utils/accountHome'

definePageMeta({ layout: 'storefront' })

const auth = useAuthStore()
const { requestCredential } = useGoogleIdentity()
const route = useRoute()
const form = reactive({ identifier: '', password: '' })
const fieldErrors = reactive({ identifier: '', password: '' })
const error = ref('')
const showPassword = ref(false)
const pendingAction = ref('')
const busy = computed(() => auth.loading || !!pendingAction.value)
const salesBars = [32, 46, 62, 44, 58, 78, 100]
const features = [
  { title: 'Sell', description: 'Process orders', icon: ShoppingCart },
  { title: 'Schedule', description: 'Manage bookings', icon: CalendarDays },
  { title: 'Inventory', description: 'Track stock', icon: Package },
  { title: 'Operate', description: 'Get insights', icon: ChartNoAxesCombined },
]

function clearError(field) {
  fieldErrors[field] = ''
  error.value = ''
}

async function openWorkspace() {
  const requested = String(route.query.next || '')
  const fallback = accountHome(auth.user)
  await navigateTo(requested.startsWith('/') && !requested.startsWith('//') ? requested : fallback)
}

async function submit() {
  if (busy.value) return
  error.value = ''
  fieldErrors.identifier = form.identifier ? '' : 'Enter your email, username, or phone.'
  fieldErrors.password = form.password ? '' : 'Enter your password.'
  if (fieldErrors.identifier || fieldErrors.password) {
    await nextTick()
    document.getElementById(fieldErrors.identifier ? 'login-identifier' : 'login-password')?.focus()
    return
  }
  pendingAction.value = 'password'
  try {
    await auth.login(form)
    await openWorkspace()
  } catch (exception) {
    showPassword.value = false
    error.value = exception?.data?.error?.message || 'The account details are incorrect.'
  } finally {
    pendingAction.value = ''
  }
}

async function continueWithGoogle() {
  if (busy.value) return
  error.value = ''
  fieldErrors.identifier = ''
  fieldErrors.password = ''
  pendingAction.value = 'google'
  try {
    await auth.google(await requestCredential())
    await openWorkspace()
  } catch (exception) {
    error.value = exception?.data?.error?.message || exception?.message || 'Google sign-in could not be completed.'
  } finally {
    pendingAction.value = ''
  }
}
</script>

<style scoped>
.login-submit {
  background: hsl(var(--foreground));
  color: hsl(var(--primary-foreground));
}

.login-submit:hover:not(:disabled) {
  background: hsl(var(--primary));
}

.login-art-shapes::before,
.login-art-shapes::after {
  position: absolute;
  top: 12%;
  left: 8%;
  width: 22%;
  height: 35%;
  border-radius: 2.5rem;
  background: hsl(var(--primary) / 0.045);
  content: '';
}

.login-art-shapes::after {
  top: 3%;
  right: 5%;
  left: auto;
  width: 39%;
  height: 57%;
  background: hsl(var(--accent) / 0.045);
}

.login-activity {
  position: absolute;
  border-radius: 0.875rem;
  background: hsl(var(--card) / 0.97);
  padding: 1rem 1.125rem;
  box-shadow: 0 8px 24px -12px hsl(var(--foreground) / 0.2);
}

.login-sales {
  top: 36%;
  left: 10%;
}

.login-orders {
  top: 24%;
  right: 15%;
}

.login-inventory {
  top: 47%;
  right: 5%;
}
</style>
