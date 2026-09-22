<template>
  <div class="flex min-h-20 items-start justify-between gap-4 rounded-lg border bg-background p-3">
    <div>
      <Label :for="controlId" class="font-semibold">{{ label }}</Label>
      <p class="mt-1 text-xs leading-5 text-muted-foreground">{{ description }}</p>
    </div>
    <Switch :id="controlId" v-model:checked="model" class="mt-0.5 shrink-0" />
  </div>
</template>

<script setup>
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

const props = defineProps({
  label: { type: String, required: true },
  description: { type: String, required: true },
})

const model = defineModel({ type: Boolean, default: false })
const controlId = computed(() => `setting-${props.label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`)
</script>
