<script setup>
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: [String, Number, Boolean], default: '' },
  value: { type: [String, Number, Boolean], required: true },
  class: { type: null, default: undefined },
})

const emit = defineEmits(['update:modelValue', 'change'])

function handleChange(event) {
  if (event.target.checked) emit('update:modelValue', props.value)
  emit('change', event)
}
</script>

<template>
  <input
    v-bind="$attrs"
    type="radio"
    :value="value"
    :checked="modelValue === value"
    :class="cn('h-4 w-4 shrink-0 rounded-full border border-primary accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', props.class)"
    @change="handleChange"
  />
</template>
