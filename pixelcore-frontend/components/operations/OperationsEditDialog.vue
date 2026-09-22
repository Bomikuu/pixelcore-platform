<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="flex max-h-[calc(100dvh-2rem)] w-[calc(100vw-2rem)] max-w-4xl flex-col gap-0 overflow-hidden p-0">
      <DialogHeader class="shrink-0 border-b px-6 py-5 pr-14">
        <DialogTitle>Edit {{ title }}</DialogTitle>
        <DialogDescription>Update the operational information used throughout this business.</DialogDescription>
      </DialogHeader>

      <form id="operations-edit-form" class="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5" @submit.prevent="submit">
        <template v-if="resource === 'inventory'">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2">
              <Label for="inventory-bin">Bin or shelf location</Label>
              <Input id="inventory-bin" v-model.trim="form.bin_location" placeholder="Aisle A · Shelf 3" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label>Preferred supplier</Label><OperationsFieldHelp text="The default replenishment source for this product at this location." /></div>
              <Select v-model="form.preferred_supplier_public_id">
                <SelectTrigger><SelectValue placeholder="No preferred supplier" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No preferred supplier</SelectItem>
                  <SelectItem v-for="supplier in suppliers" :key="supplier.public_id" :value="supplier.public_id">{{ supplier.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="inventory-threshold">Low-stock threshold</Label><OperationsFieldHelp text="The available quantity that triggers a reorder warning. It does not place an order automatically." /></div>
              <Input id="inventory-threshold" v-model="form.low_stock_threshold" type="number" min="0" step="0.001" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="inventory-reorder">Suggested reorder quantity</Label><OperationsFieldHelp text="The usual amount to purchase once the item reaches its low-stock threshold." /></div>
              <Input id="inventory-reorder" v-model="form.reorder_quantity" type="number" min="0" step="0.001" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="inventory-target">Target stock level</Label><OperationsFieldHelp text="The preferred available quantity after replenishment." /></div>
              <Input id="inventory-target" v-model="form.target_stock_level" type="number" min="0" step="0.001" />
            </div>
            <div class="grid gap-2">
              <Label for="inventory-counted">Last physically counted</Label>
              <Input id="inventory-counted" v-model="form.last_counted_at" type="date" />
            </div>
          </div>
          <div class="grid gap-2">
            <Label for="inventory-notes">Inventory notes</Label>
            <Textarea id="inventory-notes" v-model.trim="form.notes" rows="3" placeholder="Storage, handling, or replenishment instructions" />
          </div>
        </template>

        <template v-else-if="resource === 'suppliers'">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="flex items-center gap-4 sm:col-span-2">
              <div class="grid h-20 w-20 shrink-0 place-items-center overflow-hidden rounded-xl border bg-muted">
                <img v-if="supplierImagePreview" :src="supplierImagePreview" :alt="`${form.name} supplier image preview`" class="h-full w-full object-cover" />
                <Building2 v-else class="h-8 w-8 text-muted-foreground" aria-hidden="true" />
              </div>
              <div class="min-w-0 flex-1 space-y-2">
                <Label for="supplier-image">Replace supplier image</Label>
                <Input id="supplier-image" type="file" accept="image/jpeg,image/png,image/webp,image/avif" @change="handleSupplierImage" />
              </div>
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="supplier-name">Supplier name</Label>
              <Input id="supplier-name" v-model.trim="form.name" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <div class="flex items-center gap-1.5"><Label>Supplier category</Label><OperationsFieldHelp text="The supplier's role in your supply chain, such as manufacturer, distributor, contractor, or marketplace." /></div>
              <Select v-model="form.category"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="category in supplierCategories" :key="category.value" :value="category.value">{{ category.label }}</SelectItem></SelectContent></Select>
            </div>
            <div class="grid gap-2">
              <Label for="supplier-code">Supplier code</Label>
              <Input id="supplier-code" v-model.trim="form.code" placeholder="SUP-001" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="supplier-account">Account reference</Label><OperationsFieldHelp text="Your account number in the supplier's system, not the internal PixelCore supplier code." /></div>
              <Input id="supplier-account" v-model.trim="form.account_reference" />
            </div>
            <div class="grid gap-2">
              <Label for="supplier-contact">Contact person</Label>
              <Input id="supplier-contact" v-model.trim="form.contact_name" />
            </div>
            <div class="grid gap-2">
              <Label for="supplier-tax">Tax identifier</Label>
              <Input id="supplier-tax" v-model.trim="form.tax_id" />
            </div>
            <div class="grid gap-2">
              <Label for="supplier-email">Email</Label>
              <Input id="supplier-email" v-model.trim="form.email" type="email" />
            </div>
            <div class="grid gap-2">
              <Label for="supplier-phone">Phone</Label>
              <Input id="supplier-phone" v-model.trim="form.phone" type="tel" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="supplier-website">Website</Label>
              <Input id="supplier-website" v-model.trim="form.website" type="url" placeholder="https://supplier.example" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="supplier-terms">Payment terms in days</Label><OperationsFieldHelp text="How many days the supplier allows before payment is due. Zero means payment on receipt." /></div>
              <Input id="supplier-terms" v-model="form.payment_terms_days" type="number" min="0" max="365" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="supplier-lead">Typical lead time in days</Label><OperationsFieldHelp text="The usual time from placing an order to receiving it. Product-specific lead times can override this." /></div>
              <Input id="supplier-lead" v-model="form.lead_time_days" type="number" min="0" max="365" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="supplier-address">Address</Label>
              <Textarea id="supplier-address" v-model.trim="form.address" rows="3" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="supplier-notes">Internal notes</Label>
              <Textarea id="supplier-notes" v-model.trim="form.notes" rows="3" />
            </div>
            <label class="flex items-center justify-between gap-4 rounded-xl border p-4 sm:col-span-2">
              <span><strong class="block text-sm">Active supplier</strong><span class="mt-1 block text-xs text-muted-foreground">Available for new purchase orders and expense records.</span></span>
              <Switch v-model:checked="form.is_active" />
            </label>
          </div>
        </template>

        <template v-else-if="resource === 'purchase-orders'">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2">
              <Label>Supplier</Label>
              <Select v-model="form.supplier_public_id">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem v-for="supplier in suppliers" :key="supplier.public_id" :value="supplier.public_id">{{ supplier.name }}</SelectItem></SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label>Receiving location</Label><OperationsFieldHelp text="Received quantities from this order are added to inventory at this location." /></div>
              <Select v-model="form.location_public_id">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem v-for="location in locations" :key="location.public_id" :value="location.public_id">{{ location.name }}</SelectItem></SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <Label>Status</Label>
              <Select v-model="form.status">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem v-for="status in purchaseStatuses" :key="status.value" :value="status.value">{{ status.label }}</SelectItem></SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="po-reference">Supplier reference</Label><OperationsFieldHelp text="The supplier's confirmation, order, or tracking number." /></div>
              <Input id="po-reference" v-model.trim="form.supplier_reference" />
            </div>
            <div class="grid gap-2">
              <Label for="po-ordered">Ordered on</Label>
              <Input id="po-ordered" v-model="form.ordered_at" type="date" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="po-expected">Expected on</Label><OperationsFieldHelp text="The promised delivery date used to identify overdue purchase orders." /></div>
              <Input id="po-expected" v-model="form.expected_at" type="date" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="po-shipping-method">Shipping method</Label>
              <Input id="po-shipping-method" v-model.trim="form.shipping_method" placeholder="Courier, supplier delivery, pickup" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="po-shipping-address">Delivery instructions or address</Label>
              <Textarea id="po-shipping-address" v-model.trim="form.shipping_address" rows="3" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="po-notes">Purchase notes</Label>
              <Textarea id="po-notes" v-model.trim="form.notes" rows="3" />
            </div>
          </div>
        </template>

        <template v-else-if="resource === 'quotations'">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2">
              <Label>Status</Label>
              <Select v-model="form.status"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="status in quotationStatuses" :key="status.value" :value="status.value">{{ status.label }}</SelectItem></SelectContent></Select>
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5"><Label for="quotation-expiry">Expires</Label><OperationsFieldHelp text="The last date and time the quoted price and terms remain valid." /></div>
              <Input id="quotation-expiry" v-model="form.expires_at" type="datetime-local" />
            </div>
          </div>
          <div class="grid gap-2"><Label for="quotation-notes">Notes</Label><Textarea id="quotation-notes" v-model.trim="form.notes" rows="4" /></div>
        </template>

        <template v-else-if="resource === 'invoices'">
          <div class="grid gap-4 sm:grid-cols-3">
            <div class="grid gap-2">
              <Label>Status</Label>
              <Select v-model="form.status"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="status in invoiceStatuses" :key="status.value" :value="status.value">{{ status.label }}</SelectItem></SelectContent></Select>
            </div>
            <div class="grid gap-2"><Label for="invoice-issued">Issued on</Label><Input id="invoice-issued" v-model="form.issued_at" type="date" /></div>
            <div class="grid gap-2"><div class="flex items-center gap-1.5"><Label for="invoice-due">Due on</Label><OperationsFieldHelp text="The payment deadline used to surface invoices that are due soon or overdue." /></div><Input id="invoice-due" v-model="form.due_at" type="date" /></div>
          </div>
          <div class="grid gap-2"><Label for="invoice-notes">Notes</Label><Textarea id="invoice-notes" v-model.trim="form.notes" rows="4" /></div>
        </template>

        <template v-else-if="resource === 'expenses'">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2">
              <Label>Category</Label>
              <Select v-model="form.category_public_id"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="category in categories" :key="category.public_id" :value="category.public_id">{{ category.name }}</SelectItem></SelectContent></Select>
            </div>
            <div class="grid gap-2">
              <Label>Supplier</Label>
              <Select v-model="form.supplier_public_id"><SelectTrigger><SelectValue placeholder="No supplier" /></SelectTrigger><SelectContent><SelectItem value="none">No supplier</SelectItem><SelectItem v-for="supplier in suppliers" :key="supplier.public_id" :value="supplier.public_id">{{ supplier.name }}</SelectItem></SelectContent></Select>
            </div>
            <div class="grid gap-2 sm:col-span-2"><Label for="expense-description">Description</Label><Input id="expense-description" v-model.trim="form.description" /></div>
            <div class="grid gap-2"><Label for="expense-amount">Amount</Label><Input id="expense-amount" v-model="form.amount" type="number" min="0.01" step="0.01" /></div>
            <div class="grid gap-2"><div class="flex items-center gap-1.5"><Label for="expense-tax">Tax amount</Label><OperationsFieldHelp text="The tax portion included in this expense. Enter zero when no tax applies." /></div><Input id="expense-tax" v-model="form.tax_amount" type="number" min="0" step="0.01" /></div>
            <div class="grid gap-2"><Label for="expense-date">Incurred on</Label><Input id="expense-date" v-model="form.incurred_at" type="date" /></div>
            <div class="grid gap-2"><Label for="expense-method">Payment method</Label><Input id="expense-method" v-model.trim="form.payment_method" /></div>
            <div class="grid gap-2 sm:col-span-2"><div class="flex items-center gap-1.5"><Label for="expense-reference">Reference</Label><OperationsFieldHelp text="A receipt number, transaction ID, or supplier document number that makes the payment traceable." /></div><Input id="expense-reference" v-model.trim="form.reference" /></div>
            <div class="rounded-xl border bg-muted/20 p-4 sm:col-span-2">
              <div class="flex items-start gap-3">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-background text-primary ring-1 ring-border">
                  <Paperclip class="h-5 w-5" aria-hidden="true" />
                </span>
                <div class="min-w-0 flex-1 space-y-2">
                  <div>
                    <Label for="expense-receipt">{{ form.receipt_public_id ? 'Replace receipt' : 'Attach receipt' }}</Label>
                    <p class="mt-1 text-xs text-muted-foreground">
                      {{ form.receipt_name ? `Current: ${form.receipt_name}. ` : '' }}Upload a JPG, PNG, WebP, or PDF.
                    </p>
                  </div>
                  <Input
                    id="expense-receipt"
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/avif,application/pdf"
                    @change="handleExpenseReceipt"
                  />
                  <p v-if="form.receipt_file" class="truncate text-xs font-medium">Selected replacement: {{ form.receipt_file.name }}</p>
                </div>
              </div>
            </div>
          </div>
        </template>

        <p v-if="error" class="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive" role="alert">{{ error }}</p>
      </form>

      <DialogFooter class="shrink-0 border-t bg-background px-6 py-4">
        <Button type="button" variant="outline" @click="emit('update:open', false)">Cancel</Button>
        <Button form="operations-edit-form" type="submit" :disabled="saving || !canSubmit">
          <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
          {{ saving ? 'Saving…' : 'Save changes' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { Building2, Loader2, Paperclip } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import OperationsFieldHelp from '@/components/operations/OperationsFieldHelp.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  resource: { type: String, required: true },
  businessId: { type: String, required: true },
  record: { type: Object, default: null },
  suppliers: { type: Array, default: () => [] },
  locations: { type: Array, default: () => [] },
  categories: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:open', 'saved'])
const { apiFetch } = useApiClient()
const form = reactive({})
const saving = ref(false)
const error = ref('')
const supplierImagePreviewUrl = ref('')
const supplierImagePreview = computed(() => supplierImagePreviewUrl.value || form.image_url || '')

const title = computed(() => ({ inventory: 'inventory settings', suppliers: 'supplier', 'purchase-orders': 'purchase order', quotations: 'quotation', invoices: 'invoice', expenses: 'expense' }[props.resource] || 'record'))
const canSubmit = computed(() => {
  if (props.resource === 'suppliers') return Boolean(form.name)
  if (props.resource === 'purchase-orders') return Boolean(form.supplier_public_id && form.location_public_id)
  if (props.resource === 'expenses') return Boolean(form.category_public_id && form.description && Number(form.amount) > 0)
  return true
})
const purchaseStatuses = computed(() => {
  const editable = optionSet(['draft', 'ordered', 'cancelled'])
  if (['partially_received', 'received'].includes(props.record?.status)) {
    editable.unshift(...optionSet([props.record.status]))
  }
  return editable
})
const quotationStatuses = optionSet(['draft', 'sent', 'accepted', 'declined', 'expired', 'converted'])
const invoiceStatuses = optionSet(['draft', 'issued', 'partially_paid', 'paid', 'overdue', 'void'])

watch(() => [props.open, props.record], ([open]) => {
  if (!open) {
    clearSupplierImagePreview()
    return
  }
  if (!props.record) return
  clearSupplierImagePreview()
  Object.keys(form).forEach(key => delete form[key])
  Object.assign(form, { ...props.record })
  form.image_file = null
  form.receipt_file = null
  form.preferred_supplier_public_id ||= 'none'
  form.supplier_public_id ||= 'none'
  form.expires_at = toLocalDateTime(form.expires_at)
  error.value = ''
})

onBeforeUnmount(clearSupplierImagePreview)

async function submit() {
  saving.value = true
  error.value = ''
  try {
    const body = payload()
    if (props.resource === 'suppliers' && form.image_file) body.image_public_id = await uploadSupplierImage()
    if (props.resource === 'expenses' && form.receipt_file) body.receipt_public_id = await uploadExpenseReceipt()
    const saved = await apiFetch(`businesses/${props.businessId}/${props.resource}/${props.record.public_id}/`, {
      method: 'PATCH',
      body,
    })
    emit('saved', saved)
    emit('update:open', false)
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || requestError?.data?.detail || 'The changes could not be saved.'
  } finally {
    saving.value = false
  }
}

function payload() {
  if (props.resource === 'inventory') return pick(['low_stock_threshold', 'reorder_quantity', 'target_stock_level', 'bin_location', 'preferred_supplier_public_id', 'last_counted_at', 'notes'], { preferred_supplier_public_id: nullable(form.preferred_supplier_public_id), last_counted_at: form.last_counted_at || null })
  if (props.resource === 'suppliers') return pick(['name', 'code', 'category', 'contact_name', 'email', 'phone', 'website', 'address', 'tax_id', 'account_reference', 'payment_terms_days', 'lead_time_days', 'notes', 'is_active'])
  if (props.resource === 'purchase-orders') return pick(['supplier_public_id', 'location_public_id', 'status', 'ordered_at', 'expected_at', 'supplier_reference', 'shipping_method', 'shipping_address', 'notes'], { ordered_at: form.ordered_at || null, expected_at: form.expected_at || null })
  if (props.resource === 'quotations') return pick(['status', 'expires_at', 'notes'], { expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null })
  if (props.resource === 'invoices') return pick(['status', 'issued_at', 'due_at', 'notes'], { issued_at: form.issued_at || null, due_at: form.due_at || null })
  return pick(['category_public_id', 'supplier_public_id', 'receipt_public_id', 'description', 'amount', 'tax_amount', 'incurred_at', 'payment_method', 'reference'], { supplier_public_id: nullable(form.supplier_public_id) })
}

function pick(keys, overrides = {}) { return Object.assign(Object.fromEntries(keys.map(key => [key, form[key]])), overrides) }
function nullable(value) { return value && value !== 'none' ? value : null }
function optionSet(values) { return values.map(value => ({ value, label: value.replaceAll('_', ' ').replace(/^./, character => character.toUpperCase()) })) }
function toLocalDateTime(value) { return value ? new Date(value).toISOString().slice(0, 16) : '' }

function handleSupplierImage(event) {
  clearSupplierImagePreview()
  form.image_file = event.target.files?.[0] || null
  if (form.image_file) supplierImagePreviewUrl.value = URL.createObjectURL(form.image_file)
}

function clearSupplierImagePreview() {
  if (supplierImagePreviewUrl.value) URL.revokeObjectURL(supplierImagePreviewUrl.value)
  supplierImagePreviewUrl.value = ''
}

async function uploadSupplierImage() {
  const body = new FormData()
  body.append('title', `${form.name || 'Supplier'} image`)
  body.append('alt_text', `${form.name || 'Supplier'} supplier image`)
  body.append('asset_type', 'image')
  body.append('file', form.image_file)
  const asset = await apiFetch(`businesses/${props.businessId}/assets/`, { method: 'POST', body })
  return asset.public_id
}

function handleExpenseReceipt(event) {
  form.receipt_file = event.target.files?.[0] || null
}

async function uploadExpenseReceipt() {
  const body = new FormData()
  body.append('title', form.receipt_file.name)
  body.append('asset_type', form.receipt_file.type === 'application/pdf' ? 'document' : 'image')
  body.append('file', form.receipt_file)
  const asset = await apiFetch(`businesses/${props.businessId}/assets/`, { method: 'POST', body })
  return asset.public_id
}

const supplierCategories = [
  { value: 'manufacturer', label: 'Manufacturer' },
  { value: 'distributor', label: 'Distributor' },
  { value: 'wholesaler', label: 'Wholesaler' },
  { value: 'service_provider', label: 'Service provider' },
  { value: 'contractor', label: 'Contractor' },
  { value: 'marketplace', label: 'Marketplace' },
  { value: 'other', label: 'Other' },
]
</script>
