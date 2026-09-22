<template>
  <section class="workspace-page space-y-5">
    <header class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between"><div><NuxtLink to="/workspace/sell/promotions" class="inline-flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground"><ArrowLeft class="h-4 w-4" /> Back to promotions</NuxtLink><h1 class="mt-4 text-3xl font-extrabold tracking-[-.025em]">{{ promotionId ? 'Edit promotion' : 'Create a promotion' }}</h1><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Define the customer value, schedule, activation method, and exact catalog scope in one campaign workspace.</p></div><Button class="self-start xl:self-auto" type="button" :disabled="saving || loading || Boolean(loadError)" @click="save">{{ saving ? 'Saving…' : promotionId ? 'Save changes' : 'Create promotion' }}</Button></header>

    <StatePanel v-if="loading" kind="loading" title="Loading promotion" />
    <StatePanel v-else-if="loadError" kind="error" title="Promotion unavailable" :message="loadError"><Button type="button" variant="outline" @click="load">Retry</Button></StatePanel>
    <form v-else class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]" @submit.prevent="save">
      <div class="space-y-6">
        <section class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="offer-heading"><h2 id="offer-heading" class="text-base font-extrabold">Offer details</h2><p class="mt-1 text-sm text-muted-foreground">Name the campaign and define what the customer receives.</p><div class="mt-6 grid gap-5 sm:grid-cols-2"><label class="sm:col-span-2"><span class="field-label">Promotion name</span><Input v-model.trim="form.name" maxlength="120" required placeholder="For example, September welcome offer" /></label><label><span class="field-label">Discount type</span><NativeSelect v-model="form.value_type"><option value="percentage">Percentage off</option><option value="fixed">Fixed amount off</option></NativeSelect></label><label><span class="field-label">{{ form.value_type === 'percentage' ? 'Percentage' : `Amount (${business.activeBusiness?.currency})` }}</span><div class="relative"><Input v-model="form.value" type="number" min="0.01" :max="form.value_type === 'percentage' ? 100 : undefined" step="0.01" required /><span v-if="form.value_type === 'percentage'" class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm font-bold text-muted-foreground">%</span></div></label></div></section>

        <p class="text-xs text-muted-foreground">Schedule times use your device timezone ({{ deviceTimezone }}).</p>
        <section class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="activation-heading"><h2 id="activation-heading" class="text-base font-extrabold">Activation & schedule</h2><p class="mt-1 text-sm text-muted-foreground">Choose whether the offer is automatic or entered as a checkout code.</p><div class="mt-6 grid gap-5 sm:grid-cols-2"><fieldset class="sm:col-span-2"><legend class="field-label">How customers receive it</legend><div class="grid gap-3 sm:grid-cols-2"><label class="flex cursor-pointer gap-3 rounded-xl border p-4" :class="form.is_automatic ? 'border-primary bg-secondary/45' : ''"><NativeRadio v-model="form.is_automatic" class="mt-1" :value="true" /><span><strong class="block text-sm">Automatic discount</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">Applied when eligible items enter checkout.</span></span></label><label class="flex cursor-pointer gap-3 rounded-xl border p-4" :class="!form.is_automatic ? 'border-primary bg-secondary/45' : ''"><NativeRadio v-model="form.is_automatic" class="mt-1" :value="false" /><span><strong class="block text-sm">Promotion code</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">Customers enter a memorable code.</span></span></label></div></fieldset><label v-if="!form.is_automatic" class="sm:col-span-2"><span class="field-label">Code</span><Input v-model.trim="form.code" class="uppercase" maxlength="40" required placeholder="WELCOME10" /></label><label><span class="field-label">Starts</span><Input v-model="form.starts_at" type="datetime-local" /></label><label><span class="field-label">Ends</span><Input v-model="form.ends_at" type="datetime-local" /></label></div></section>

        <PromotionScope v-model:scope="scope" :form="form" :business-id="business.activeBusiness.public_id" />
      </div>

      <aside class="space-y-6 xl:sticky xl:top-24 xl:self-start"><section class="rounded-xl border bg-card p-5" aria-labelledby="preview-heading"><h2 id="preview-heading" class="text-base font-extrabold">Customer preview</h2><div class="mt-5 rounded-xl bg-[var(--brand-secondary)] p-5 text-white"><Megaphone class="h-5 w-5 text-[var(--brand-accent)]" /><p class="mt-5 text-sm font-semibold text-white/90">{{ form.name || 'Your promotion' }}</p><p class="mt-2 text-3xl font-extrabold">{{ valuePreview }}</p><p class="mt-3 text-xs leading-5 text-white/90">{{ form.is_automatic ? 'Applied automatically at checkout' : form.code ? `Use code ${form.code.toUpperCase()}` : 'Add a promotion code' }}</p></div></section><label class="flex items-start gap-3 rounded-xl border bg-card p-5"><NativeCheckbox v-model="form.is_active" class="mt-1" /><span><strong class="block text-sm">Active promotion</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">An active campaign follows the configured schedule and scope.</span></span></label><p class="text-sm leading-6 text-muted-foreground">{{ scopeSummary }}</p><p v-if="error" class="rounded-xl border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive" role="alert">{{ error }}</p><Button class="w-full" type="submit" :disabled="saving">{{ saving ? 'Saving…' : promotionId ? 'Save changes' : 'Create promotion' }}</Button></aside>
    </form>
  </section>
