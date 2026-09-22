<template>
  <Dialog :open="Boolean(item)" @update:open="value => { if (!value && !saving) $emit('close') }">
    <DialogContent class="max-h-[90dvh] overflow-y-auto sm:max-w-2xl" @interact-outside="saving && $event.preventDefault()" @escape-key-down="saving && $event.preventDefault()">
      <template v-if="item">
        <DialogHeader><div class="mb-2 flex items-center gap-3"><CalendarRange v-if="item.kind === 'rental'" class="h-6 w-6 text-primary" /><PackageCheck v-else class="h-6 w-6 text-primary" /><Badge variant="secondary">{{ label(item.status) }}</Badge></div><DialogTitle>{{ item.snapshot.name }}</DialogTitle><DialogDescription>{{ item.snapshot.variant }} · {{ item.quantity }} units · {{ item.location_name }}</DialogDescription></DialogHeader>
        <Alert v-if="item.attention" :variant="item.attention.code === 'overdue' ? 'destructive' : 'default'"><CircleAlert class="h-4 w-4" /><AlertTitle>{{ item.attention.label }}</AlertTitle><AlertDescription>{{ guidance }}</AlertDescription></Alert>
        <div class="grid gap-5 border-y py-5 sm:grid-cols-2"><div><h3 class="text-xs font-semibold text-muted-foreground">Customer</h3><p class="mt-2 text-sm font-semibold">{{ item.first_name }} {{ item.last_name }}</p><p class="mt-1 break-all text-sm">{{ item.email }}</p><p class="text-sm">{{ item.phone }}</p></div><div><h3 class="text-xs font-semibold text-muted-foreground">{{ item.kind === 'rental' ? 'Rental dates' : 'Hold deadline' }}</h3><p class="mt-2 text-sm">{{ item.kind === 'rental' ? `${item.starts_on} – ${item.ends_on}` : deadline(item.expires_at) }}</p><p class="mt-2 text-xs leading-5 text-muted-foreground">{{ item.stock_held ? 'Units remain set aside. Do not release until physically returned or the uncollected request is cancelled.' : 'This request is not holding stock.' }}</p></div></div>
        <CustomerContactActions :email="item.email" :phone="item.phone" :reference="`${item.snapshot.name} · ${item.public_id}`" />
        <p class="text-xs leading-5 text-muted-foreground">Contact buttons open your phone or email app. Nothing is sent automatically. Record the outcome below.</p>
        <p v-if="item.notes" class="whitespace-pre-line text-sm leading-6"><strong>Customer notes:</strong> {{ item.notes }}</p>
        <p v-if="item.decision_note" class="rounded-lg bg-muted p-4 text-sm leading-6"><strong>Latest staff note:</strong> {{ item.decision_note }}</p>
        <Accordion type="single" collapsible><AccordionItem value="terms"><AccordionTrigger>Original request terms</AccordionTrigger><AccordionContent class="whitespace-pre-line text-sm leading-6">{{ item.snapshot.terms || 'No additional product terms were entered.' }}</AccordionContent></AccordionItem></Accordion>
        <div class="space-y-4"><div><Label for="request-action">Next action</Label><Select v-model="action"><SelectTrigger id="request-action" class="mt-2"><SelectValue placeholder="Choose an action" /></SelectTrigger><SelectContent><SelectItem v-for="option in actions" :key="option.key" :value="option.key">{{ option.label }}</SelectItem></SelectContent></Select></div>
          <p v-if="action" class="text-sm leading-6 text-muted-foreground">{{ actionHelp[action] }}</p>
          <label v-if="action === 'extend'" class="block"><span class="field-label">New agreed return date</span><Input v-model="endsOn" type="date" /></label>
          <label class="block"><span class="field-label">{{ noteRequired ? 'Outcome or reason (required)' : 'Staff note (optional)' }}</span><Textarea v-model.trim="note" maxlength="500" placeholder="Record who you contacted, the outcome, and agreed next steps." /></label>
          <label class="flex items-start gap-3 text-sm leading-6"><Checkbox v-model:checked="confirmed" class="mt-1" /><span>{{ action === 'return' ? 'I confirm the units have physically returned and can be released into available stock.' : 'I have reviewed the request and confirm this action.' }}</span></label>
        </div>
        <Alert v-if="error" variant="destructive"><AlertTitle>Action not completed</AlertTitle><AlertDescription>{{ error }}</AlertDescription></Alert>
        <DialogFooter><Button variant="outline" :disabled="saving" @click="$emit('close')">Close</Button><Button :disabled="saving || !action || !confirmed || (noteRequired && !note) || (action === 'extend' && !endsOn)" @click="save">{{ saving ? 'Updating…' : 'Confirm action' }}</Button></DialogFooter>
      </template>
    </DialogContent>
  </Dialog>
