<template>
  <section class="workspace-page space-y-6">
    <PageHeader title="Reservations & rentals" description="Choose how customers can request physical products, alongside your usual checkout." />
    <StatePanel v-if="loading" kind="loading" title="Loading commerce settings" />
    <StatePanel v-else-if="loadError" kind="error" title="Settings unavailable" :message="loadError"><Button variant="outline" @click="load">Try again</Button></StatePanel>
    <form v-else class="max-w-4xl space-y-6" @submit.prevent="save">
      <div class="divide-y rounded-xl border bg-card">
        <section class="p-5 sm:p-7">
          <div class="flex items-start gap-4"><PackageCheck class="mt-1 h-6 w-6 shrink-0 text-primary" /><div class="flex-1"><h2 class="font-bold">Reserve for pickup</h2><p class="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">Customers hold available stock for later pickup or purchase. No payment is taken. Expired or cancelled holds release stock automatically.</p></div><Switch v-model:checked="form.reservation_enabled" aria-label="Enable stock reservations" /></div>
          <div v-if="form.reservation_enabled" class="mt-6 border-t pt-5 sm:ml-10"><Label for="hold-hours">Hold deadline (hours)</Label><Input id="hold-hours" v-model.number="form.hold_hours" class="mt-2 max-w-32" type="number" min="1" max="168" required /><p class="mt-2 text-xs leading-5 text-muted-foreground">1–168 hours from confirmation. Changes apply only to new reservations.</p></div>
        </section>
        <section class="p-5 sm:p-7"><div class="flex items-start gap-4"><CalendarRange class="mt-1 h-6 w-6 shrink-0 text-primary" /><div class="flex-1"><h2 class="font-bold">Request a rental</h2><p class="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">Customers choose dates and submit a request. Staff reviews availability, price, deposit, and collection arrangements before approval. This does not collect payment or promise availability.</p><p class="mt-3 text-xs leading-5 text-muted-foreground">Approving sets aside units immediately until they are returned or the approval is cancelled. Future back-to-back rental scheduling is not enabled.</p></div><Switch v-model:checked="form.rental_enabled" aria-label="Enable rental requests" /></div></section>
      </div>
      <Alert><Info class="h-4 w-4" /><AlertTitle>Enable the business, then choose products</AlertTitle><AlertDescription>In each product’s Merchandising tab, enable reservations or rentals and write its terms. Only physical products with tracked inventory and active variants can accept requests. Turning a mode off does not cancel existing requests.</AlertDescription></Alert>
      <p v-if="error" role="alert" class="text-sm text-destructive">{{ error }}</p>
      <div class="flex flex-wrap items-center gap-3"><Button :disabled="saving"><Save class="h-4 w-4" />{{ saving ? 'Saving…' : 'Save request settings' }}</Button><ButtonLink variant="outline" to="/workspace/sell/requests">Manage requests</ButtonLink></div>
    </form>
  </section>
</template>
<script setup>
import { CalendarRange, Info, PackageCheck, Save } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const loading = ref(true), saving = ref(false), loadError = ref(''), error = ref('')
const form = reactive({ reservation_enabled: false, rental_enabled: false, hold_hours: 24 })
const endpoint = () => `businesses/${business.activeBusiness.public_id}/product-request-settings/`
onMounted(load)
async function load() {
  loading.value = true; loadError.value = ''
  try { if (!business.activeBusiness) await business.loadBusinesses(); Object.assign(form, await apiFetch(endpoint())) }
  catch (exception) { loadError.value = exception?.data?.error?.message || 'These settings require owner, admin, or manager access.' }
  finally { loading.value = false }
}
async function save() {
  saving.value = true; error.value = ''
  try { Object.assign(form, await apiFetch(endpoint(), { method: 'PUT', body: { ...form } })); toast({ title: 'Request settings saved', description: 'Enabled products now use these settings.' }) }
  catch (exception) { error.value = exception?.data?.error?.message || 'Settings could not be saved.' }
  finally { saving.value = false }
}
</script>