</template>

<script setup>
import { ArrowLeft, Megaphone } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'
import PromotionScope from './PromotionScope.vue'
const props = defineProps({ promotionId: { type: String, default: '' } })
const router = useRouter(), business = useBusinessStore()
const { apiFetch } = useApiClient()
const saving = ref(false), loading = ref(true), error = ref(''), loadError = ref(''), scope = ref('catalog')
const form = reactive({ name: '', code: '', value_type: 'percentage', value: 10, is_automatic: false, starts_at: '', ends_at: '', offering_ids: [], category_ids: [], is_active: true })
const deviceTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
const valuePreview = computed(() => form.value_type === 'percentage' ? `${Number(form.value || 0)}% off` : `${money(form.value)} off`)
const scopeSummary = computed(() => scope.value === 'catalog' ? 'Applies to the entire catalog.' : scope.value === 'categories' ? `Applies to ${form.category_ids.length} selected categories.` : `Applies to ${form.offering_ids.length} selected products.`)
function localTime(value) {
  if (!value) return ''
  const date = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}
async function load() {
  loading.value = true; loadError.value = ''
  try {
    if (!business.activeBusiness) await business.loadBusinesses()
    if (props.promotionId) {
      const data = await apiFetch(`businesses/${business.activeBusiness.public_id}/discounts/${props.promotionId}/`)
      for (const key of Object.keys(form)) if (data[key] !== undefined) form[key] = data[key]
      form.starts_at = localTime(data.starts_at); form.ends_at = localTime(data.ends_at)
      scope.value = data.category_ids?.length ? 'categories' : data.offering_ids?.length ? 'products' : 'catalog'
    }
  } catch (err) { loadError.value = err?.data?.error?.message || 'The promotion could not be loaded.' }
  finally { loading.value = false }
}
onMounted(load)
async function save() {
  if (saving.value || loading.value || loadError.value) return
  error.value = ''
  if (!form.name || !Number.isFinite(Number(form.value)) || Number(form.value) <= 0 || (form.value_type === 'percentage' && Number(form.value) > 100)) error.value = 'Add a name and a valid discount value (1–100% for percentages).'
  else if (!form.is_automatic && !form.code.trim()) error.value = 'Add a promotion code.'
  else if (form.starts_at && form.ends_at && new Date(form.ends_at) <= new Date(form.starts_at)) error.value = 'The end must be after the start.'
  else if (scope.value === 'categories' && !form.category_ids.length) error.value = 'Select at least one category.'
  else if (scope.value === 'products' && !form.offering_ids.length) error.value = 'Select at least one product.'
  if (error.value) { toast({ title: 'Review promotion', description: error.value, variant: 'destructive' }); return }
  saving.value = true
  try {
    const payload = { ...form, code: form.is_automatic ? '' : form.code.trim().toUpperCase(), starts_at: form.starts_at ? new Date(form.starts_at).toISOString() : null, ends_at: form.ends_at ? new Date(form.ends_at).toISOString() : null, offering_ids: scope.value === 'products' ? form.offering_ids : [], category_ids: scope.value === 'categories' ? form.category_ids : [] }
    const data = await apiFetch(`businesses/${business.activeBusiness.public_id}/discounts/${props.promotionId ? props.promotionId + '/' : ''}`, { method: props.promotionId ? 'PATCH' : 'POST', body: payload })
    toast({ title: props.promotionId ? 'Promotion updated' : 'Promotion created', description: form.name })
    if (!props.promotionId) await router.replace(`/workspace/sell/promotions/${data.public_id}`)
  } catch (err) {
    const details = err?.data?.error?.details
    error.value = details && typeof details === 'object' ? Object.values(details).flat().filter(value => typeof value === 'string').join(' ') : ''
    error.value ||= err?.data?.error?.message || 'The promotion could not be saved.'
    toast({ title: 'Promotion not saved', description: error.value, variant: 'destructive' })
  } finally { saving.value = false }
}
function money(value) { return new Intl.NumberFormat('en-PH', { style: 'currency', currency: business.activeBusiness?.currency || 'PHP' }).format(Number(value || 0)) }
</script>
