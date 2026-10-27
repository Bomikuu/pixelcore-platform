<template>
  <Dialog :open="open" @update:open="handleOpenChange">
    <DialogContent class="flex max-h-[calc(100dvh-2rem)] w-[calc(100vw-2rem)] max-w-4xl flex-col gap-0 overflow-hidden p-0 transition-none" @close-auto-focus="emit('closed', $event)">
      <DialogHeader class="shrink-0 border-b px-6 py-5 pr-14">
        <DialogTitle class="flex items-center gap-2">
          <component :is="dialogMeta.icon" class="h-5 w-5 text-primary" aria-hidden="true" />
          {{ dialogMeta.title }}
        </DialogTitle>
        <DialogDescription>{{ dialogMeta.description }}</DialogDescription>
      </DialogHeader>

      <form id="operations-create-form" class="min-h-0 flex-1 space-y-5 overflow-y-auto px-6 py-5" novalidate @submit.prevent="submit">
        <template v-if="view === 'inventory'">
          <div v-if="inventory.length" class="grid gap-2">
            <Label>Inventory action</Label>
            <Select v-model="form.inventory_mode">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="adjust">Adjust an existing balance</SelectItem>
                <SelectItem value="new">Add a new stock location</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div v-if="form.inventory_mode === 'adjust' && inventory.length" class="grid gap-2">
            <Label>Stock balance</Label>
            <Select v-model="form.balance_public_id">
              <SelectTrigger><SelectValue placeholder="Choose inventory" /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="item in inventory" :key="item.public_id" :value="item.public_id">
                  {{ item.offering_name }} · {{ item.variant_name }} · {{ item.location_name || 'Location' }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div v-else class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2">
              <Label>Product variant</Label>
              <Select v-model="form.variant_public_id">
                <SelectTrigger><SelectValue placeholder="Choose a variant" /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="variant in variants" :key="variant.public_id" :value="variant.public_id">{{ variant.label }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <Label>Location</Label>
              <Select v-model="form.location_public_id">
                <SelectTrigger><SelectValue placeholder="Choose a location" /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="location in locations" :key="location.public_id" :value="location.public_id">{{ location.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="inventory-threshold">Low-stock threshold</Label>
                <OperationsFieldHelp text="The available quantity that triggers a reorder warning. This does not place an order automatically." />
              </div>
              <Input id="inventory-threshold" v-model="form.low_stock_threshold" type="number" min="0" step="0.001" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="inventory-reorder">Suggested reorder quantity</Label>
                <OperationsFieldHelp text="The quantity your team normally purchases when this item reaches its low-stock threshold." />
              </div>
              <Input id="inventory-reorder" v-model="form.reorder_quantity" type="number" min="0" step="0.001" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="inventory-target">Target stock level</Label>
                <OperationsFieldHelp text="The preferred quantity after replenishment. Keep this at or above the low-stock threshold." />
              </div>
              <Input id="inventory-target" v-model="form.target_stock_level" type="number" min="0" step="0.001" />
            </div>
            <div class="grid gap-2">
              <Label for="inventory-bin">Bin or shelf location</Label>
              <Input id="inventory-bin" v-model.trim="form.bin_location" placeholder="Aisle A · Shelf 3" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <div class="flex items-center gap-1.5">
                <Label>Preferred supplier</Label>
                <OperationsFieldHelp text="The default supplier suggested when this product needs replenishment. Other suppliers can still provide the same product." />
              </div>
              <Select v-model="form.preferred_supplier_public_id">
                <SelectTrigger><SelectValue placeholder="No preferred supplier" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No preferred supplier</SelectItem>
                  <SelectItem v-for="supplier in suppliers" :key="supplier.public_id" :value="supplier.public_id">{{ supplier.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div class="grid gap-2">
            <Label for="inventory-quantity">{{ form.inventory_mode === 'adjust' ? 'Quantity change' : 'Opening quantity' }}</Label>
            <Input id="inventory-quantity" v-model="form.quantity_delta" type="number" step="0.001" />
            <p class="text-xs text-muted-foreground">Use a negative number to reduce recorded stock.</p>
          </div>
          <div class="grid gap-2">
            <Label for="inventory-note">Reason</Label>
            <Textarea id="inventory-note" v-model.trim="form.note" rows="3" placeholder="Opening count, damage correction, or physical count adjustment" />
          </div>
        </template>

        <template v-else-if="view === 'suppliers'">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2 sm:col-span-2">
              <Label for="supplier-image">Supplier image or logo</Label>
              <Input id="supplier-image" type="file" accept="image/jpeg,image/png,image/webp,image/avif" @change="form.image_file = $event.target.files?.[0] || null" />
              <p class="text-xs text-muted-foreground">Optional. Use a recognizable logo, storefront, product, or contact image.</p>
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="supplier-name">Supplier name</Label>
              <Input id="supplier-name" v-model.trim="form.name" placeholder="Acme Distribution" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <div class="flex items-center gap-1.5">
                <Label>Supplier category</Label>
                <OperationsFieldHelp text="Describes the supplier's role in your supply chain, such as manufacturer, distributor, contractor, or marketplace." />
              </div>
              <Select v-model="form.category">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem v-for="category in supplierCategories" :key="category.value" :value="category.value">{{ category.label }}</SelectItem></SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <Label for="supplier-code">Supplier code</Label>
              <Input id="supplier-code" v-model.trim="form.code" placeholder="SUP-001" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="supplier-account">Account reference</Label>
                <OperationsFieldHelp text="Your customer or account number in the supplier's own system. This is different from the supplier code used internally in PixelCore." />
              </div>
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
              <div class="flex items-center gap-1.5">
                <Label for="supplier-terms">Payment terms in days</Label>
                <OperationsFieldHelp text="How many days the supplier normally allows before payment is due. Use zero for payment on receipt." />
              </div>
              <Input id="supplier-terms" v-model="form.payment_terms_days" type="number" min="0" max="365" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="supplier-lead">Typical lead time in days</Label>
                <OperationsFieldHelp text="The normal number of days between placing an order and receiving it. Product-specific lead times can override this." />
              </div>
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
          </div>
        </template>

        <template v-else-if="view === 'purchase-orders'">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2">
              <Label>Supplier</Label>
              <Select v-model="form.supplier_public_id">
                <SelectTrigger><SelectValue placeholder="Choose a supplier" /></SelectTrigger>
                <SelectContent><SelectItem v-for="supplier in suppliers" :key="supplier.public_id" :value="supplier.public_id">{{ supplier.name }}</SelectItem></SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label>Receiving location</Label>
                <OperationsFieldHelp text="Inventory from this order will be added to this location when Receive stock is recorded." />
              </div>
              <Select v-model="form.location_public_id">
                <SelectTrigger><SelectValue placeholder="Choose a location" /></SelectTrigger>
                <SelectContent><SelectItem v-for="location in locations" :key="location.public_id" :value="location.public_id">{{ location.name }}</SelectItem></SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <Label for="po-ordered">Ordered date</Label>
              <Input id="po-ordered" v-model="form.ordered_at" type="date" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="po-expected">Expected date</Label>
                <OperationsFieldHelp text="The promised delivery date. Open orders become overdue when this date passes." />
              </div>
              <Input id="po-expected" v-model="form.expected_at" type="date" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="po-reference">Supplier reference</Label>
                <OperationsFieldHelp text="The supplier's order, confirmation, or tracking number used when following up on delivery." />
              </div>
              <Input id="po-reference" v-model.trim="form.supplier_reference" />
            </div>
            <div class="grid gap-2">
              <Label for="po-shipping-method">Shipping method</Label>
              <Input id="po-shipping-method" v-model.trim="form.shipping_method" placeholder="Courier or pickup" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="po-shipping-address">Delivery instructions or address</Label>
              <Textarea id="po-shipping-address" v-model.trim="form.shipping_address" rows="3" />
            </div>
          </div>
          <DocumentLineFields :model-value="form" :variants="variants" mode="purchase" @update:model-value="Object.assign(form, $event)" />
          <div class="grid gap-2">
            <Label for="po-notes">Purchase notes</Label>
            <Textarea id="po-notes" v-model.trim="form.notes" rows="3" />
          </div>
        </template>

        <template v-else-if="['quotations', 'invoices'].includes(view)">
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2 sm:col-span-2">
              <Label>Customer</Label>
              <Select v-model="form.customer_public_id">
                <SelectTrigger><SelectValue placeholder="Choose a customer" /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="customer in customers" :key="customer.public_id" :value="customer.public_id">{{ customerLabel(customer) }}</SelectItem>
                </SelectContent>
              </Select>
              <p v-if="!customers.length" class="text-xs text-destructive">Add a customer in Sell before creating this document.</p>
            </div>
            <div v-if="view === 'quotations'" class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="quote-expiry">Expires on</Label>
                <OperationsFieldHelp text="The last date the quoted price and terms remain valid. Expiring quotations are highlighted for follow-up." />
              </div>
              <Input id="quote-expiry" v-model="form.expires_at" type="date" />
            </div>
            <template v-else>
              <div class="grid gap-2">
                <Label for="invoice-issued">Issued on</Label>
                <Input id="invoice-issued" v-model="form.issued_at" type="date" />
              </div>
              <div class="grid gap-2">
                <div class="flex items-center gap-1.5">
                  <Label for="invoice-due">Due on</Label>
                  <OperationsFieldHelp text="The payment deadline. Unpaid balances are highlighted when this date approaches or passes." />
                </div>
                <Input id="invoice-due" v-model="form.due_at" type="date" />
              </div>
            </template>
          </div>
          <DocumentLineFields :model-value="form" mode="commercial" @update:model-value="Object.assign(form, $event)" />
          <div class="grid gap-2">
            <Label for="document-notes">Document notes</Label>
            <Textarea id="document-notes" v-model.trim="form.notes" rows="3" />
          </div>
          <Alert>
            <Info class="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Operational document</AlertTitle>
            <AlertDescription>This record is not represented as a BIR-authorized invoice or receipt.</AlertDescription>
          </Alert>
        </template>

        <template v-else-if="view === 'expenses'">
          <div class="grid gap-4 sm:grid-cols-2">
            <div v-if="categories.length" class="grid gap-2">
              <Label>Category</Label>
              <Select v-model="form.category_public_id">
                <SelectTrigger><SelectValue placeholder="Choose a category" /></SelectTrigger>
                <SelectContent><SelectItem v-for="category in categories" :key="category.public_id" :value="category.public_id">{{ category.name }}</SelectItem></SelectContent>
              </Select>
            </div>
            <div v-else class="grid gap-2">
              <Label for="expense-category-name">New category</Label>
              <Input id="expense-category-name" v-model.trim="form.category_name" placeholder="Utilities" />
            </div>
            <div class="grid gap-2">
              <Label>Supplier</Label>
              <Select v-model="form.supplier_public_id">
                <SelectTrigger><SelectValue placeholder="Optional supplier" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No supplier</SelectItem>
                  <SelectItem v-for="supplier in suppliers" :key="supplier.public_id" :value="supplier.public_id">{{ supplier.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <Label for="expense-description">Description</Label>
              <Input id="expense-description" v-model.trim="form.description" />
            </div>
            <div class="grid gap-2">
              <Label for="expense-amount">Amount</Label>
              <Input id="expense-amount" v-model="form.amount" type="number" min="0.01" step="0.01" />
            </div>
            <div class="grid gap-2">
              <div class="flex items-center gap-1.5">
                <Label for="expense-tax">Tax amount</Label>
                <OperationsFieldHelp text="The tax portion already included in the recorded expense amount. Enter zero when no tax applies." />
              </div>
              <Input id="expense-tax" v-model="form.tax_amount" type="number" min="0" step="0.01" />
            </div>
            <div class="grid gap-2">
              <Label for="expense-date">Incurred on</Label>
              <Input id="expense-date" v-model="form.incurred_at" type="date" />
            </div>
            <div class="grid gap-2">
              <Label for="expense-method">Payment method</Label>
              <Input id="expense-method" v-model.trim="form.payment_method" placeholder="Cash, card, transfer" />
            </div>
            <div class="grid gap-2 sm:col-span-2">
              <div class="flex items-center gap-1.5">
                <Label for="expense-reference">Reference</Label>
                <OperationsFieldHelp text="A receipt number, bank transaction ID, or supplier document number that makes the payment traceable." />
              </div>
              <Input id="expense-reference" v-model.trim="form.reference" />
            </div>
            <div class="rounded-xl border bg-muted/20 p-4 sm:col-span-2">
              <div class="flex items-start gap-3">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-background text-primary ring-1 ring-border">
                  <Paperclip class="h-5 w-5" aria-hidden="true" />
                </span>
                <div class="min-w-0 flex-1 space-y-2">
                  <div>
                    <Label for="expense-receipt">Attach receipt</Label>
                    <p class="mt-1 text-xs text-muted-foreground">Upload a JPG, PNG, WebP, or PDF. Images may be up to 8 MB and PDFs up to 10 MB.</p>
                  </div>
                  <Input
                    id="expense-receipt"
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/avif,application/pdf"
                    @change="handleExpenseReceipt"
                  />
                  <p v-if="form.receipt_file" class="truncate text-xs font-medium">Selected: {{ form.receipt_file.name }}</p>
                </div>
              </div>
            </div>
          </div>
        </template>

        <p v-if="error" class="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive" role="alert">{{ error }}</p>
      </form>

      <DialogFooter class="shrink-0 border-t bg-background px-6 py-4">
        <Button type="button" variant="outline" :disabled="saving" @click="emit('update:open', false)">Cancel</Button>
        <Button form="operations-create-form" type="submit" :disabled="saving || !canSubmit">
          <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
          {{ saving ? 'Saving…' : dialogMeta.action }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { Boxes, Building2, FileText, Info, Loader2, PackagePlus, Paperclip, ReceiptText, ShoppingCart } from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import DocumentLineFields from '@/components/operations/DocumentLineFields.vue'
import OperationsFieldHelp from '@/components/operations/OperationsFieldHelp.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  view: { type: String, required: true },
  businessId: { type: String, required: true },
  inventory: { type: Array, default: () => [] },
  suppliers: { type: Array, default: () => [] },
  locations: { type: Array, default: () => [] },
  customers: { type: Array, default: () => [] },
  variants: { type: Array, default: () => [] },
  categories: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:open', 'created', 'closed'])
const { apiFetch } = useApiClient()
const saving = ref(false)
const error = ref('')
const form = reactive(defaultForm())

const dialogMeta = computed(() => ({
  inventory: { title: 'Update inventory', description: 'Add a stock location or record an audited quantity adjustment.', action: 'Save inventory', icon: Boxes },
  suppliers: { title: 'Add supplier', description: 'Create a purchasing contact for orders and expenses.', action: 'Add supplier', icon: Building2 },
  'purchase-orders': { title: 'Create purchase order', description: 'Start a supplier order with its first product line.', action: 'Create order', icon: ShoppingCart },
  quotations: { title: 'Create quotation', description: 'Prepare an operational quote for an existing customer.', action: 'Create quotation', icon: FileText },
  invoices: { title: 'Create invoice', description: 'Issue an operational commercial document for an existing customer.', action: 'Create invoice', icon: ReceiptText },
  expenses: { title: 'Record expense', description: 'Capture an incurred business cost for operating reports.', action: 'Record expense', icon: PackagePlus },
}[props.view] || { title: 'Create record', description: 'Add an operations record.', action: 'Save', icon: FileText }))

const canSubmit = computed(() => {
  if (props.view === 'inventory') {
    return form.inventory_mode === 'adjust'
      ? Boolean(form.balance_public_id && Number(form.quantity_delta) !== 0)
      : Boolean(form.variant_public_id && form.location_public_id)
  }
  if (props.view === 'suppliers') return Boolean(form.name)
  if (props.view === 'purchase-orders') return Boolean(form.supplier_public_id && form.location_public_id && form.variant_public_id && Number(form.quantity) > 0 && Number(form.unit_amount) >= 0)
  if (['quotations', 'invoices'].includes(props.view)) return Boolean(form.customer_public_id && form.description && Number(form.quantity) > 0 && Number(form.unit_amount) >= 0)
  if (props.view === 'expenses') return Boolean((form.category_public_id || form.category_name) && form.description && Number(form.amount) > 0 && form.incurred_at)
  return false
})

watch(() => [props.open, props.view], ([open]) => {
  if (!open) return
  Object.assign(form, defaultForm())
  form.inventory_mode = props.inventory.length ? 'adjust' : 'new'
  form.balance_public_id = props.inventory[0]?.public_id || ''
  form.supplier_public_id = props.suppliers[0]?.public_id || 'none'
  form.location_public_id = props.locations[0]?.public_id || ''
  form.customer_public_id = props.customers[0]?.public_id || ''
  form.variant_public_id = props.variants[0]?.public_id || ''
  form.category_public_id = props.categories[0]?.public_id || ''
  error.value = ''
})

function handleOpenChange(value) {
  if (!saving.value) emit('update:open', value)
}

async function submit() {
  if (saving.value || !canSubmit.value) return
  saving.value = true
  error.value = ''
  try {
    const created = await createRecord()
    emit('created', created)
    emit('update:open', false)
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || requestError?.data?.detail || 'The record could not be saved.'
  } finally {
    saving.value = false
  }
}

async function createRecord() {
  const base = `businesses/${props.businessId}`
  if (props.view === 'inventory') {
    let balanceId = form.balance_public_id
    if (form.inventory_mode === 'new') {
      const balance = await apiFetch(`${base}/inventory/`, {
        method: 'POST',
        body: {
          variant_public_id: form.variant_public_id,
          location_public_id: form.location_public_id,
          low_stock_threshold: form.low_stock_threshold || '0',
          reorder_quantity: form.reorder_quantity || '0',
          target_stock_level: form.target_stock_level || '0',
          bin_location: form.bin_location,
          preferred_supplier_public_id: form.preferred_supplier_public_id === 'none' ? null : form.preferred_supplier_public_id,
        },
      })
      balanceId = balance.public_id
    }
    if (Number(form.quantity_delta) !== 0) {
      await apiFetch(`${base}/inventory/${balanceId}/adjust/`, {
        method: 'POST',
        body: { quantity_delta: form.quantity_delta, note: form.note },
      })
    }
    return apiFetch(`${base}/inventory/${balanceId}/`)
  }
  if (props.view === 'suppliers') {
    const imagePublicId = await uploadSupplierImage()
    return apiFetch(`${base}/suppliers/`, {
      method: 'POST',
      body: {
        name: form.name,
        code: form.code,
        category: form.category,
        image_public_id: imagePublicId,
        contact_name: form.contact_name,
        email: form.email,
        phone: form.phone,
        website: form.website,
        address: form.address,
        tax_id: form.tax_id,
        account_reference: form.account_reference,
        payment_terms_days: form.payment_terms_days || 0,
        lead_time_days: form.lead_time_days || 0,
        notes: form.notes,
        is_active: true,
      },
    })
  }
  if (props.view === 'purchase-orders') {
    return apiFetch(`${base}/purchase-orders/`, {
      method: 'POST',
      body: {
        supplier_public_id: form.supplier_public_id,
        location_public_id: form.location_public_id,
        status: 'draft',
        ordered_at: form.ordered_at || null,
        expected_at: form.expected_at || null,
        supplier_reference: form.supplier_reference,
        shipping_method: form.shipping_method,
        shipping_address: form.shipping_address,
        notes: form.notes,
        lines: [{
          variant_public_id: form.variant_public_id,
          description: form.description || selectedVariantLabel(),
          quantity_ordered: form.quantity,
          unit_cost: form.unit_amount,
        }],
      },
    })
  }
  if (props.view === 'quotations') {
    return apiFetch(`${base}/quotations/`, {
      method: 'POST',
      body: {
        customer_public_id: form.customer_public_id,
        status: 'draft',
        expires_at: form.expires_at ? new Date(`${form.expires_at}T23:59:59`).toISOString() : null,
        notes: form.notes,
        lines: commercialLines(),
      },
    })
  }
  if (props.view === 'invoices') {
    return apiFetch(`${base}/invoices/`, {
      method: 'POST',
      body: {
        customer_public_id: form.customer_public_id,
        order_public_id: null,
        status: 'draft',
        issued_at: form.issued_at || null,
        due_at: form.due_at || null,
        notes: form.notes,
        lines: commercialLines(),
      },
    })
  }
  let categoryId = form.category_public_id
  if (!categoryId) {
    const category = await apiFetch(`${base}/expense-categories/`, {
      method: 'POST',
      body: { name: form.category_name, is_active: true },
    })
    categoryId = category.public_id
  }
  const receiptPublicId = await uploadExpenseReceipt()
  return apiFetch(`${base}/expenses/`, {
    method: 'POST',
    body: {
      category_public_id: categoryId,
      supplier_public_id: form.supplier_public_id === 'none' ? null : form.supplier_public_id,
      receipt_public_id: receiptPublicId,
      description: form.description,
      amount: form.amount,
      tax_amount: form.tax_amount || '0.00',
      incurred_at: form.incurred_at,
      payment_method: form.payment_method,
      reference: form.reference,
    },
  })
}

async function uploadSupplierImage() {
  if (!form.image_file) return null
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
  if (!form.receipt_file) return null
  const body = new FormData()
  body.append('title', form.receipt_file.name)
  body.append('asset_type', form.receipt_file.type === 'application/pdf' ? 'document' : 'image')
  body.append('file', form.receipt_file)
  const asset = await apiFetch(`businesses/${props.businessId}/assets/`, { method: 'POST', body })
  return asset.public_id
}

function commercialLines() {
  return [{ description: form.description, quantity: form.quantity, unit_price: form.unit_amount, tax_rate: form.tax_rate || '0' }]
}

function selectedVariantLabel() {
  return props.variants.find(variant => variant.public_id === form.variant_public_id)?.label || 'Purchased item'
}

function customerLabel(customer) {
  return `${customer.first_name || ''} ${customer.last_name || ''}`.trim() || customer.email
}

function defaultForm() {
  const today = new Date().toISOString().slice(0, 10)
  return {
    inventory_mode: 'adjust', balance_public_id: '', variant_public_id: '', location_public_id: '', low_stock_threshold: '0', reorder_quantity: '0', target_stock_level: '0', bin_location: '', preferred_supplier_public_id: 'none', quantity_delta: '0', note: '',
    name: '', code: '', category: 'distributor', image_file: null, contact_name: '', email: '', phone: '', website: '', address: '', tax_id: '', account_reference: '', payment_terms_days: '0', lead_time_days: '0', notes: '', is_active: true,
    supplier_public_id: 'none', ordered_at: today, expected_at: '', supplier_reference: '', shipping_method: '', shipping_address: '', customer_public_id: '', expires_at: '', issued_at: today, due_at: '',
    description: '', quantity: '1', unit_amount: '0.00', tax_rate: '0',
    category_public_id: '', category_name: 'Utilities', amount: '', tax_amount: '0.00', incurred_at: today, payment_method: '', reference: '', receipt_file: null,
  }
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
