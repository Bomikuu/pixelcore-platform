<template>
  <figure class="min-w-0" :aria-labelledby="titleId">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div><h2 :id="titleId" class="text-base font-extrabold">{{ title }}</h2><p class="mt-1 text-sm text-muted-foreground">{{ description }}</p></div>
      <p class="text-2xl font-extrabold tabular-nums">{{ money(total) }}</p>
    </div>

    <div v-if="points.length" class="relative mt-7">
      <svg class="h-64 w-full overflow-visible" viewBox="0 0 760 250" role="img" :aria-label="`${title}: ${description}`" preserveAspectRatio="none">
        <g class="text-border">
          <line v-for="line in 5" :key="line" x1="0" x2="760" :y1="(line - 1) * 55 + 10" :y2="(line - 1) * 55 + 10" stroke="currentColor" stroke-width="1" vector-effect="non-scaling-stroke" />
        </g>
        <path :d="areaPath" fill="var(--brand-primary)" opacity="0.09" />
        <path :d="linePath" fill="none" stroke="var(--brand-primary)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke" />
        <g v-for="point in plotted" :key="point.key">
          <circle :cx="point.x" :cy="point.y" r="4" fill="hsl(var(--background))" stroke="var(--brand-primary)" stroke-width="3" vector-effect="non-scaling-stroke"><title>{{ point.fullLabel }}: {{ money(point.value) }}</title></circle>
        </g>
      </svg>
      <p v-if="!hasValues" class="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 text-center text-sm font-semibold text-muted-foreground">No sales recorded in this period</p>
      <div class="mt-3 grid text-xs font-semibold text-muted-foreground" :style="{ gridTemplateColumns: `repeat(${visibleLabels.length}, minmax(0, 1fr))` }"><span v-for="label in visibleLabels" :key="label.key" class="truncate" :class="label.align">{{ label.label }}</span></div>
    </div>
    <div v-else class="mt-7 grid h-64 place-items-center border-y bg-muted/25 px-6 text-center"><p class="text-sm font-semibold text-muted-foreground">Choose a valid reporting period.</p></div>

    <Table class="sr-only"><TableCaption>{{ title }}</TableCaption><TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Value</TableHead></TableRow></TableHeader><TableBody><TableRow v-for="point in points" :key="point.key"><TableCell>{{ point.fullLabel }}</TableCell><TableCell>{{ money(point.value) }}</TableCell></TableRow></TableBody></Table>
  </figure>
</template>

<script setup>
const props = defineProps({ title: { type: String, required: true }, description: { type: String, required: true }, points: { type: Array, default: () => [] }, currency: { type: String, default: 'PHP' } })
const titleId = `chart-${useId()}`
const values = computed(() => props.points.map((point) => Number(point.value || 0)))
const maximum = computed(() => Math.max(...values.value, 1))
const total = computed(() => values.value.reduce((sum, value) => sum + value, 0))
const hasValues = computed(() => values.value.some((value) => value > 0))
const plotted = computed(() => props.points.map((point, index) => ({ ...point, x: props.points.length === 1 ? 380 : (index / (props.points.length - 1)) * 760, y: 230 - (Number(point.value || 0) / maximum.value) * 210 })))
const linePath = computed(() => plotted.value.map((point, index) => `${index ? 'L' : 'M'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' '))
const areaPath = computed(() => plotted.value.length ? `${linePath.value} L 760 230 L 0 230 Z` : '')
const visibleLabels = computed(() => { if (!props.points.length) return []; const indexes = [...new Set([0, Math.floor((props.points.length - 1) / 2), props.points.length - 1])]; return indexes.map((index, position) => ({ ...props.points[index], align: position === 0 ? 'text-left' : position === indexes.length - 1 ? 'text-right' : 'text-center' })) })
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency, maximumFractionDigits: 0 }).format(Number(value || 0))
</script>
