<template>
  <StatePanel
    v-if="!items.length"
    title="No leave requests"
    message="Vacation, sick leave, and other time-off requests will appear here."
  />
  <div v-else class="divide-y rounded-lg border">
    <article
      v-for="item in items"
      :key="item.public_id"
      class="flex flex-col justify-between gap-3 p-4 sm:flex-row sm:items-center"
    >
      <div>
        <div class="flex flex-wrap items-center gap-2">
          <p class="text-sm font-bold capitalize">{{ item.leave_type.replaceAll("_", " ") }}</p>
          <StatusPill :value="item.status" />
        </div>
        <p class="mt-1 text-sm text-muted-foreground">{{ dateRange(item) }}</p>
        <p class="mt-2 text-sm leading-6">{{ item.reason }}</p>
        <p v-if="item.review_notes" class="mt-2 text-xs text-muted-foreground">
          Manager note: {{ item.review_notes }}
        </p>
      </div>
      <Button
        v-if="item.status === 'pending'"
        variant="outline"
        size="sm"
        type="button"
        @click="$emit('cancel', item)"
      >
        <X class="h-4 w-4" aria-hidden="true" />
        Cancel request
      </Button>
    </article>
  </div>
</template>

<script setup>
import { X } from "lucide-vue-next";

defineProps({
  items: { type: Array, default: () => [] },
});

defineEmits(["cancel"]);

function dateRange(item) {
  const start = formatDate(item.start_date);
  const end = formatDate(item.end_date);
  const range = item.start_date === item.end_date ? start : `${start}–${end}`;
  return item.partial_day ? `${range} · Partial day` : range;
}

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}
</script>
