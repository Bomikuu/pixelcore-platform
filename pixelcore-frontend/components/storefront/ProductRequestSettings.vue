<template>
  <section class="rounded-xl border bg-card p-5 sm:p-6">
    <div class="flex items-center gap-3"><PackageCheck class="h-5 w-5 text-primary" /><h2 class="font-bold">Reservations & rentals</h2></div>
    <p class="mt-2 text-sm leading-6 text-muted-foreground">Offer a stock hold, an approval-based rental, or both. Normal purchases stay available.</p>
    <p v-if="!eligible" class="mt-4 rounded-lg bg-muted p-3 text-sm">Choose a physical product and enable inventory tracking first. Add an active variant and stock at a business location before accepting requests.</p>
    <div class="mt-5 divide-y">
      <div v-for="mode in modes" :key="mode.key" class="py-5 first:pt-0 last:pb-0">
        <label class="flex items-start justify-between gap-5"><span><strong class="block text-sm">{{ mode.label }}</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">{{ mode.description }}</span></span><Switch v-model:checked="profile[`${mode.key}_enabled`]" :disabled="!eligible" :aria-label="mode.label" /></label>
        <label v-if="profile[`${mode.key}_enabled`]" class="mt-4 block"><span class="field-label">{{ mode.label }} — customer information</span><Textarea v-model="profile[`${mode.key}_terms`]" maxlength="2000" :placeholder="mode.placeholder" /><span class="mt-2 block text-xs leading-5 text-muted-foreground">Shown on the product page and in the confirmation dialog. Use plain text.</span></label>
      </div>
    </div>
    <p class="mt-5 border-t pt-4 text-xs leading-5 text-muted-foreground">These options also need to be enabled in <NuxtLink to="/settings/commerce" class="font-bold text-primary underline underline-offset-4">business request settings</NuxtLink>. Saving product changes does not enable a business-wide mode.</p>
  </section>
</template>
<script setup>
import { PackageCheck } from 'lucide-vue-next'
defineProps({ profile: { type: Object, required: true }, eligible: Boolean })
const modes = [
  { key: 'reservation', label: 'Reserve for pickup', description: 'Hold available stock until the business deadline. No online payment.', placeholder: 'Where to collect, what to bring, and any pickup conditions.' },
  { key: 'rental', label: 'Request a rental', description: 'A date-range request for staff approval, not an instant booking.', placeholder: 'Explain rental pricing, deposit, collection, return conditions, and what staff will confirm.' },
]
</script>
