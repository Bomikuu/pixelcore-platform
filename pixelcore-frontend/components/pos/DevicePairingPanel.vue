<template>
  <section
    class="grid min-h-dvh bg-background lg:grid-cols-[minmax(0,1.05fr)_minmax(28rem,.95fr)]"
  >
    <div
      class="relative isolate flex min-h-[24rem] flex-col overflow-hidden bg-[var(--brand-secondary)] px-6 py-8 text-white sm:px-10 lg:min-h-dvh lg:px-14 lg:py-12"
    >
      <div
        class="absolute right-10 top-10 -z-10 grid grid-cols-2 gap-2 opacity-20"
        aria-hidden="true"
      >
        <span class="h-16 w-16 rounded-lg bg-[var(--brand-accent)]" /><span
          class="h-16 w-16 rounded-lg bg-white"
        /><span class="h-16 w-16 rounded-lg bg-white" /><span
          class="h-16 w-16 rounded-lg bg-[var(--brand-accent)]"
        />
      </div>
      <PixelCoreMark />
      <div class="my-auto max-w-xl py-12">
        <div class="grid h-12 w-12 place-items-center rounded-xl bg-white/10">
          <component
            :is="icon"
            class="h-6 w-6 text-[var(--brand-accent)]"
            aria-hidden="true"
          />
        </div>
        <h1
          class="mt-6 text-4xl font-extrabold leading-tight tracking-[-0.03em] sm:text-5xl"
        >
          {{ title }}
        </h1>
        <p class="mt-4 max-w-lg text-base leading-7 text-white/70">
          {{ description }}
        </p>
        <ul class="mt-8 space-y-4" aria-label="Screen details">
          <li
            v-for="detail in details"
            :key="detail"
            class="flex items-start gap-3 text-sm leading-6 text-white/80"
          >
            <CheckCircle2
              class="mt-0.5 h-5 w-5 shrink-0 text-[var(--brand-accent)]"
              aria-hidden="true"
            /><span>{{ detail }}</span>
          </li>
        </ul>
      </div>
      <p class="text-xs text-white/50">
        Secure device session · {{ audience }}
      </p>
    </div>
    <div class="flex items-center justify-center px-6 py-12 sm:px-10 lg:px-14">
      <form class="w-full max-w-md" @submit.prevent="$emit('submit')">
        <h2 class="text-2xl font-extrabold tracking-[-0.02em]">
          Enter the pairing code
        </h2>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">
          Generate a one-time code from {{ setupSource }}, then enter all eight
          characters below.
        </p>
        <div class="mt-8 rounded-xl border bg-card p-5 shadow-sm">
          <p class="field-label">One-time setup code</p>
          <CodeInput
            v-model="codeModel"
            class="mt-3"
            :disabled="working"
            :label="`${title} setup code`"
            @complete="$emit('submit')"
          />
          <p class="mt-3 text-xs leading-5 text-muted-foreground">
            You can type each character or paste the complete code. The code
            expires after it is used.
          </p>
        </div>
        <p
          v-if="message"
          class="mt-4 rounded-lg bg-destructive/10 px-4 py-3 text-sm font-semibold text-destructive"
          role="alert"
        >
          {{ message }}
        </p>
        <Button
          class="mt-5 h-12 w-full"
          :disabled="working || modelValue.length !== 8"
          >{{ working ? "Connecting…" : actionLabel }}</Button
        >
        <p class="mt-5 text-center text-xs text-muted-foreground">
          This screen never receives workspace credentials or unrelated business
          data.
        </p>
      </form>
    </div>
  </section>
</template>

<script setup>
import { CheckCircle2, MonitorSmartphone } from "lucide-vue-next";
const props = defineProps({
  modelValue: { type: String, default: "" },
  title: { type: String, required: true },
  description: { type: String, required: true },
  details: { type: Array, default: () => [] },
  audience: { type: String, default: "Dedicated business screen" },
  actionLabel: { type: String, default: "Pair screen" },
  setupSource: { type: String, default: "Sell → POS" },
  working: { type: Boolean, default: false },
  message: { type: String, default: "" },
  icon: { type: [Object, Function], default: () => MonitorSmartphone },
});
const emit = defineEmits(["update:modelValue", "submit"]);
const codeModel = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});
</script>
