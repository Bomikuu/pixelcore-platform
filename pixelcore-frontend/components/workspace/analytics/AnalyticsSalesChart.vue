<template>
  <section
    class="min-w-0 rounded-xl border bg-card p-5"
    aria-labelledby="sales-chart-heading"
  >
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 id="sales-chart-heading" class="text-sm font-extrabold">
          Sales overview
        </h2>
        <p class="mt-1 text-xs leading-5 text-muted-foreground">
          Gross sales and orders · cancelled orders excluded
        </p>
      </div>
      <Select
        :model-value="interval"
        @update:model-value="$emit('update:interval', $event)"
      >
        <SelectTrigger class="h-8 w-28 text-xs" aria-label="Chart interval"
          ><SelectValue
        /></SelectTrigger>
        <SelectContent class="w-[var(--radix-select-trigger-width)] min-w-0"
          ><SelectItem value="daily">Daily</SelectItem
          ><SelectItem value="weekly">Weekly</SelectItem
          ><SelectItem value="monthly">Monthly</SelectItem></SelectContent
        >
      </Select>
    </div>
    <div
      class="relative mt-5 overflow-x-auto pb-2"
      tabindex="0"
      role="group"
      aria-label="Sales chart. Use Left and Right arrow keys to inspect periods."
      @keydown="inspectKey"
      @blur="activeIndex = null"
      @pointerleave="activeIndex = null"
    >
      <svg
        class="h-60 w-full min-w-[28rem]"
        viewBox="0 0 720 250"
        role="img"
        aria-label="Sales bars and order-count line"
        @pointermove="inspectPointer"
      >
        <g v-for="step in 5" :key="step">
          <line
            x1="48"
            x2="672"
            :y1="18 + (step - 1) * 47"
            :y2="18 + (step - 1) * 47"
            stroke="hsl(var(--border))"
            stroke-opacity="0.65"
          />
          <text
            x="39"
            :y="22 + (step - 1) * 47"
            text-anchor="end"
            class="chart-label"
          >
            {{ compactNumber((salesMaximum * (5 - step)) / 4) }}
          </text>
          <text x="683" :y="22 + (step - 1) * 47" class="chart-label">
            {{ Math.round((orderMaximum * (5 - step)) / 4) }}
          </text>
        </g>
        <g v-for="(point, index) in plotted" :key="point.key">
          <rect
            :x="point.x - barWidth / 2"
            :y="point.y"
            :width="barWidth"
            :height="Math.max(0, 206 - point.y)"
            rx="2"
            fill="var(--brand-secondary)"
            :opacity="activeIndex === null || activeIndex === index ? 1 : 0.45"
            class="sales-bar"
          >
            <title>
              {{ periodLabel(point) }}: {{ money(point.sales) }},
              {{ point.orders }} orders
            </title>
          </rect>
        </g>
        <path
          v-if="hasValues"
          :d="orderPath"
          fill="none"
          stroke="var(--brand-primary)"
          stroke-width="2.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <circle
          v-for="point in plotted.length <= 35 && hasValues ? plotted : []"
          :key="point.key"
          :cx="point.x"
          :cy="point.orderY"
          r="3"
          fill="hsl(var(--card))"
          stroke="var(--brand-primary)"
          stroke-width="2"
        />
        <line
          v-if="activePoint"
          :x1="activePoint.x"
          :x2="activePoint.x"
          y1="12"
          y2="208"
          stroke="var(--brand-primary)"
          stroke-dasharray="3 3"
          stroke-opacity="0.6"
        />
        <text
          v-for="label in labels"
          :key="label.key"
          :x="label.x"
          y="235"
          text-anchor="middle"
          class="chart-label"
        >
          {{ shortDate(label.from) }}
        </text>
      </svg>
      <div
        v-if="activePoint"
        class="pointer-events-none absolute left-1/2 top-0 z-10 max-w-64 -translate-x-1/2 rounded-lg border bg-popover px-3 py-2 text-xs leading-5 text-popover-foreground shadow-md"
        role="status"
      >
        <strong class="block">{{ periodLabel(activePoint) }}</strong>
        {{ money(activePoint.sales) }} · {{ activePoint.orders }} order{{
          activePoint.orders === 1 ? "" : "s"
        }}
      </div>
      <p
        v-if="!hasValues"
        class="pointer-events-none absolute inset-x-0 top-24 mx-auto max-w-56 rounded-md bg-card/95 px-3 py-2 text-center text-xs text-muted-foreground"
      >
        No sales recorded in this period
      </p>
    </div>
    <div
      class="mt-3 flex flex-wrap justify-center gap-5 text-xs text-muted-foreground"
    >
      <span class="inline-flex items-center gap-2"
        ><span
          class="h-2.5 w-2.5 rounded-sm bg-[var(--brand-secondary)]"
          aria-hidden="true"
        />Sales ({{ currency }}) · left axis</span
      >
      <span class="inline-flex items-center gap-2"
        ><span
          class="h-2.5 w-2.5 rounded-full bg-[var(--brand-primary)]"
          aria-hidden="true"
        />Orders · right axis</span
      >
    </div>
    <Table class="sr-only"
      ><TableCaption>Sales overview by {{ interval }} period</TableCaption
      ><TableHeader
        ><TableRow
          ><TableHead>Period</TableHead><TableHead>Gross sales</TableHead
          ><TableHead>Orders</TableHead></TableRow
        ></TableHeader
      ><TableBody
        ><TableRow v-for="row in points" :key="row.key"
          ><TableCell>{{ periodLabel(row) }}</TableCell
          ><TableCell>{{ money(row.sales) }}</TableCell
          ><TableCell>{{ row.orders }}</TableCell></TableRow
        ></TableBody
      ></Table
    >
  </section>
