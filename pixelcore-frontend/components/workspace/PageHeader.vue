<template>
  <header class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
    <div>
      <h1 class="text-3xl font-extrabold tracking-[-0.025em]">{{ title }}</h1>
      <p v-if="description" class="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2"><slot name="actions" /></div>
  </header>
</template>

<script setup>
defineProps({ title: { type: String, required: true }, description: { type: String, default: '' } })
</script>
