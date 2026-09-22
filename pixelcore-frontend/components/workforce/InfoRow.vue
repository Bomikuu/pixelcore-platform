<template>
  <div class="flex items-start gap-3 rounded-lg border bg-muted/20 p-3">
    <component :is="icon" class="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
    <div class="min-w-0">
      <p class="text-xs text-muted-foreground">{{ label }}</p>
      <p class="mt-1 break-words text-sm font-bold">{{ value }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: [Object, Function], required: true },
});
</script>