</template>
<script setup>
import { CalendarRange, CircleAlert, PackageCheck } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'
import CustomerContactActions from './CustomerContactActions.vue'
import { requestStatusLabel } from '~/utils/requestStatus'
const props = defineProps({ item: { type: Object, default: null }, initialAction: { type: String, default: '' } })
const emit = defineEmits(['close', 'updated'])
const business = useBusinessStore(), { apiFetch } = useApiClient()
const action = ref(''), note = ref(''), endsOn = ref(''), confirmed = ref(false), saving = ref(false), error = ref('')
const label = requestStatusLabel
const actions = computed(() => [
  ...({ pending: [{ key: 'approve', label: 'Approve rental and set aside stock' }, { key: 'reject', label: 'Reject request' }, { key: 'cancel', label: 'Cancel request' }], held: [{ key: 'convert', label: 'Create pickup order' }, { key: 'cancel', label: 'Cancel and release stock' }], approved: [{ key: 'collect', label: 'Mark rental collected' }, { key: 'extend', label: 'Extend by agreement' }, { key: 'cancel', label: 'Cancel and release stock' }], collected: [{ key: 'return', label: 'Record physical return' }, { key: 'extend', label: 'Extend by agreement' }] }[props.item?.status] || []),
  { key: 'follow_up', label: 'Record customer follow-up' },
])
const noteRequired = computed(() => ['cancel', 'reject', 'extend', 'follow_up'].includes(action.value))
const guidance = computed(() => ({ overdue: 'Contact the customer. Agree a later return date or record the physical return. Stock stays held; no late charge is added automatically.', due_today: 'Confirm the return arrangements. Only mark returned once the units are received.', missed_pickup: 'Check whether collection is still required. Contact the customer before cancelling and releasing stock.', approval: 'Confirm availability, price and collection arrangements before approval.' }[props.item?.attention?.code]))
const actionHelp = { approve: 'Confirm charges and collection with the customer first. Approval sets aside stock immediately; this action takes no payment.', convert: 'Creates an unpaid pickup order at current catalog prices. Complete payment in the existing counter flow within its normal stock deadline.', extend: 'Records the agreed date without charging a fee. Existing units remain held until return. The previous date is retained in the audit record.', follow_up: 'Saves an audit note only. It does not send a message or change the request status.', return: 'Release only units that have been physically returned. Overdue rentals never auto-release.', collect: 'Confirm that the customer has collected the rental. Units remain set aside until their return.', cancel: 'Cancels this uncollected request and releases held stock, if any.', reject: 'Rejects the pending request without creating a rental or taking payment.' }
watch(() => props.item?.public_id, () => { action.value = props.initialAction; note.value = ''; endsOn.value = props.item?.ends_on || ''; confirmed.value = false; error.value = '' }, { immediate: true })
watch(action, () => { confirmed.value = false })
function deadline(date) { return date ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short', timeZone: business.activeBusiness?.timezone || 'Asia/Manila' }).format(new Date(date)) : '—' }
async function save() {
  if (!confirmed.value || saving.value) return
  saving.value = true; error.value = ''
  try {
    const body = { action: action.value, note: note.value, expected_updated_at: props.item.updated_at, ...(action.value === 'extend' ? { ends_on: endsOn.value } : {}) }
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/product-requests/${props.item.public_id}/transition/`, { method: 'POST', body })
    toast({ title: 'Request updated', description: action.value === 'follow_up' ? 'Follow-up recorded. No message was sent automatically.' : label(response.status) })
    emit('updated', response); emit('close')
  } catch (exception) { error.value = exception?.data?.error?.message || 'The request changed or could not be updated. Close, refresh, and review before retrying.' }
  finally { saving.value = false }
}
</script>
