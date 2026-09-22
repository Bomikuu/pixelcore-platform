<template><span class="status-pill" :class="tone">{{ normalized }}</span></template>

<script setup>
const props = defineProps({ value: { type: String, default: '' } })
const normalized = computed(() => props.value.replaceAll('_', ' '))
const tone = computed(() => {
  if (['active', 'published', 'paid', 'confirmed', 'fulfilled', 'received', 'accepted', 'completed'].includes(props.value)) return 'border-primary/25 bg-secondary text-foreground'
  if (['cancelled', 'failed', 'void', 'expired', 'archived'].includes(props.value)) return 'border-destructive/25 bg-destructive/5 text-destructive'
  return 'bg-muted text-muted-foreground'
})
</script>

