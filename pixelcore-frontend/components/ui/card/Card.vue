<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
  class: { type: null, required: false },
});
</script>

<template>
  <div
    :class="
      cn('rounded-[var(--card-radius,var(--radius))] border-[length:var(--business-border-width,1px)] bg-card text-card-foreground shadow-[var(--surface-shadow)]', props.class)
    "
  >
    <slot />
  </div>
</template>