</template>

<script setup>
const props = defineProps({
  points: { type: Array, default: () => [] },
  currency: { type: String, default: "PHP" },
  interval: { type: String, default: "daily" },
});
defineEmits(["update:interval"]);
const activeIndex = ref(null);
const roundMaximum = (value) => {
  if (value <= 0) return 4;
  const unit = 10 ** Math.floor(Math.log10(value / 4));
  return Math.ceil(value / 4 / unit) * unit * 4;
};
const salesMaximum = computed(() =>
  roundMaximum(Math.max(0, ...props.points.map((row) => row.sales))),
);
const orderMaximum = computed(() =>
  Math.max(
    4,
    roundMaximum(Math.max(0, ...props.points.map((row) => row.orders))),
  ),
);
const hasValues = computed(() =>
  props.points.some((row) => row.sales || row.orders),
);
const barWidth = computed(() =>
  Math.max(0.7, Math.min(30, (624 / Math.max(1, props.points.length)) * 0.65)),
);
const plotted = computed(() =>
  props.points.map((row, index) => ({
    ...row,
    x: 48 + ((index + 0.5) / props.points.length) * 624,
    y: 206 - (row.sales / salesMaximum.value) * 188,
    orderY: 206 - (row.orders / orderMaximum.value) * 188,
  })),
);
const orderPath = computed(() =>
  plotted.value
    .map((row, index) => `${index ? "L" : "M"} ${row.x} ${row.orderY}`)
    .join(" "),
);
const labels = computed(() =>
  [
    ...new Set([
      0,
      Math.floor((plotted.value.length - 1) / 4),
      Math.floor((plotted.value.length - 1) / 2),
      Math.floor((plotted.value.length - 1) * 0.75),
      plotted.value.length - 1,
    ]),
  ]
    .map((index) => plotted.value[index])
    .filter(Boolean),
);
const activePoint = computed(() => plotted.value[activeIndex.value] || null);
watch(
  () => props.points,
  () => {
    activeIndex.value = null;
  },
);
function inspectPointer(event) {
  const rect = event.currentTarget.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * 720;
  activeIndex.value =
    x >= 48 && x <= 672
      ? Math.min(
          props.points.length - 1,
          Math.floor(((x - 48) / 624) * props.points.length),
        )
      : null;
}
function inspectKey(event) {
  if (
    !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key) ||
    !props.points.length
  )
    return;
  event.preventDefault();
  activeIndex.value =
    event.key === "Home"
      ? 0
      : event.key === "End"
        ? props.points.length - 1
        : Math.max(
            0,
            Math.min(
              props.points.length - 1,
              (activeIndex.value ??
                (event.key === "ArrowLeft" ? props.points.length : -1)) +
                (event.key === "ArrowLeft" ? -1 : 1),
            ),
          );
}
const money = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: props.currency,
  }).format(value);
const compactNumber = (value) =>
  new Intl.NumberFormat("en-PH", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
const shortDate = (value) =>
  new Intl.DateTimeFormat("en-PH", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T12:00:00Z`));
const periodLabel = (row) =>
  row.from === row.to
    ? shortDate(row.from)
    : `${shortDate(row.from)} – ${shortDate(row.to)}`;
</script>

<style scoped>
.chart-label {
  fill: hsl(var(--muted-foreground));
  font-size: 10px;
  font-family: inherit;
}
.sales-bar {
  transition: opacity 160ms ease;
}
@media (prefers-reduced-motion: reduce) {
  .sales-bar {
    transition: none;
  }
}
</style>
