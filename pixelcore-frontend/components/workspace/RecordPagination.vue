<template>
  <nav class="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3 text-xs text-muted-foreground" aria-label="Results pagination">
    <span>{{ count ? `${(page - 1) * size + 1}–${Math.min(page * size, count)} of ${count}` : '0 results' }}</span>
    <div class="flex flex-wrap items-center gap-2"><span>Page {{ page }} of {{ Math.max(1, Math.ceil(count / size)) }}</span><Button type="button" variant="outline" size="sm" :disabled="busy || page <= 1" @click="$emit('page', page - 1)"><ChevronLeft class="h-4 w-4" />Previous</Button><Button type="button" variant="outline" size="sm" :disabled="busy || page * size >= count" @click="$emit('page', page + 1)">Next<ChevronRight class="h-4 w-4" /></Button></div>
  </nav>
</template>
<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
defineProps({ page: { type: Number, default: 1 }, count: { type: Number, default: 0 }, size: { type: Number, default: 20 }, busy: Boolean })
defineEmits(['page'])
</script>
