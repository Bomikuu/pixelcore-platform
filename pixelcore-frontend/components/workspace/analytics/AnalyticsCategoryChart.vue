<template>
  <section
    class="min-w-0 rounded-xl border bg-card p-5"
    aria-labelledby="category-chart-heading"
  >
    <h2 id="category-chart-heading" class="text-sm font-extrabold">
      Sales by category
    </h2>
    <p class="mt-1 text-xs leading-5 text-muted-foreground">
      Recorded item totals · current catalog categories
    </p>
    <div
      v-if="total > 0"
      class="mt-6 flex flex-col items-center gap-6 sm:flex-row xl:flex-col 2xl:flex-row"
    >
      <div class="relative h-44 w-44 shrink-0">
        <svg
          viewBox="0 0 200 200"
          class="h-full w-full -rotate-90"
          role="img"
          :aria-label="`Category distribution of ${money(total)} in item sales`"
        >
          <circle
            cx="100"
            cy="100"
            r="78"
            fill="none"
            stroke="hsl(var(--muted))"
            stroke-width="30"
          />
          <circle
            v-for="category in segments"
            :key="category.name"
            cx="100"
            cy="100"
            r="78"
            fill="none"
            :stroke="category.color"
            stroke-width="30"
            :stroke-dasharray="`${category.fraction * circumference} ${circumference}`"
            :stroke-dashoffset="-category.offset * circumference"
          >
            <title>
              {{ category.name }}: {{ money(category.sales) }} ({{
                percent(category.fraction)
              }})
            </title>
          </circle>
        </svg>
        <div
          class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center px-8 text-center"
        >
          <strong
            class="text-lg font-extrabold tabular-nums"
            :title="money(total)"
            >{{ compactMoney(total) }}</strong
          >
          <span class="mt-1 text-[0.6875rem] text-muted-foreground"
            >Item sales</span
          >
        </div>
      </div>
      <ul class="w-full min-w-0 flex-1 space-y-3 text-xs">
        <li
          v-for="category in segments"
          :key="category.name"
          class="flex items-start gap-2"
        >
          <span
            class="mt-1 h-2.5 w-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: category.color }"
            aria-hidden="true"
          />
          <span class="min-w-0 flex-1 break-words leading-5">{{
            category.name
          }}</span>
          <span
            class="ml-1 w-9 shrink-0 text-right font-semibold tabular-nums"
            >{{ percent(category.fraction) }}</span
          >
          <strong class="w-24 shrink-0 text-right leading-5 tabular-nums">{{
            money(category.sales)
          }}</strong>
        </li>
      </ul>
    </div>
    <div
      v-else
      class="mt-6 flex min-h-52 flex-col items-center justify-center gap-3 text-center"
    >
      <div
        class="grid h-24 w-24 place-items-center rounded-full border-[14px] border-muted"
      >
        <Package class="h-6 w-6 text-muted-foreground" aria-hidden="true" />
      </div>
      <p class="text-sm font-semibold">No item sales in this period</p>
      <p class="max-w-64 text-xs leading-5 text-muted-foreground">
        Product and service categories appear when orders contain recorded
        items.
      </p>
    </div>
    <p class="mt-5 text-[0.6875rem] leading-5 text-muted-foreground">
      Category totals use item lines. Shipping and order-level adjustments can
      make them differ from gross sales.
    </p>
  </section>
</template>

<script setup>
import { Package } from "lucide-vue-next";
const props = defineProps({
  categories: { type: Array, default: () => [] },
  currency: { type: String, default: "PHP" },
});
const circumference = 2 * Math.PI * 78;
const colors = [
  "var(--brand-secondary)",
  "var(--brand-primary)",
  "color-mix(in srgb, var(--brand-primary) 70%, hsl(var(--card)))",
  "color-mix(in srgb, var(--brand-primary) 44%, hsl(var(--card)))",
  "color-mix(in srgb, var(--brand-secondary) 30%, hsl(var(--card)))",
  "hsl(var(--muted-foreground) / 0.25)",
];
const total = computed(() =>
  props.categories.reduce(
    (sum, row) => sum + Math.max(0, Number(row.sales) || 0),
    0,
  ),
);
const segments = computed(() => {
  let offset = 0;
  return props.categories
    .filter((row) => Number(row.sales) > 0)
    .map((row, index) => {
      const fraction = Number(row.sales) / total.value;
      const segment = {
        ...row,
        fraction,
        offset,
        color: colors[index % colors.length],
      };
      offset += fraction;
      return segment;
    });
});
const money = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: props.currency,
  }).format(Number(value) || 0);
const compactMoney = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: props.currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
const percent = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
</script>
