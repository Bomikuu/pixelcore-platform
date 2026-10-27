<template>
  <section class="space-y-3">
    <h2 class="text-lg font-semibold">{{ table.label }}</h2>
    <p class="text-xs text-muted-foreground">
      {{ table.total }} records<span v-if="table.truncated">
        · Showing the first {{ table.stored }} saved rows; totals include all
        records.</span
      >
    </p>
    <p v-if="error" role="alert" class="text-sm text-destructive">
      {{ error }}
    </p>
    <SmokeyMascotStatus
      v-if="loading"
      state="searching"
      label="Loading saved report rows…"
    /><Table
      ><TableHeader
        ><TableRow
          ><TableHead v-for="column in columns" :key="column">{{
            metricLabel(column)
          }}</TableHead></TableRow
        ></TableHeader
      ><TableBody
        ><TableRow v-for="(row, index) in rows" :key="index"
          ><TableCell v-for="column in columns" :key="column">{{
            display(row[column])
          }}</TableCell></TableRow
        ></TableBody
      ><TableCaption v-if="!rows.length"
        >No matching records in this period.</TableCaption
      ></Table
    >
    <div class="flex items-center gap-3">
      <Button
        variant="outline"
        size="sm"
        :disabled="offset === 0 || loading"
        @click="offset -= 100"
        >Previous rows</Button
      ><Button
        variant="outline"
        size="sm"
        :disabled="offset + 100 >= (data?.count || 0) || loading"
        @click="offset += 100"
        >Next rows</Button
      >
    </div>
  </section>
</template>
<script setup>
import { metricLabel } from "~/utils/smokeySettings";
import SmokeyMascotStatus from "./SmokeyMascotStatus.vue";
const props = defineProps({
  reportId: { type: String, required: true },
  tableKey: { type: String, required: true },
  table: { type: Object, required: true },
});
const offset = ref(0);
const { data, error, loading } = useSmokeyResource(
  computed(
    () =>
      `reports/${props.reportId}/tables/${props.tableKey}/?offset=${offset.value}`,
  ),
);
const rows = computed(() => data.value?.results || props.table.rows || []);
const columns = computed(() =>
  Object.keys(rows.value[0] || props.table.rows?.[0] || {}),
);
const display = (value) =>
  value == null
    ? "—"
    : typeof value === "boolean"
      ? value
        ? "Yes"
        : "No"
      : value;
</script>
