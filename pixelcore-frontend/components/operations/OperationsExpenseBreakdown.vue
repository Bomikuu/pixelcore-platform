<template>
  <figure :aria-labelledby="titleId">
    <div>
      <h2 :id="titleId" class="font-semibold">{{ title }}</h2>
      <p class="mt-1 text-sm text-muted-foreground">{{ description }}</p>
    </div>

    <div v-if="items.length" class="mt-6 space-y-4">
      <div v-for="item in items" :key="item.category">
        <div class="flex items-baseline justify-between gap-4 text-sm">
          <span class="truncate font-medium">{{ item.category }}</span>
          <span class="shrink-0 font-semibold tabular-nums">{{ money(item.amount) }}</span>
        </div>
        <div class="mt-2 h-2 overflow-hidden rounded-full bg-muted" aria-hidden="true">
          <div class="h-full rounded-full bg-[var(--brand-accent)]" :style="{ width: `${barWidth(item.amount)}%` }" />
        </div>
      </div>
    </div>
    <div v-else class="mt-6 grid min-h-52 place-items-center border-y bg-muted/25 px-6 text-center">
      <div>
        <p class="font-medium">No categorized expenses</p>
        <p class="mt-1 text-sm text-muted-foreground">Expense categories will appear after costs are recorded in this period.</p>
      </div>
    </div>
  </figure>
</template>

<script setup>
const props = defineProps({
  title: { type: String, default: 'Expense mix' },
  description: { type: String, default: 'Recorded spend by category' },
  items: { type: Array, default: () => [] },
  currency: { type: String, default: 'PHP' },
})
const titleId = `expense-chart-${useId()}`
const maximum = computed(() => Math.max(...props.items.map(item => Number(item.amount || 0)), 1))
function barWidth(value) { return Math.max(3, (Number(value || 0) / maximum.value) * 100) }
function money(value) { return new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency, maximumFractionDigits: 0 }).format(Number(value || 0)) }
</script>
