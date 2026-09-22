<template>
  <div class="flex flex-wrap gap-1.5" :aria-label="`Setup code ${code}`">
    <code v-for="(character, index) in code" :key="`${character}-${index}`" class="grid h-10 w-9 place-items-center rounded-md border bg-muted font-mono text-lg font-extrabold text-foreground">{{ character }}</code>
  </div>
</template>

<script setup>
defineProps({ code: { type: String, required: true } })
</script>
