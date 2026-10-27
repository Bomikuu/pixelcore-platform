<script setup>
import { cn } from "@/lib/utils";

defineOptions({ inheritAttrs: false });

const props = defineProps({
  modelValue: { type: String, default: "" },
  length: { type: Number, default: 8 },
  numericOnly: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  label: { type: String, default: "Setup code" },
  class: { type: null, default: undefined },
  inputClass: { type: null, default: undefined },
});
const emit = defineEmits(["update:modelValue", "complete"]);
const inputs = ref([]);
const normalized = computed(() => sanitize(props.modelValue));
const characters = computed(() =>
  Array.from(
    { length: props.length },
    (_, index) => normalized.value[index] || "",
  ),
);

defineExpose({ focus: () => inputs.value[0]?.focus() });

function sanitize(value) {
  const pattern = props.numericOnly ? /[^0-9]/g : /[^A-Z0-9]/g;
  return String(value || "")
    .toUpperCase()
    .replace(pattern, "")
    .slice(0, props.length);
}

function setValue(value, focusIndex) {
  const next = sanitize(value);
  emit("update:modelValue", next);
  if (next.length === props.length) emit("complete", next);
  nextTick(() => inputs.value[Math.min(focusIndex, props.length - 1)]?.focus());
}
function handleInput(index, event) {
  const entered = sanitize(event.target.value);
  const values = [...characters.value];
  if (entered.length > 1) {
    entered.split("").forEach((character, offset) => {
      if (index + offset < props.length) values[index + offset] = character;
    });
    setValue(values.join(""), index + entered.length);
    return;
  }
  values[index] = entered.slice(-1);
  setValue(values.join(""), entered ? index + 1 : index);
}
function handleKeydown(index, event) {
  if (event.key === "Backspace" && !characters.value[index] && index > 0) {
    const values = [...characters.value];
    values[index - 1] = "";
    setValue(values.join(""), index - 1);
  } else if (event.key === "ArrowLeft" && index > 0) {
    event.preventDefault();
    inputs.value[index - 1]?.focus();
  } else if (event.key === "ArrowRight" && index < props.length - 1) {
    event.preventDefault();
    inputs.value[index + 1]?.focus();
  }
}
function handlePaste(event) {
  event.preventDefault();
  setValue(event.clipboardData?.getData("text") || "", props.length - 1);
}
</script>

<template>
  <div
    role="group"
    :aria-label="label"
    :class="cn('flex w-full justify-between gap-1.5 sm:gap-2', props.class)"
    @paste="handlePaste"
  >
    <input
      v-for="(_, index) in characters"
      :key="index"
      :ref="
        (element) => {
          if (element) inputs[index] = element;
        }
      "
      v-bind="$attrs"
      :value="characters[index]"
      :disabled="disabled"
      :aria-label="`${label}, character ${index + 1} of ${length}`"
      :class="
        cn(
          'h-12 min-w-0 flex-1 rounded-md border border-input bg-background text-center font-mono text-lg font-extrabold uppercase shadow-sm transition-colors focus-visible:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:h-14 sm:text-xl',
          inputClass,
        )
      "
      maxlength="1"
      autocomplete="one-time-code"
      :inputmode="numericOnly ? 'numeric' : 'text'"
      :pattern="numericOnly ? '[0-9]*' : undefined"
      autocapitalize="characters"
      spellcheck="false"
      @input="handleInput(index, $event)"
      @keydown="handleKeydown(index, $event)"
      @focus="$event.target.select()"
    />
  </div>
</template>
