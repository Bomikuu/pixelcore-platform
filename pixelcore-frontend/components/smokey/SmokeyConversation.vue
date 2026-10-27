<template>
  <div class="flex min-h-0 flex-1 flex-col gap-5">
    <div class="min-h-0 flex-1 space-y-5 overflow-y-auto px-1">
      <SmokeyMascotStatus
        :state="state.state"
        :kind="state.plan?.kind"
        :has-plan="Boolean(state.plan && Object.keys(state.plan).length)"
      />
      <template v-if="state.state === 'idle'">
        <div>
          <h2 class="text-xl font-semibold tracking-tight">
            What would you like to know?
          </h2>
          <p class="mt-2 text-sm leading-6 text-muted-foreground">
            Ask about recorded sales, attendance, or late arrivals. Dates follow
            {{ config?.timezone || "your business timezone" }}.
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <Button
            v-for="text in suggestions"
            :key="text"
            variant="outline"
            size="sm"
            class="h-auto whitespace-normal text-left"
            @click="prompt = text"
            >{{ text }}</Button
          >
        </div>
      </template>
      <p v-if="state.prompt" class="rounded-lg bg-muted px-4 py-3 text-sm">
        {{ state.prompt }}
      </p>
      <p v-if="state.plan?.date_from" class="text-xs text-muted-foreground">
        {{ state.plan.date_from }} – {{ state.plan.date_to }} ·
        {{ config?.timezone }}
      </p>
      <p v-if="state.clarification" class="text-sm leading-6">
        {{ state.clarification }}
      </p>
      <div
        v-if="state.error || state.transport_error"
        role="alert"
        class="space-y-3 rounded-lg border border-destructive/30 p-4 text-sm"
      >
        <p>{{ state.error?.message || state.transport_error }}</p>
        <Button
          v-if="state.interrupted"
          variant="outline"
          size="sm"
          @click="controller.resume()"
          >Recover this request</Button
        >
        <p class="text-xs text-muted-foreground">
          A stopped or interrupted provider call may still consume usage. New
          attempts can consume additional usage.
        </p>
      </div>
      <div v-if="state.report_id" class="space-y-3 border-t pt-4">
        <p
          v-if="previewLoading"
          class="text-sm text-muted-foreground"
          role="status"
        >
          Opening your summary…
        </p>
        <p v-if="previewError" role="alert" class="text-sm text-destructive">
          {{ previewError }}
        </p>
        <p v-if="preview" class="whitespace-pre-wrap text-sm leading-7">
          {{ preview.narrative.summary }}
        </p>
        <dl v-if="preview" class="grid grid-cols-2 gap-3">
          <div v-for="(value, key) in preview.facts.metrics" :key="key">
            <dt class="text-xs text-muted-foreground">
              {{ metricLabel(key) }}
            </dt>
            <dd class="text-sm font-semibold tabular-nums">{{ value }}</dd>
          </div>
        </dl>
        <ButtonLink
          :to="`/workspace/smokey/reports/${state.report_id}`"
          @click="opened = false"
          >Open full report<ArrowUpRight class="h-4 w-4"
        /></ButtonLink>
      </div>
      <p
        v-if="state.state === 'cancelled'"
        class="text-sm text-muted-foreground"
      >
        Generation stopped. Your prompt is still available below.
      </p>
    </div>
    <form
      novalidate
      class="shrink-0 space-y-3 border-t pt-4"
      @submit.prevent="submit"
    >
      <Label for="smokey-prompt">Ask Smokey</Label>
      <Textarea
        id="smokey-prompt"
        v-model="prompt"
        :disabled="busy"
        :maxlength="4000"
        rows="3"
        placeholder="Who arrived late today?"
        class="resize-none"
      />
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span class="text-xs text-muted-foreground"
          >Uses your business’s selected AI connection.</span
        >
        <Button
          v-if="busy"
          type="button"
          variant="outline"
          @click="controller.stop()"
          >Stop generation</Button
        >
        <Button
          v-else
          type="submit"
          :disabled="!prompt.trim() || !config?.default_connection_id"
          >{{
            state.state === "failed"
              ? "Try a new generation"
              : "Generate report"
          }}<Send class="ml-2 h-4 w-4"
        /></Button>
      </div>
      <p
        v-if="!config?.default_connection_id"
        class="text-xs text-muted-foreground"
      >
        An administrator needs to configure an
        <NuxtLink to="/workspace/smokey/connections" class="underline"
          >AI connection</NuxtLink
        >
        first.
      </p>
    </form>
  </div>
</template>
<script setup>
import { ArrowUpRight, Send } from "lucide-vue-next";
import { mascotPresentation } from "~/utils/smokeyAssistant";
import { metricLabel } from "~/utils/smokeySettings";
import SmokeyMascotStatus from "./SmokeyMascotStatus.vue";
const { state, config, controller, opened } = useSmokeyAssistant();
const prompt = ref("");
const {
  data: preview,
  loading: previewLoading,
  error: previewError,
} = useSmokeyResource(
  computed(() =>
    state.value.report_id ? `reports/${state.value.report_id}/` : null,
  ),
);
const busy = computed(
  () => mascotPresentation(state.value.state).busy && !state.value.interrupted,
);
const suggestions = [
  "Summarize today's business",
  "Who attended today?",
  "Who arrived late today?",
  "Show today's sales totals",
];
function submit() {
  if (prompt.value.trim()) controller.submit(prompt.value);
}
watch(
  () => state.value.prompt,
  (value) => {
    if (value) prompt.value = value;
  },
);
watch(
  () => useBusinessStore().activeBusiness?.public_id,
  () => {
    prompt.value = "";
  },
);
</script>
