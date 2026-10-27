<template>
  <div class="space-y-7">
    <SmokeyMascotStatus
      v-if="loading || saving"
      state="searching"
      :label="
        saving ? 'Saving your usage limits…' : 'Checking assistant usage…'
      "
    />
    <p v-if="error || localError" role="alert" class="text-sm text-destructive">
      {{ localError || error }}
    </p>
    <p v-if="notice" role="status" class="text-sm">{{ notice }}</p>
    <div class="flex flex-wrap items-end gap-3">
      <div class="space-y-2">
        <Label for="usage-from">From</Label
        ><Input id="usage-from" v-model="dateFrom" type="date" />
      </div>
      <div class="space-y-2">
        <Label for="usage-to">To</Label
        ><Input id="usage-to" v-model="dateTo" type="date" />
      </div>
      <Button
        variant="outline"
        :disabled="loading || !dateFrom || !dateTo"
        @click="applyRange"
        >Apply dates</Button
      >
    </div>
    <p class="max-w-3xl text-sm leading-6 text-muted-foreground">
      AI calls include report interpretation, summaries and connection checks.
      Tokens marked unknown may still have been billed by your provider.
      Application limits are separate from your provider’s balance and invoice.
    </p>
    <Table
      ><TableCaption
        >Usage by connection and model for the selected period</TableCaption
      ><TableHeader
        ><TableRow
          ><TableHead>Provider / model</TableHead><TableHead>Calls</TableHead
          ><TableHead>Input tokens</TableHead
          ><TableHead>Output tokens</TableHead
          ><TableHead>Unknown usage</TableHead></TableRow
        ></TableHeader
      ><TableBody
        ><TableRow
          v-for="row in data?.by_model || []"
          :key="row.connection_id_snapshot + row.model"
          ><TableCell class="break-all"
            >{{ row.provider }} / {{ row.model }}</TableCell
          ><TableCell>{{ row.calls }}</TableCell
          ><TableCell>{{ formatTokenCount(row.input_tokens) }}</TableCell
          ><TableCell>{{ formatTokenCount(row.output_tokens) }}</TableCell
          ><TableCell>{{ row.unknown }}</TableCell></TableRow
        ></TableBody
      ></Table
    >
    <p
      v-if="!loading && !data?.by_model?.length"
      class="text-sm text-muted-foreground"
    >
      No AI calls in this period.
    </p>
    <section class="space-y-3">
      <h2 class="text-lg font-semibold">Current limit accounting</h2>
      <p class="text-xs text-muted-foreground">
        Token accounting includes reservations for in-flight calls and uncertain
        usage.
      </p>
      <Table
        ><TableHeader
          ><TableRow
            ><TableHead>Period</TableHead><TableHead>Calls</TableHead
            ><TableHead>Tokens used or reserved</TableHead></TableRow
          ></TableHeader
        ><TableBody
          ><TableRow
            v-for="bucket in data?.limits_usage || []"
            :key="bucket.period"
            ><TableCell>{{ bucket.period }}</TableCell
            ><TableCell>{{ bucket.requests }}</TableCell
            ><TableCell>{{
              formatTokenCount(bucket.tokens)
            }}</TableCell></TableRow
          ></TableBody
        ></Table
      >
    </section>
    <form
      novalidate
      v-if="canEdit"
      class="max-w-2xl space-y-5 border-t pt-6"
      @submit.prevent="save"
    >
      <h2 class="text-lg font-semibold">Application limits</h2>
      <div class="grid gap-4 sm:grid-cols-2">
        <div v-for="field in fields" :key="field.key" class="space-y-2">
          <Label :for="field.key">{{ field.label }}</Label
          ><Input
            :id="field.key"
            v-model.number="limits[field.key]"
            type="number"
            :min="field.key.endsWith('tokens') ? 1000 : 1"
            required
          />
        </div>
      </div>
      <Button type="submit" :disabled="saving">Save limits</Button>
    </form>
    <section class="space-y-3 border-t pt-6">
      <h2 class="text-lg font-semibold">Recent AI calls</h2>
      <Table
        ><TableHeader
          ><TableRow
            ><TableHead>Model</TableHead><TableHead>Purpose</TableHead
            ><TableHead>Outcome</TableHead
            ><TableHead>Input / output tokens</TableHead></TableRow
          ></TableHeader
        ><TableBody
          ><TableRow
            v-for="(attempt, index) in data?.attempts || []"
            :key="index"
            ><TableCell class="break-all"
              >{{ attempt.provider }} / {{ attempt.model }}</TableCell
            ><TableCell>{{ attempt.purpose }}</TableCell
            ><TableCell
              >{{ attempt.outcome
              }}<span
                v-if="attempt.generation_state"
                class="block text-xs text-muted-foreground"
                >Report {{ attempt.generation_state }} · User
                {{ attempt.actor_id }}</span
              ></TableCell
            ><TableCell
              >{{ formatTokenCount(attempt.input_tokens) }} /
              {{ formatTokenCount(attempt.output_tokens) }}</TableCell
            ></TableRow
          ></TableBody
        ></Table
      >
    </section>
  </div>
</template>
<script setup>
import { formatTokenCount, canConfigureSmokey } from "~/utils/smokeySettings";
import SmokeyMascotStatus from "./SmokeyMascotStatus.vue";
const { config, refresh: refreshConfig } = useSmokeyAssistant();
const dateFrom = ref(""),
  dateTo = ref(""),
  query = ref("usage/");
const { data, error, loading, request, refresh } = useSmokeyResource(query);
const saving = ref(false),
  localError = ref(""),
  notice = ref(""),
  limits = reactive({
    daily_requests: 100,
    monthly_requests: 2000,
    daily_tokens: 200000,
    monthly_tokens: 3000000,
  });
const fields = [
  { key: "daily_requests", label: "Daily AI calls" },
  { key: "monthly_requests", label: "Monthly AI calls" },
  { key: "daily_tokens", label: "Daily tokens" },
  { key: "monthly_tokens", label: "Monthly tokens" },
];
const canEdit = computed(() => canConfigureSmokey(config.value));
watch(
  config,
  (value) => {
    if (value) for (const field of fields) limits[field.key] = value[field.key];
  },
  { immediate: true },
);
function applyRange() {
  if (dateFrom.value > dateTo.value) {
    localError.value = "Choose an end date on or after the start date.";
    return;
  }
  localError.value = "";
  query.value = `usage/?date_from=${dateFrom.value}&date_to=${dateTo.value}`;
}
async function save() {
  for (const field of fields) {
    const value = Number(limits[field.key]);
    const minimum = field.key.endsWith("tokens") ? 1000 : 1;
    const maximum = field.key.endsWith("tokens")
      ? 1000000000
      : field.key === "daily_requests"
        ? 100000
        : 1000000;
    if (!Number.isInteger(value) || value < minimum || value > maximum) {
      localError.value = `${field.label} must be a whole number from ${minimum} to ${maximum}.`;
      return;
    }
  }
  saving.value = true;
  notice.value = "";
  localError.value = "";
  try {
    await request("settings/", { method: "PATCH", body: { ...limits } });
    await refreshConfig();
    await refresh();
    notice.value = "Usage limits saved.";
  } catch (issue) {
    localError.value =
      issue?.data?.error?.message || "Could not save usage limits.";
  } finally {
    saving.value = false;
  }
}
</script>
