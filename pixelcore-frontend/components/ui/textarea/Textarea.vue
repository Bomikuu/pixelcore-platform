<script setup>
import { cn } from '@/lib/utils';

const props = defineProps({
  class: { type: null, required: false },
  defaultValue: { type: [String, Number], required: false },
  modelValue: { type: [String, Number], required: false },
  modelModifiers: { type: Object, default: () => ({}) },
});

const emits = defineEmits(['update:modelValue']);
const internalValue = ref(props.modelValue ?? props.defaultValue ?? '');

watch(() => props.modelValue, (value) => {
  if (value !== undefined) internalValue.value = value;
});

const modelValue = computed({
  get: () => props.modelValue ?? internalValue.value,
  set: (value) => {
    const normalizedValue = props.modelModifiers.trim && typeof value === 'string' ? value.trim() : value;
    internalValue.value = normalizedValue;
    emits('update:modelValue', normalizedValue);
  },
});
</script>

<template>
  <textarea
    v-model="modelValue"
    :class="
      cn(
        'flex min-h-[60px] w-full rounded-[var(--input-radius,var(--radius))] border-[length:var(--business-border-width,1px)] border-input bg-background px-3 py-2 text-sm shadow-[var(--surface-shadow)] placeholder:text-muted-foreground focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
        props.class,
      )
    "
  />
</template>
