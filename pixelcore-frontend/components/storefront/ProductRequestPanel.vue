<template>
  <section v-if="enabledModes.length" class="mt-7 border-y py-5" aria-label="Other ways to get this product">
    <p class="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Another way to make it yours</p>
    <div class="mt-3 divide-y">
      <div v-for="mode in enabledModes" :key="mode.key" class="py-4 first:pt-0 last:pb-0">
        <div class="flex items-start gap-3"><component :is="mode.icon" class="mt-0.5 h-5 w-5 shrink-0" /><div class="min-w-0 flex-1"><h2 class="font-semibold">{{ mode.label }}</h2><p class="mt-1 text-sm leading-6 text-muted-foreground">{{ mode.description }}</p><p v-if="options[`${mode.key}_terms`]" class="mt-2 whitespace-pre-line text-sm leading-6">{{ options[`${mode.key}_terms`] }}</p></div></div>
        <Button type="button" variant="outline" class="mt-3 w-full" :disabled="!variant || !options.locations?.length" @click="begin(mode.key)">{{ mode.label }}<ArrowUpRight class="ml-auto h-4 w-4" /></Button>
      </div>
    </div>
    <p v-if="!variant" class="mt-3 text-xs text-muted-foreground">Select a product option first.</p>
    <p v-else-if="!options.locations?.length" class="mt-3 text-xs text-muted-foreground">Contact the business to arrange collection. No location is currently available.</p>
    <Dialog :open="open" @update:open="value => { if (!submitting) open = value }">
      <DialogContent class="max-h-[90dvh] overflow-y-auto sm:max-w-xl" @interact-outside="submitting && $event.preventDefault()" @escape-key-down="submitting && $event.preventDefault()">
        <DialogHeader><div class="mb-2 grid h-11 w-11 place-items-center rounded-full bg-secondary"><component :is="kind === 'rental' ? CalendarRange : PackageCheck" class="h-5 w-5" /></div><DialogTitle>{{ result ? (kind === 'rental' ? 'Rental request received' : 'Your stock is reserved') : title }}</DialogTitle><DialogDescription>{{ product.name }} · {{ variant?.name }}. {{ kind === 'rental' ? 'Staff approval is required. No payment is taken here.' : `Stock is held for ${options.hold_hours} hours. No payment is taken here.` }}</DialogDescription></DialogHeader>
        <div v-if="result" class="space-y-5" role="status">
          <CheckCircle2 class="h-8 w-8 text-primary" />
          <p class="text-sm leading-6">{{ kind === 'rental' ? 'The business will review your dates and contact you using the details you provided. Price, deposit, and availability are not confirmed yet.' : 'Keep this reference and collect before the deadline. The business will confirm the final purchase price at checkout.' }}</p>
          <dl class="grid grid-cols-[auto_1fr] gap-x-5 gap-y-3 rounded-lg bg-muted p-4 text-sm"><dt class="text-muted-foreground">Reference</dt><dd class="break-all font-mono text-xs">{{ result.public_id }}</dd><dt class="text-muted-foreground">Collection</dt><dd>{{ result.location_name }}</dd><dt class="text-muted-foreground">Quantity</dt><dd>{{ result.quantity }}</dd><template v-if="result.expires_at"><dt class="text-muted-foreground">Hold expires</dt><dd>{{ deadline(result.expires_at) }}</dd></template><template v-else><dt class="text-muted-foreground">Requested dates</dt><dd>{{ result.starts_on }} – {{ result.ends_on }}</dd></template></dl>
          <Button class="w-full" @click="open = false">Done</Button>
        </div>
        <form v-else class="space-y-5" @submit.prevent="submit">
          <div class="grid grid-cols-2 gap-4"><label><span class="field-label">First name</span><Input v-model.trim="form.first_name" autocomplete="given-name" maxlength="100" required /></label><label><span class="field-label">Last name</span><Input v-model.trim="form.last_name" autocomplete="family-name" maxlength="100" /></label></div>
          <label class="block"><span class="field-label">Email</span><Input v-model.trim="form.email" type="email" autocomplete="email" required /></label>
          <label class="block"><span class="field-label">Phone</span><Input v-model.trim="form.phone" type="tel" autocomplete="tel" minlength="5" maxlength="32" required /></label>
          <div class="grid gap-4 sm:grid-cols-[1fr_7rem]"><div><Label for="request-location">Collection location</Label><Select v-model="form.location_public_id"><SelectTrigger id="request-location" class="mt-2"><SelectValue placeholder="Choose location" /></SelectTrigger><SelectContent><SelectItem v-for="location in options.locations" :key="location.public_id" :value="location.public_id">{{ location.name }}</SelectItem></SelectContent></Select><p v-if="locationAddress" class="mt-2 text-xs text-muted-foreground">{{ locationAddress }}</p></div><label><span class="field-label">Quantity</span><Input v-model.number="form.quantity" type="number" min="1" max="20" required /></label></div>
          <div v-if="kind === 'rental'" class="grid grid-cols-2 gap-4"><label><span class="field-label">Collect on</span><Input v-model="form.starts_on" type="date" required /></label><label><span class="field-label">Return on</span><Input v-model="form.ends_on" type="date" :min="form.starts_on" required /></label></div>
          <label class="block"><span class="field-label">Notes (optional)</span><Textarea v-model.trim="form.notes" maxlength="1000" placeholder="Anything the business should know?" /></label>
          <div class="rounded-lg bg-muted p-4 text-sm leading-6"><p>{{ kind === 'rental' ? 'This is a request, not a confirmed rental. Staff will contact you about availability, charges, and collection.' : `Your chosen units will be held for ${options.hold_hours} hours, then released if not purchased. Final price is confirmed at checkout.` }}</p><p v-if="options[`${kind}_terms`]" class="mt-3 whitespace-pre-line">{{ options[`${kind}_terms`] }}</p></div>
          <label class="flex items-start gap-3 text-sm leading-6"><Checkbox v-model:checked="form.accepts_terms" class="mt-1" /><span>I understand these terms and agree to be contacted about this request.</span></label>
          <Alert v-if="error" variant="destructive"><AlertCircle class="h-4 w-4" /><AlertTitle>Request not completed</AlertTitle><AlertDescription>{{ error }}</AlertDescription></Alert>
          <DialogFooter><Button type="button" variant="outline" :disabled="submitting" @click="open = false">Cancel</Button><Button :disabled="submitting || !form.accepts_terms || !form.location_public_id">{{ submitting ? 'Sending…' : title }}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </section>
