<template>
  <section
    class="pairing-screen grid min-h-dvh bg-card text-foreground lg:grid-cols-[minmax(0,1.05fr)_minmax(0,.95fr)]"
    :data-illustration="illustration"
  >
    <div class="pairing-introduction relative isolate flex min-w-0 flex-col overflow-hidden bg-secondary/20 px-6 py-7 sm:px-10 lg:min-h-dvh lg:px-14 lg:py-12 xl:px-20 2xl:px-24">
      <div class="pairing-shapes pointer-events-none absolute inset-0 -z-20" aria-hidden="true" />
      <PixelCoreMark class="relative z-10 self-start" />

      <img
        :src="illustrationSource"
        alt=""
        class="pairing-illustration pointer-events-none absolute -z-10 select-none"
        decoding="async"
        fetchpriority="high"
      />

      <div class="pairing-copy relative z-10 my-auto py-10 lg:py-16">
        <h1 class="max-w-[11ch] text-3xl font-extrabold leading-[1.12] tracking-[-0.03em] sm:text-4xl xl:text-5xl">
          {{ title }}
        </h1>
        <p class="mt-4 text-sm leading-6 text-muted-foreground sm:text-base sm:leading-7 lg:mt-5 xl:text-lg xl:leading-8">
          {{ description }}
        </p>
        <ul class="mt-7 hidden space-y-4 lg:block" aria-label="Screen details">
          <li v-for="detail in details" :key="detail" class="flex items-start gap-4 text-sm leading-7">
            <span class="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground">
              <Check class="h-4 w-4" aria-hidden="true" />
            </span>
            <span>{{ detail }}</span>
          </li>
        </ul>
      </div>

      <p class="relative z-10 hidden items-start gap-3 text-xs leading-5 text-muted-foreground sm:flex">
        <ShieldCheck class="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
        <span>Secure device session · {{ audience }}</span>
      </p>
    </div>

    <div class="flex min-w-0 items-center justify-center px-6 py-10 sm:px-10 sm:py-14 lg:px-12 xl:px-16 2xl:px-24">
      <form class="w-full min-w-0 max-w-[552px]" novalidate :aria-busy="working" @submit.prevent="submit">
        <h2 class="text-2xl font-extrabold tracking-[-0.02em] xl:text-[1.75rem]">
          Enter the pairing code
        </h2>
        <p class="mt-3 text-sm leading-7 text-muted-foreground xl:text-base">
          Generate a one-time code from {{ setupSource }}, then enter all eight characters below.
        </p>

        <div class="pairing-code-panel mt-7 rounded-2xl bg-card p-4 ring-1 ring-border/70 sm:mt-8 sm:p-6">
          <p class="text-sm font-semibold">One-time setup code</p>
          <CodeInput
            ref="codeInput"
            v-model="codeModel"
            class="mt-4"
            input-class="h-12 w-0 min-w-0 rounded-lg bg-muted/15 font-sans text-lg font-semibold sm:h-14"
            :length="8"
            :disabled="working"
            :label="`${title} setup code`"
            :aria-invalid="!!message"
            :aria-describedby="message ? `${helpId} ${errorId}` : helpId"
            @complete="submit"
          />
          <p :id="helpId" class="mt-4 flex items-start gap-3 text-xs leading-5 text-muted-foreground xl:text-sm xl:leading-6">
            <Info class="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
            <span>You can type each character or paste the complete code. The code expires after it is used.</span>
          </p>
        </div>

        <p
          v-if="message"
          :id="errorId"
          class="mt-4 break-words rounded-lg bg-destructive/10 px-4 py-3 text-sm font-semibold text-destructive"
          role="alert"
        >
          {{ message }}
        </p>
        <Button class="mt-5 h-14 w-full gap-3 rounded-xl text-sm font-semibold xl:text-base" type="submit" :disabled="working || modelValue.length !== 8">
          <LoaderCircle v-if="working" class="h-5 w-5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
          <Link2 v-else class="h-5 w-5" aria-hidden="true" />
          {{ working ? "Connecting…" : actionLabel }}
        </Button>

        <div class="mt-5 flex items-center gap-4 rounded-xl bg-secondary/45 px-5 py-4 text-sm leading-6 text-muted-foreground">
          <LockKeyhole class="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
          <p>This screen never receives workspace credentials or unrelated business data.</p>
        </div>
      </form>
    </div>
  </section>
</template>

<script setup>
import { Check, Info, Link2, LoaderCircle, LockKeyhole, ShieldCheck } from "lucide-vue-next";

const props = defineProps({
  modelValue: { type: String, default: "" },
  title: { type: String, required: true },
  description: { type: String, required: true },
  details: { type: Array, default: () => [] },
  audience: { type: String, default: "Dedicated business screen" },
  actionLabel: { type: String, default: "Pair screen" },
  setupSource: { type: String, default: "Sell → POS" },
  illustration: {
    type: String,
    default: "pos",
    validator: (value) => ["fulfillment", "pos", "customer", "attendance"].includes(value),
  },
  working: { type: Boolean, default: false },
  message: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue", "submit"]);
const codeInput = ref(null);
const id = useId();
const helpId = `${id}-pairing-help`;
const errorId = `${id}-pairing-error`;
const illustrationSource = computed(() => `/images/pairing/${props.illustration}.png`);
const codeModel = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

async function submit() {
  // CodeInput emits its completed value before the parent's v-model has rendered.
  await nextTick();
  if (!props.working && props.modelValue.length === 8) emit("submit");
}

onMounted(() => codeInput.value?.focus());
</script>

<style scoped>
.pairing-copy {
  width: 68%;
  max-width: 27rem;
}

.pairing-illustration {
  right: -14%;
  bottom: 0;
  width: 67%;
  mask-image: linear-gradient(to right, transparent, black 20%);
}

.pairing-code-panel {
  box-shadow: 0 3px 8px -4px hsl(var(--foreground) / 0.16);
}

.pairing-shapes::before,
.pairing-shapes::after {
  position: absolute;
  right: -8%;
  top: 5%;
  width: 32%;
  height: 38%;
  border-radius: 5rem 0 0 2rem;
  background: hsl(var(--primary) / 0.045);
  content: "";
}

.pairing-shapes::after {
  top: 22%;
  right: 11%;
  width: 21%;
  height: 22%;
  border-radius: 2.5rem;
}

@media (min-width: 1024px) {
  .pairing-copy {
    width: 65%;
  }

  .pairing-copy ul {
    max-width: 18rem;
  }

  .pairing-illustration {
    right: -10%;
    bottom: 9%;
    width: 72%;
    mask-image: linear-gradient(to right, transparent, black 28%);
  }
}

@media (min-width: 1280px) {
  .pairing-illustration {
    right: -1%;
    width: 90%;
  }

  .pairing-screen[data-illustration="fulfillment"] .pairing-illustration {
    right: 0;
    width: 98%;
  }

  .pairing-screen[data-illustration="customer"] .pairing-illustration {
    right: -3%;
    width: 82%;
  }

  .pairing-screen[data-illustration="attendance"] .pairing-illustration {
    right: -4%;
    width: 90%;
  }
}

@media (min-width: 1536px) {
  .pairing-copy {
    width: 62%;
  }
}
</style>
