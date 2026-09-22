<template>
  <section class="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-16">
    <div class="grid gap-10 lg:grid-cols-[0.72fr_1.28fr]">
      <div class="lg:sticky lg:top-24 lg:self-start">
        <p class="text-sm font-semibold text-primary">Account verified</p>
        <h1 class="display-face mt-3 text-4xl font-semibold tracking-[-0.025em] sm:text-5xl">Give PixelCore its business context.</h1>
        <p class="mt-5 max-w-md leading-7 text-muted-foreground">A preset changes starter language and templates—not what your business is allowed to do.</p>
        <ol class="mt-8 space-y-4 border-t pt-5 text-sm">
          <li class="flex gap-3"><span class="font-bold text-primary">1</span><span>Name the business and its first location.</span></li>
          <li class="flex gap-3"><span class="font-bold text-primary">2</span><span>Choose the closest starting preset.</span></li>
          <li class="flex gap-3"><span class="font-bold text-primary">3</span><span>Enable the capabilities needed now.</span></li>
        </ol>
      </div>

      <form class="space-y-9 border-t pt-8" @submit.prevent="submit">
        <fieldset class="space-y-5"><legend class="display-face text-2xl font-semibold">Business identity</legend><div class="grid gap-5 sm:grid-cols-2"><div class="sm:col-span-2"><label class="field-label" for="business-name">Business name</label><Input id="business-name" v-model.trim="form.display_name" autocomplete="organization" required /></div><div><label class="field-label" for="country">Country</label><NativeSelect id="country" v-model="form.country"><option value="PH">Philippines</option><option value="SG">Singapore</option><option value="US">United States</option><option value="CA">Canada</option><option value="AU">Australia</option></NativeSelect></div><div><label class="field-label" for="location-name">First location</label><Input id="location-name" v-model.trim="form.location_name" required /></div></div></fieldset>

        <fieldset><legend class="display-face text-2xl font-semibold">Starting preset</legend><p class="mt-2 text-sm text-muted-foreground">You can use every capability regardless of this choice.</p><div class="mt-5 divide-y border-y"><label v-for="preset in presets" :key="preset.value" class="flex cursor-pointer items-start gap-4 py-4"><NativeRadio v-model="form.industry_preset" class="mt-1 h-4 w-4" :value="preset.value" /><span><strong class="block">{{ preset.label }}</strong><span class="mt-1 block text-sm leading-6 text-muted-foreground">{{ preset.description }}</span></span></label></div></fieldset>

        <fieldset><legend class="display-face text-2xl font-semibold">Capabilities</legend><div class="mt-5 divide-y border-y"><label v-for="capability in capabilities" :key="capability.value" class="flex cursor-pointer items-start justify-between gap-5 py-4"><span><strong class="block">{{ capability.label }}</strong><span class="mt-1 block text-sm text-muted-foreground">{{ capability.description }}</span></span><NativeCheckbox v-model="form.enabled_modules" class="mt-1 h-4 w-4" :value="capability.value" /></label></div></fieldset>

        <p v-if="error" role="alert" class="border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{{ error }}</p>
        <div class="flex flex-col-reverse gap-3 border-t pt-6 sm:flex-row sm:items-center sm:justify-between"><p class="text-xs text-muted-foreground">The first account becomes the business owner.</p><Button class="min-h-12 px-6" :disabled="saving">{{ saving ? 'Creating workspace…' : 'Create business workspace' }}</Button></div>
      </form>
    </div>
  </section>
</template>

<script setup>
const { apiFetch } = useApiClient()
const auth = useAuthStore()
const business = useBusinessStore()
const saving = ref(false)
const error = ref('')
const form = reactive({ display_name: '', country: 'PH', location_name: 'Main location', industry_preset: 'general', enabled_modules: ['site', 'sell', 'schedule', 'operate'] })
const presets = [
  { value: 'general', label: 'General business', description: 'Neutral vocabulary and a blank operational starting point.' },
  { value: 'restaurant', label: 'Restaurant', description: 'Menu, table reservation, poster menu, counter, and attendance starters.' },
  { value: 'retail', label: 'Retail', description: 'Product catalog, inventory, POS, promotion, and pickup starters.' },
  { value: 'services', label: 'Services', description: 'Service catalog, staff, availability, resources, and booking starters.' },
  { value: 'hybrid', label: 'Hybrid', description: 'Products and services operating together from one catalog.' },
]
const capabilities = [
  { value: 'site', label: 'Site', description: 'Pages, media, displays, and domains.' },
  { value: 'sell', label: 'Sell', description: 'Catalog, customers, POS, orders, and payments.' },
  { value: 'schedule', label: 'Schedule', description: 'Calendar, bookings, staff availability, and resources.' },
  { value: 'operate', label: 'Operate', description: 'Inventory, suppliers, documents, reports, and workforce.' },
]
async function submit() {
  saving.value = true; error.value = ''
  try {
    await apiFetch('businesses/onboarding/', { method: 'POST', body: form })
    await auth.loadUser(); await business.loadBusinesses(); await navigateTo('/workspace')
  } catch (exception) { error.value = exception?.data?.error?.message || 'The business workspace could not be created.' } finally { saving.value = false }
}
</script>
