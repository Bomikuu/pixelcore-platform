<template>
  <div :role="kind === 'error' ? 'alert' : undefined" :aria-live="kind === 'loading' ? 'polite' : undefined" class="border-y bg-card px-5 py-10 text-center">
    <LoaderCircle v-if="kind === 'loading'" class="mx-auto h-6 w-6 animate-spin text-primary" aria-hidden="true" />
    <component :is="icon" v-else class="mx-auto h-7 w-7 text-muted-foreground" aria-hidden="true" />
    <h2 class="mt-4 font-bold">{{ title }}</h2>
    <p class="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted-foreground">{{ message }}</p>
    <div v-if="$slots.default" class="mt-5"><slot /></div>
  </div>
</template>

<script setup>
import { AlertCircle, Inbox, LoaderCircle } from 'lucide-vue-next'

const props = defineProps({
  kind: { type: String, default: 'empty' },
  title: { type: String, required: true },
  message: { type: String, required: true },
})
const icon = computed(() => props.kind === 'error' ? AlertCircle : Inbox)
</script>

