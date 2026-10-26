<template>
  <div v-if="configured" class="fixed bottom-4 left-4 z-40 max-w-sm rounded-xl border bg-background p-4 text-foreground shadow-lg" role="region" aria-label="Website analytics preferences">
    <template v-if="choice === 'unset' || editing">
      <p class="text-sm font-semibold">Help us understand visits</p>
      <p class="mt-2 text-sm text-muted-foreground">Allow optional {{ providerLabel }} analytics for this business? Your choice applies to its website pages and events. You can change it here at any time.</p>
      <div class="mt-4 flex flex-wrap gap-2">
        <Button variant="outline" size="sm" @click="select('denied')">Decline</Button>
        <Button size="sm" @click="select('allowed')">Allow analytics</Button>
      </div>
    </template>
    <Button v-else variant="ghost" size="sm" @click="editing = true">Analytics: {{ choice === 'allowed' ? 'allowed' : 'off' }} · change</Button>
  </div>
</template>
<script setup>
import { Button } from '@/components/ui/button'
const props = defineProps({ choice: { type: String, default: 'unset' }, config: { type: Object, default: () => ({}) } })
const emit = defineEmits(['choose'])
const editing = ref(false)
const configured = computed(() => ['google', 'plausible'].includes(props.config.provider))
const providerLabel = computed(() => props.config.provider === 'google' ? 'Google Analytics' : 'Plausible')
function select(value) { emit('choose', value); editing.value = false }
</script>