</template>
<script setup>
import { AlertCircle, ArrowUpRight, CalendarRange, CheckCircle2, PackageCheck } from 'lucide-vue-next'
const props = defineProps({ product: { type: Object, required: true }, variant: { type: Object, default: null }, quantity: { type: Number, default: 1 }, slug: { type: String, required: true }, timezone: { type: String, default: 'Asia/Manila' } })
const config = useRuntimeConfig()
const options = computed(() => props.product.request_options || {})
const enabledModes = computed(() => [
  { key: 'reservation', label: 'Reserve for pickup', icon: PackageCheck, description: `Hold available units for ${options.value.hold_hours} hours and purchase later.` },
  { key: 'rental', label: 'Request a rental', icon: CalendarRange, description: 'Choose dates. Staff confirms availability, price, and collection before you commit.' },
].filter(mode => options.value[`${mode.key}_enabled`]))
const open = ref(false), kind = ref('reservation'), submitting = ref(false), error = ref(''), result = ref(null)
const form = reactive({ first_name: '', last_name: '', email: '', phone: '', location_public_id: '', quantity: 1, starts_on: '', ends_on: '', notes: '', accepts_terms: false })
const title = computed(() => kind.value === 'rental' ? 'Send rental request' : 'Confirm stock reservation')
const locationAddress = computed(() => options.value.locations?.find(item => item.public_id === form.location_public_id)?.address)
let requestKey = '', previousPayload = ''
function begin(mode) { kind.value = mode; result.value = null; error.value = ''; form.quantity = Math.min(20, Math.max(1, props.quantity || 1)); form.location_public_id ||= options.value.locations?.[0]?.public_id || ''; form.accepts_terms = false; requestKey = ''; previousPayload = ''; open.value = true }
function deadline(value) { return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short', timeZone: props.timezone }).format(new Date(value)) + ` (${props.timezone})` }
async function submit() {
  if (submitting.value || !props.variant) return
  const body = { ...form, kind: kind.value, offering_public_id: props.product.public_id, variant_public_id: props.variant.public_id }
  if (kind.value !== 'rental') { delete body.starts_on; delete body.ends_on }
  const payload = JSON.stringify(body)
  if (!requestKey || payload !== previousPayload) { requestKey = crypto.randomUUID(); previousPayload = payload }
  submitting.value = true; error.value = ''
  try { result.value = await $fetch(`public/${props.slug}/product-requests/`, { baseURL: config.public.apiBaseUrl, method: 'POST', body: { ...body, idempotency_key: requestKey } }) }
  catch (exception) { error.value = exception?.data?.error?.message || 'We could not complete this request. Check the details and try again.' }
  finally { submitting.value = false }
}
</script>
