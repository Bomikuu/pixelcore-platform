<template>
  <SmokeyDashboardFrame
    title="Usage"
    description="See your AI calls, token usage and application limits."
    ><SmokeyUsage
  /></SmokeyDashboardFrame>
</template>
<script setup>
import SmokeyDashboardFrame from "~/components/smokey/SmokeyDashboardFrame.vue";
import SmokeyUsage from "~/components/smokey/SmokeyUsage.vue";
</script>
