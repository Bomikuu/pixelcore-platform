<template>
  <dl class="space-y-2 border-t border-black/10 pt-5 text-sm">
    <div class="flex justify-between"><dt class="text-black/55">Subtotal</dt><dd class="font-semibold tabular-nums">{{ money(order.subtotal) }}</dd></div>
    <div v-if="Number(order.discount_total)" class="flex justify-between text-emerald-700"><dt>Promotion</dt><dd class="font-semibold tabular-nums">−{{ money(order.discount_total) }}</dd></div>
    <div v-if="Number(order.tax_total)" class="flex justify-between"><dt class="text-black/55">Tax</dt><dd class="font-semibold tabular-nums">{{ money(order.tax_total) }}</dd></div>
    <div class="flex justify-between pt-2 text-3xl font-extrabold"><dt>Total</dt><dd class="tabular-nums">{{ money(order.grand_total) }}</dd></div>
  </dl>
</template>

<script setup>
const props = defineProps({ order: { type: Object, required: true } })
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.order.currency || 'PHP' }).format(Number(value || 0))
</script>
