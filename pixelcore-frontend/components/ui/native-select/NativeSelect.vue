<script setup>
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: [String, Number], default: undefined },
  value: { type: [String, Number], default: undefined },
  modelModifiers: { type: Object, default: () => ({}) },
  class: { type: null, default: undefined },
})

const emit = defineEmits(['update:modelValue', 'change'])

function handleChange(event) {
  const value = props.modelModifiers.number ? Number(event.target.value) : event.target.value
  emit('update:modelValue', value)
  emit('change', event)
}
</script>

<template>
  <select
    v-bind="$attrs"
    :value="modelValue ?? value"
    :class="cn('flex h-11 w-full rounded-[var(--radius)] border border-input bg-background px-3 py-2 text-sm shadow-sm ring-offset-background focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50', props.class)"
    @change="handleChange"
  >
    <slot />
  </select>
</template>
