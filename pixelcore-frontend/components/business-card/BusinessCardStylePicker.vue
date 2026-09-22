<template>
  <div class="grid gap-3 sm:grid-cols-2">
    <Button
      v-for="option in options"
      :key="option.value"
      type="button"
      variant="outline"
      class="h-auto min-h-24 items-start justify-start whitespace-normal p-4 text-left"
      :class="modelValue === option.value ? 'border-primary bg-primary/5 ring-1 ring-primary' : ''"
      :aria-pressed="modelValue === option.value"
      @click="$emit('update:modelValue', option.value)"
    >
      <span class="block">
        <span class="flex items-center gap-2 font-semibold">
          <component :is="option.icon" class="h-4 w-4 text-primary" aria-hidden="true" />
          {{ option.label }}
        </span>
        <span class="mt-2 block text-xs font-normal leading-5 text-muted-foreground">
          {{ option.description }}
        </span>
      </span>
    </Button>
  </div>
</template>

<script setup>
import { AlignLeft, Gem, PanelTop, Sparkles } from 'lucide-vue-next'

defineProps({
  modelValue: { type: String, required: true },
})

defineEmits(['update:modelValue'])

const options = [
  {
    value: 'signature',
    label: 'Signature',
    description: 'Deep brand color, restrained details, and a formal contact side.',
    icon: Sparkles,
  },
  {
    value: 'editorial',
    label: 'Editorial',
    description: 'Decisive typography with a high-contrast paper reverse.',
    icon: AlignLeft,
  },
  {
    value: 'studio',
    label: 'Studio',
    description: 'Bright business identity with a compact accent edge.',
    icon: PanelTop,
  },
  {
    value: 'luxury',
    label: 'Luxury',
    description: 'Dark material, metallic framing, ornamental corners, and refined type.',
    icon: Gem,
  },
]
</script>
