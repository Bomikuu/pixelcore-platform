<template>
  <div class="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
    <span role="status">{{ stale ? 'Update failed · showing last data' : busy ? 'Refreshing…' : updatedAt ? `Updated ${time}` : 'Waiting for data' }}</span>
    <label class="flex items-center gap-2"><Switch :checked="modelValue" @update:checked="$emit('update:modelValue', $event)" /><span>Auto-refresh · 30s</span></label>
    <Button type="button" variant="outline" size="sm" :disabled="busy" @click="$emit('refresh')"><RefreshCw class="h-3.5 w-3.5" />Refresh</Button>
  </div>
</template>
<script setup>
import { RefreshCw } from 'lucide-vue-next'
const props = defineProps({ modelValue: Boolean, busy: Boolean, stale: Boolean, updatedAt: { type: Date, default: null } })
defineEmits(['update:modelValue', 'refresh'])
const time = computed(() => props.updatedAt?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))
</script>
