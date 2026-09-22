<script setup>
import { computed } from 'vue'
import { AccordionRoot, useForwardPropsEmits } from 'radix-vue'

const props = defineProps({
  modelValue: { type: [String, Array], required: false },
  defaultValue: { type: [String, Array], required: false },
  type: { type: String, default: 'single' },
  collapsible: { type: Boolean, default: false },
  disabled: { type: Boolean, required: false },
  dir: { type: String, required: false },
  orientation: { type: String, required: false },
  asChild: { type: Boolean, required: false },
  as: { type: null, required: false },
  class: { type: null, required: false },
})
const emits = defineEmits(['update:modelValue'])

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props
  return delegated
})
const forwarded = useForwardPropsEmits(delegatedProps, emits)
</script>

<template>
  <AccordionRoot v-bind="forwarded" :class="props.class">
    <slot />
  </AccordionRoot>
</template>
