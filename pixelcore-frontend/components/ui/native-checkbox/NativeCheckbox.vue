<script setup>
import { cn } from '@/lib/utils'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: [Boolean, Array], default: false },
  value: { type: [String, Number, Boolean, Object], default: true },
  class: { type: null, default: undefined },
})

const emit = defineEmits(['update:modelValue', 'change'])
const checked = computed(() => Array.isArray(props.modelValue) ? props.modelValue.includes(props.value) : Boolean(props.modelValue))

function handleChange(event) {
  if (Array.isArray(props.modelValue)) {
    const nextValue = event.target.checked
      ? [...props.modelValue, props.value]
      : props.modelValue.filter((item) => item !== props.value)
    emit('update:modelValue', nextValue)
  } else {
    emit('update:modelValue', event.target.checked)
  }
  emit('change', event)
}
</script>

<template>
  <input
    v-bind="$attrs"
    type="checkbox"
    :value="value"
    :checked="checked"
    :class="cn('h-4 w-4 shrink-0 rounded border border-primary accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50', props.class)"
    @change="handleChange"
  />
</template>
