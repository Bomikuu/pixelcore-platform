<template>
  <div class="space-y-7">
    <SmokeyMascotStatus
      v-if="loading"
      state="searching"
      label="Opening your saved report…"
    />
    <p v-if="error || localError" role="alert" class="text-sm text-destructive">
      {{ localError || error }}
    </p>
    <template v-if="data"
      ><header class="space-y-3 border-b pb-6">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 class="text-2xl font-semibold tracking-tight">
              {{ data.title }}
            </h2>
            <p class="mt-2 text-sm text-muted-foreground">
              {{ data.facts.date_from }} – {{ data.facts.date_to }} ·
              {{ data.facts.timezone }}
            </p>
            <p class="mt-2 text-xs text-muted-foreground">
              Generated {{ generatedAt }} · {{ data.provider }} /
              {{ data.model }} · User {{ data.actor_id }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button
              variant="outline"
              :disabled="regenerating"
              @click="regenerate"
              >Regenerate · uses AI</Button
            ><Button
              v-if="canDelete"
              variant="ghost"
              @click="confirmDelete = true"
              >Delete report</Button
            >
          </div>
        </div>
      </header>
      <dl
        class="grid grid-cols-2 gap-x-8 gap-y-5 rounded-xl border bg-card p-5 md:grid-cols-3"
      >
        <div v-for="(value, key) in data.facts.metrics" :key="key">
          <dt class="text-xs text-muted-foreground">{{ metricLabel(key) }}</dt>
          <dd class="mt-1 break-words text-xl font-semibold tabular-nums">
            {{ value }}
          </dd>
        </div>
      </dl>
      <section class="max-w-3xl space-y-4">
        <h2 class="text-lg font-semibold">Summary</h2>
        <p class="whitespace-pre-wrap text-sm leading-7">
          {{ data.narrative.summary }}
        </p>
        <ul
          v-if="data.narrative.highlights?.length"
          class="list-disc space-y-2 pl-5 text-sm leading-6"
        >
          <li
            v-for="(highlight, index) in data.narrative.highlights"
            :key="index"
          >
            {{ highlight }}
          </li>
        </ul>
      </section>
      <section
        v-if="data.facts.unavailable_sources?.length"
        class="space-y-2 rounded-lg border p-4"
      >
        <h2 class="font-medium">Unavailable information</h2>
        <p
          v-for="message in data.facts.unavailable_sources"
          :key="message"
          class="text-sm text-muted-foreground"
        >
          {{ message }}
        </p>
      </section>
      <SmokeyReportTable
        v-for="(table, key) in data.facts.tables"
        :key="key"
        :report-id="data.id"
        :table-key="key"
        :table="table"
      />
      <footer class="space-y-3 border-t pt-5">
        <h2 class="text-sm font-semibold">Sources</h2>
        <div class="flex flex-wrap gap-4">
          <NuxtLink
            v-for="source in data.facts.sources"
            :key="source.href"
            :to="source.href"
            class="text-sm underline underline-offset-4"
            >{{ source.label }}</NuxtLink
          >
        </div>
        <p class="text-xs leading-6 text-muted-foreground">
          Totals and tables are a saved snapshot of recorded facts. The AI
          summary is generated text; check the source records when making
          decisions. Missing clock-ins do not prove absence.
        </p>
      </footer> </template
    ><Dialog v-model:open="confirmDelete"
      ><DialogContent
        ><DialogHeader
          ><DialogTitle>Delete this report?</DialogTitle
          ><DialogDescription
            >This removes the saved summary and its detail snapshot. Usage
            records remain.</DialogDescription
          ></DialogHeader
        ><DialogFooter
          ><Button variant="outline" @click="confirmDelete = false"
            >Keep report</Button
          ><Button variant="destructive" @click="remove"
            >Delete report</Button
          ></DialogFooter
        ></DialogContent
      ></Dialog
    >
  </div>
</template>
<script setup>
import { metricLabel } from "~/utils/smokeySettings";
import SmokeyMascotStatus from "./SmokeyMascotStatus.vue";
import SmokeyReportTable from "./SmokeyReportTable.vue";
const route = useRoute(),
  router = useRouter(),
  business = useBusinessStore();
const { data, error, loading, request } = useSmokeyResource(
  computed(() => `reports/${route.params.reportId}/`),
);
const { config, controller } = useSmokeyAssistant();
const confirmDelete = ref(false),
  localError = ref(""),
  regenerating = ref(false);
const canDelete = computed(() =>
  config.value?.permissions?.includes("delete_reports"),
);
const generatedAt = computed(() =>
  data.value
    ? new Date(data.value.created_at).toLocaleString(undefined, {
        timeZone: data.value.facts.timezone,
      })
    : "",
);
async function regenerate() {
  if (!data.value) return;
  regenerating.value = true;
  const facts = data.value.facts;
  await controller.submit(
    `Regenerate ${facts.kind} report from ${facts.date_from} to ${facts.date_to}`,
    { kind: facts.kind, date_from: facts.date_from, date_to: facts.date_to },
  );
  await router.push("/workspace/smokey/assistant");
  regenerating.value = false;
}
async function remove() {
  const id = business.activeBusiness?.public_id;
  try {
    await request(`reports/${data.value.id}/`, { method: "DELETE" });
    if (id === business.activeBusiness?.public_id)
      await router.push("/workspace/smokey/reports");
  } catch (issue) {
    localError.value =
      issue?.data?.error?.message || "Could not delete this report.";
  } finally {
    confirmDelete.value = false;
  }
}
</script>
