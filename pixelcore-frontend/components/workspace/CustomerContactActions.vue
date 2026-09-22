<template>
  <div class="flex flex-wrap gap-2">
    <ButtonAnchor v-if="telephone" :href="`tel:${telephone}`" variant="outline" size="sm"><Phone class="h-4 w-4" />Call customer</ButtonAnchor>
    <ButtonAnchor v-if="email" :href="emailLink" variant="outline" size="sm"><Mail class="h-4 w-4" />Email customer</ButtonAnchor>
    <span v-if="!telephone && !email" class="text-xs text-muted-foreground">No customer contact details on this record.</span>
  </div>
</template>
<script setup>
import { Mail, Phone } from 'lucide-vue-next'
const props = defineProps({ phone: { type: String, default: '' }, email: { type: String, default: '' }, reference: { type: String, default: '' } })
const telephone = computed(() => props.phone.replace(/[^+0-9]/g, ''))
const emailLink = computed(() => `mailto:${encodeURIComponent(props.email)}?subject=${encodeURIComponent(`Regarding ${props.reference}`)}`)
</script>
