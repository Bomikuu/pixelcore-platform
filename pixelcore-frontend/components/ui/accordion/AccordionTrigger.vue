<script setup>
import { computed } from 'vue'
import { ChevronDown } from 'lucide-vue-next'
import { AccordionHeader, AccordionTrigger, useForwardProps } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps({
  disabled: { type: Boolean, required: false },
  asChild: { type: Boolean, required: false },
  as: { type: null, required: false },
  class: { type: null, required: false },
})

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props
  return delegated
})
const forwardedProps = useForwardProps(delegatedProps)
</script>

<template>
  <AccordionHeader class="flex">
    <AccordionTrigger
      v-bind="forwardedProps"
      :class="cn('flex flex-1 items-center justify-between py-4 text-left font-medium transition-all hover:underline [&[data-state=open]>svg]:rotate-180', props.class)"
    >
      <slot />
      <ChevronDown class="h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200" />
    </AccordionTrigger>
  </AccordionHeader>
</template>
