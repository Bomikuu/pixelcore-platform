<template>
  <section class="min-w-0 w-full">
    <p
      v-if="status.loading && !status.ready"
      role="status"
      class="py-8 text-sm text-muted-foreground"
    >
      Opening Smokey…
    </p>
    <div v-if="status.error" role="alert" class="space-y-4 py-8">
      <h1 class="text-xl font-semibold">Smokey is unavailable</h1>
      <p class="text-sm text-muted-foreground">{{ status.error }}</p>
      <Button variant="outline" @click="retry">Try again</Button>
    </div>
    <div v-show="!status.error" ref="surface" class="min-w-0" />
  </section>
</template>
<script setup>
import { Button } from "@/components/ui/button";
const { status, retry, attachDashboard, detachDashboard } =
  useSmokeyAssistant();
const surface = ref(null);
onMounted(() => {
  if (surface.value) attachDashboard(surface.value);
});
onBeforeUnmount(detachDashboard);
</script>
