<script setup>
import { cn } from '@/lib/utils';

defineOptions({ inheritAttrs: false });

const props = defineProps({
  defaultValue: { type: [String, Number], required: false },
  modelValue: { type: [String, Number], required: false },
  modelModifiers: { type: Object, default: () => ({}) },
  class: { type: null, required: false },
});

const emits = defineEmits(['update:modelValue', 'input']);
const attrs = useAttrs();
const internalValue = ref(props.modelValue ?? props.defaultValue ?? '');

watch(() => props.modelValue, (value) => {
  if (value !== undefined) internalValue.value = value;
});

const inputValue = computed(() => props.modelValue ?? internalValue.value);

function normalizeValue(value) {
  if (props.modelModifiers.trim && typeof value === 'string') return value.trim();
  if (props.modelModifiers.number && value !== '') {
    const numberValue = Number(value);
    if (!Number.isNaN(numberValue)) return numberValue;
  }
  return value;
}

function handleInput(event) {
  if (attrs.type !== 'file') {
    const value = normalizeValue(event.target.value);
    internalValue.value = value;
    emits('update:modelValue', value);
  }
  emits('input', event);
}
</script>

<template>
  <input
    v-bind="$attrs"
    :value="$attrs.type === 'file' ? undefined : inputValue"
    :class="
      cn(
        'flex h-11 w-full rounded-[var(--input-radius,var(--radius))] border-[length:var(--business-border-width,1px)] border-input bg-background px-3 py-2 text-sm shadow-[var(--surface-shadow)] transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
        props.class,
      )
    "
    @input="handleInput"
  />
</template>
