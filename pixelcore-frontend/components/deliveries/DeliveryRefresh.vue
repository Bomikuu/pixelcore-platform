<template>
  <div class="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
    <span class="inline-flex items-center gap-2"
      ><Clock3 class="h-3.5 w-3.5" aria-hidden="true" />{{
        terminal
          ? "Tracking ended"
          : paused
            ? "Automatic refresh paused"
            : "Refreshes every 30 seconds"
      }}</span
    >
    <span v-if="lastUpdated"
      >Received
      {{
        new Intl.DateTimeFormat("en-PH", { timeStyle: "short" }).format(
          lastUpdated,
        )
      }}</span
    >
    <Button
      class="gap-2"
      v-if="!terminal"
      type="button"
      variant="outline"
      size="sm"
      :disabled="busy"
      @click="$emit('refresh')"
      ><RefreshCw
        :class="['h-3.5 w-3.5', busy ? 'motion-safe:animate-spin' : '']"
        aria-hidden="true"
      />{{ busy ? "Refreshing…" : "Refresh" }}</Button
    >
  </div>
</template>
<script setup>
import { Clock3, RefreshCw } from "lucide-vue-next";
import { Button } from "~/components/ui/button";
defineProps({
  busy: Boolean,
  paused: Boolean,
  terminal: Boolean,
  lastUpdated: { type: Date, default: null },
});
defineEmits(["refresh"]);
</script>
