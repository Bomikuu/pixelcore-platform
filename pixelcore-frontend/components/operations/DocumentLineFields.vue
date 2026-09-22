<template>
  <section class="rounded-xl border bg-muted/15 p-4">
    <h3 class="font-semibold">First line item</h3>
    <p class="mt-1 text-xs leading-5 text-muted-foreground">Create the document with one line. Additional document management is available from its detail page.</p>
    <div class="mt-4 grid gap-4 sm:grid-cols-2">
      <div v-if="mode === 'purchase'" class="grid gap-2 sm:col-span-2">
        <Label>Product variant</Label>
        <Select :model-value="modelValue.variant_public_id" @update:model-value="update('variant_public_id', $event)">
          <SelectTrigger><SelectValue placeholder="Choose a variant" /></SelectTrigger>
          <SelectContent><SelectItem v-for="variant in variants" :key="variant.public_id" :value="variant.public_id">{{ variant.label }}</SelectItem></SelectContent>
        </Select>
      </div>
      <div class="grid gap-2 sm:col-span-2">
        <Label for="operation-line-description">Description</Label>
        <Input id="operation-line-description" :model-value="modelValue.description" placeholder="Item or service description" @update:model-value="update('description', $event)" />
      </div>
      <div class="grid gap-2">
        <Label for="operation-line-quantity">Quantity</Label>
        <Input id="operation-line-quantity" :model-value="modelValue.quantity" type="number" min="0.001" step="0.001" @update:model-value="update('quantity', $event)" />
      </div>
      <div class="grid gap-2">
        <div class="flex items-center gap-1.5">
          <Label for="operation-line-amount">{{ mode === 'purchase' ? 'Unit cost' : 'Unit price' }}</Label>
          <OperationsFieldHelp :text="mode === 'purchase' ? 'The supplier cost for one unit. This becomes the latest known cost for this supplier-product relationship.' : 'The price for one unit before quantity is applied.'" />
        </div>
        <Input id="operation-line-amount" :model-value="modelValue.unit_amount" type="number" min="0" step="0.01" @update:model-value="update('unit_amount', $event)" />
      </div>
      <div v-if="mode !== 'purchase'" class="grid gap-2 sm:max-w-56">
        <div class="flex items-center gap-1.5">
          <Label for="operation-line-tax">Tax rate (%)</Label>
          <OperationsFieldHelp text="The percentage used to calculate the tax portion of this line. Use zero when no tax applies." />
        </div>
        <Input id="operation-line-tax" :model-value="modelValue.tax_rate" type="number" min="0" step="0.001" @update:model-value="update('tax_rate', $event)" />
      </div>
    </div>
  </section>
</template>

<script setup>
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import OperationsFieldHelp from '@/components/operations/OperationsFieldHelp.vue'

const props = defineProps({
  modelValue: { type: Object, required: true },
  mode: { type: String, default: 'commercial' },
  variants: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

function update(field, value) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}
</script>
