<template>
  <div class="relative isolate overflow-hidden bg-secondary" :class="sizeClass">
    <img v-if="image" :src="image.url" :alt="image.alt_text || name" class="h-full w-full object-cover" />
    <div v-else class="absolute inset-0 grid place-items-center" :style="fallbackStyle">
      <div class="absolute -right-5 -top-7 h-24 w-24 rounded-full bg-white/10" aria-hidden="true" />
      <div class="absolute -bottom-10 -left-8 h-28 w-28 rounded-full border border-white/15" aria-hidden="true" />
      <component :is="typeIcon" class="h-9 w-9 text-white/85" aria-hidden="true" />
      <span class="absolute bottom-3 left-3 text-[10px] font-extrabold uppercase tracking-[.14em] text-white/65">{{ typeLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { Box, CalendarClock, FileDown } from 'lucide-vue-next'
const props = defineProps({ name: { type: String, required: true }, type: { type: String, default: 'physical' }, media: { type: Array, default: () => [] }, size: { type: String, default: 'card' } })
const image = computed(() => props.media?.[0] || null)
const typeIcon = computed(() => ({ service: CalendarClock, digital: FileDown, physical: Box }[props.type] || Box))
const typeLabel = computed(() => ({ service: 'Service', digital: 'Digital', physical: 'Product' }[props.type] || 'Offering'))
const sizeClass = computed(() => props.size === 'thumb' ? 'h-12 w-12 shrink-0 rounded-lg' : 'aspect-[4/3] w-full')
const fallbackStyle = computed(() => ({ backgroundColor: 'var(--brand-primary)' }))
</script>
