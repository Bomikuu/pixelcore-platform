<template>
  <div class="grid gap-2">
    <Label :for="forId">{{ label }}</Label>
    <slot />
    <p v-if="$slots.help" class="text-xs leading-5 text-muted-foreground">
      <slot name="help" />
    </p>
  </div>
</template>

<script setup>
import { Label } from '@/components/ui/label'

defineProps({
  label: { type: String, required: true },
  forId: { type: String, required: true },
})
</script>
