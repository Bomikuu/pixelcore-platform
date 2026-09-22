<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-xl">
      <DialogHeader>
        <DialogTitle>Add supplied product</DialogTitle>
        <DialogDescription>Connect a catalog variant to this supplier for purchasing and replenishment.</DialogDescription>
      </DialogHeader>

      <form id="supplier-product-form" class="grid gap-4 sm:grid-cols-2" @submit.prevent="submit">
        <div class="grid gap-2 sm:col-span-2">
          <Label>Product variant</Label>
          <Select v-model="form.variant_public_id">
            <SelectTrigger><SelectValue placeholder="Choose a product variant" /></SelectTrigger>
            <SelectContent><SelectItem v-for="variant in variants" :key="variant.public_id" :value="variant.public_id">{{ variant.label }}</SelectItem></SelectContent>
          </Select>
        </div>
        <div class="grid gap-2">
          <Label for="supplier-sku">Supplier SKU</Label>
          <Input id="supplier-sku" v-model.trim="form.supplier_sku" />
        </div>
        <div class="grid gap-2">
          <Label for="supplier-product-name">Supplier product name</Label>
          <Input id="supplier-product-name" v-model.trim="form.supplier_product_name" />
        </div>
        <div class="grid gap-2">
          <div class="flex items-center gap-1.5"><Label for="supplier-unit-cost">Latest unit cost</Label><OperationsFieldHelp text="The most recent price quoted or paid for one unit from this supplier." /></div>
          <Input id="supplier-unit-cost" v-model="form.last_unit_cost" type="number" min="0" step="0.01" />
        </div>
        <div class="grid gap-2">
          <div class="flex items-center gap-1.5"><Label for="supplier-minimum">Minimum order quantity</Label><OperationsFieldHelp text="The smallest quantity this supplier accepts in one purchase order." /></div>
          <Input id="supplier-minimum" v-model="form.minimum_order_quantity" type="number" min="0.001" step="0.001" />
        </div>
        <div class="grid gap-2 sm:col-span-2 sm:max-w-xs">
          <div class="flex items-center gap-1.5"><Label for="supplier-lead-time">Lead time in days</Label><OperationsFieldHelp text="The expected delivery time for this specific product. It overrides the supplier's general lead time when provided." /></div>
          <Input id="supplier-lead-time" v-model="form.lead_time_days" type="number" min="0" max="365" />
        </div>
        <div class="grid gap-2 sm:col-span-2">
          <Label for="supplier-product-notes">Notes</Label>
          <Textarea id="supplier-product-notes" v-model.trim="form.notes" rows="3" placeholder="Pack size, ordering instructions, substitutions, or contact details" />
        </div>
        <p v-if="error" class="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive sm:col-span-2" role="alert">{{ error }}</p>
      </form>

      <DialogFooter>
        <Button type="button" variant="outline" @click="emit('update:open', false)">Cancel</Button>
        <Button form="supplier-product-form" type="submit" :disabled="saving || !canSubmit">
          <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
          {{ saving ? 'Connecting…' : 'Add product' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { Loader2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import OperationsFieldHelp from '@/components/operations/OperationsFieldHelp.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  businessId: { type: String, required: true },
  supplierId: { type: String, required: true },
  variants: { type: Array, default: () => [] },
  defaultLeadTime: { type: Number, default: 0 },
})
const emit = defineEmits(['update:open', 'created'])
const { apiFetch } = useApiClient()
const form = reactive(defaultForm())
const saving = ref(false)
const error = ref('')
const canSubmit = computed(() => Boolean(form.variant_public_id && Number(form.minimum_order_quantity) > 0))

watch(() => props.open, open => {
  if (!open) return
  Object.assign(form, defaultForm())
  form.lead_time_days = String(props.defaultLeadTime || 0)
  error.value = ''
})

async function submit() {
  saving.value = true
  error.value = ''
  try {
    const created = await apiFetch(`businesses/${props.businessId}/supplier-products/`, {
      method: 'POST',
      body: {
        supplier_public_id: props.supplierId,
        variant_public_id: form.variant_public_id,
        supplier_sku: form.supplier_sku,
        supplier_product_name: form.supplier_product_name,
        last_unit_cost: form.last_unit_cost || '0',
        minimum_order_quantity: form.minimum_order_quantity,
        lead_time_days: form.lead_time_days || 0,
        is_active: true,
        notes: form.notes,
      },
    })
    emit('created', created)
    emit('update:open', false)
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || requestError?.data?.detail || 'This product could not be connected to the supplier.'
  } finally {
    saving.value = false
  }
}

function defaultForm() {
  return { variant_public_id: '', supplier_sku: '', supplier_product_name: '', last_unit_cost: '0.00', minimum_order_quantity: '1', lead_time_days: '0', notes: '' }
}
</script>
