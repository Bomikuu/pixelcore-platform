<script setup>
import { Button } from '@/components/ui/button'

defineOptions({ inheritAttrs: false })

defineProps({
  variant: { type: null, default: 'default' },
  size: { type: null, default: 'default' },
  class: { type: null, default: undefined },
})
</script>

<template>
  <Button as-child :variant="variant" :size="size" :class="$props.class">
    <NuxtLink v-bind="$attrs"><slot /></NuxtLink>
  </Button>
</template>
