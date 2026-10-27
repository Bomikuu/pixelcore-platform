<template>
  <Tooltip :delay-duration="180">
    <TooltipTrigger as-child>
      <div
        class="analytics-metric group relative min-w-0 rounded-xl border bg-card p-3 outline-none sm:p-5"
        tabindex="0"
        role="group"
        :aria-label="`${label}: ${value}. ${detail}`"
      >
        <div class="mb-3 flex items-center justify-between gap-3">
          <span
            class="metric-icon grid h-9 w-9 place-items-center rounded-lg bg-secondary text-primary"
          >
            <component
              :is="icon"
              class="h-[1.125rem] w-[1.125rem]"
              aria-hidden="true"
            />
          </span>
          <Info
            class="h-3.5 w-3.5 text-muted-foreground opacity-60 transition-opacity duration-200 group-hover:opacity-100 group-focus-visible:opacity-100"
            aria-hidden="true"
          />
        </div>
        <dt
          class="min-h-10 text-xs font-semibold leading-5 text-muted-foreground sm:min-h-5"
        >
          {{ label }}
        </dt>
        <dd
          class="mt-1 break-words text-base font-extrabold leading-8 tracking-tight tabular-nums min-[360px]:text-lg sm:text-[1.35rem]"
        >
          {{ value }}
        </dd>
        <div class="mt-3 flex min-h-9 items-end justify-between gap-2">
          <p class="max-w-40 text-[0.6875rem] leading-4 text-muted-foreground">
            {{ detail }}
          </p>
          <svg
            v-if="sparkline && hasActivity"
            class="metric-sparkline hidden h-9 w-16 shrink-0 text-primary sm:block"
            viewBox="0 0 80 36"
            aria-hidden="true"
          >
            <path
              :d="`${sparkline} L 78 35 L 2 35 Z`"
              fill="currentColor"
              opacity="0.09"
            />
            <path
              :d="sparkline"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </div>
    </TooltipTrigger>
    <TooltipContent
      side="bottom"
      :side-offset="8"
      class="max-w-64 text-xs leading-5 motion-reduce:animate-none"
    >
      {{ explanation }}
    </TooltipContent>
  </Tooltip>
</template>

<script setup>
import { Info } from "lucide-vue-next";

const props = defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  detail: { type: String, required: true },
  explanation: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  values: { type: Array, default: () => [] },
});
const hasActivity = computed(() =>
  props.values.some((value) => Number(value) !== 0),
);
const sparkline = computed(() => {
  if (props.values.length < 2) return "";
  const values = props.values.map((value) => Number(value) || 0);
  const minimum = Math.min(0, ...values);
  const span = Math.max(...values) - minimum || 1;
  return values
    .map(
      (value, index) =>
        `${index ? "L" : "M"} ${(2 + (index / (values.length - 1)) * 76).toFixed(2)} ${(32 - ((value - minimum) / span) * 28).toFixed(2)}`,
    )
    .join(" ");
});
</script>

<style scoped>
.analytics-metric {
  transition:
    transform 200ms cubic-bezier(0.16, 1, 0.3, 1),
    border-color 200ms ease,
    box-shadow 200ms ease,
    background-color 200ms ease;
}
.analytics-metric:focus-visible {
  outline: 2px solid hsl(var(--ring));
  outline-offset: 3px;
  border-color: hsl(var(--primary) / 0.5);
}
@media (hover: hover) {
  .analytics-metric:hover {
    transform: translateY(-3px);
    border-color: hsl(var(--primary) / 0.4);
    box-shadow: 0 10px 22px -14px hsl(var(--foreground) / 0.25);
  }
}
@media (prefers-reduced-motion: reduce) {
  .analytics-metric,
  .analytics-metric * {
    transition: none !important;
  }
  .analytics-metric:hover {
    transform: none;
  }
}
</style>
