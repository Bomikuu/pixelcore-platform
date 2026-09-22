<template>
  <TooltipProvider :delay-duration="150">
    <Tooltip :open="open">
      <TooltipTrigger as-child>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          class="h-9 w-9 rounded-lg border"
          :class="buttonClass"
          :aria-label="tooltipLabel"
          @pointerenter="showTooltip"
          @pointerleave="hideTooltip"
          @focus="showTooltip"
          @blur="closeTooltip"
          @click.stop="toggleTooltip"
          @keydown.stop
        >
          <component :is="icon" class="h-4 w-4" aria-hidden="true" />
        </Button>
      </TooltipTrigger>
      <TooltipContent side="top" class="max-w-64 px-3 py-2" @escape-key-down="closeTooltip">
        <p class="font-semibold">{{ fallbackLabel }}</p>
        <p v-if="message" class="mt-1 leading-5 opacity-80">{{ message }}</p>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
</template>

<script setup>
import { AlertTriangle, CircleCheck, CircleDashed, CircleX, Wrench } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

const props = defineProps({
  status: { type: String, default: 'clear' },
  message: { type: String, default: '' },
})
const styles = {
  critical: { icon: CircleX, label: 'Needs attention', class: 'border-destructive/35 bg-destructive/10 text-destructive hover:bg-destructive/15 hover:text-destructive' },
  warning: { icon: AlertTriangle, label: 'Review soon', class: 'border-amber-500/40 bg-amber-500/10 text-amber-800 hover:bg-amber-500/15 hover:text-amber-900 dark:text-amber-300' },
  setup: { icon: Wrench, label: 'Setup needed', class: 'border-sky-500/40 bg-sky-500/10 text-sky-800 hover:bg-sky-500/15 hover:text-sky-900 dark:text-sky-300' },
  muted: { icon: CircleDashed, label: 'Inactive', class: 'border-border bg-muted text-muted-foreground hover:bg-muted' },
  clear: { icon: CircleCheck, label: 'Up to date', class: 'border-emerald-500/35 bg-emerald-500/10 text-emerald-800 hover:bg-emerald-500/15 hover:text-emerald-900 dark:text-emerald-300' },
}
const open = ref(false)
const pinned = ref(false)
const current = computed(() => styles[props.status] || styles.clear)
const icon = computed(() => current.value.icon)
const buttonClass = computed(() => current.value.class)
const fallbackLabel = computed(() => current.value.label)
const tooltipLabel = computed(() => props.message ? `${fallbackLabel.value}: ${props.message}` : fallbackLabel.value)

function showTooltip() {
  open.value = true
}

function hideTooltip() {
  if (!pinned.value) open.value = false
}

function toggleTooltip() {
  pinned.value = !pinned.value
  open.value = pinned.value
}

function closeTooltip() {
  pinned.value = false
  open.value = false
}
</script>
