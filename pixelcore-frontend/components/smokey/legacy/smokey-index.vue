<template>
  <SmokeyDashboardFrame
    title="Smokey"
    description="Turn your business records into a useful daily briefing."
  >
    <div class="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div class="space-y-6 py-3">
        <SmokeyMascotStatus />
        <div class="max-w-2xl">
          <h2 class="text-2xl font-semibold tracking-tight">
            A clearer picture of your day.
          </h2>
          <p class="mt-3 text-sm leading-7 text-muted-foreground">
            Ask who attended, who arrived late, or how sales are doing. Smokey
            finds the recorded facts and writes a summary using your business’s
            AI connection.
          </p>
        </div>
        <div class="flex flex-wrap gap-3">
          <ButtonLink to="/workspace/smokey/assistant"
            >Ask Smokey<ArrowUpRight class="h-4 w-4" /></ButtonLink
          ><ButtonLink variant="outline" to="/workspace/smokey/reports"
            >Saved reports</ButtonLink
          >
        </div>
        <div class="border-t pt-5">
          <h3 class="font-semibold">Your records stay the source of truth</h3>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Totals come from PixelCore. Each report records its date range,
            timezone and sources. Opening a saved report does not make another
            AI request.
          </p>
        </div>
      </div>
      <aside class="space-y-5 rounded-xl border bg-card p-5">
        <h2 class="font-semibold">Get ready</h2>
        <ol class="space-y-5 text-sm">
          <li>
            <NuxtLink
              to="/workspace/smokey/connections"
              class="font-medium underline underline-offset-4"
              >Connect your AI provider</NuxtLink
            >
            <p class="mt-1 text-muted-foreground">
              Add a key, choose a model, and run a connection check.
            </p>
          </li>
          <li>
            <NuxtLink
              to="/workspace/smokey/appearance"
              class="font-medium underline underline-offset-4"
              >Choose your mascot</NuxtLink
            >
            <p class="mt-1 text-muted-foreground">
              Use Smokey, a custom image or a standard launcher.
            </p>
          </li>
          <li>
            <NuxtLink
              to="/workspace/smokey/usage"
              class="font-medium underline underline-offset-4"
              >Set your limits</NuxtLink
            >
            <p class="mt-1 text-muted-foreground">
              Keep track of calls and tokens across your connections.
            </p>
          </li>
        </ol>
      </aside>
    </div>
  </SmokeyDashboardFrame>
</template>
<script setup>
import { ArrowUpRight } from "lucide-vue-next";
import SmokeyDashboardFrame from "~/components/smokey/SmokeyDashboardFrame.vue";
import SmokeyMascotStatus from "~/components/smokey/SmokeyMascotStatus.vue";
</script>
