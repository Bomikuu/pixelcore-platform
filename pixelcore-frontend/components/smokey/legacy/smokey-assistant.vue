<template>
  <SmokeyDashboardFrame
    title="Ask Smokey"
    description="Ask for a report in your own words."
    ><div
      class="flex h-[max(34rem,calc(100dvh-19rem))] max-w-3xl flex-col rounded-xl border bg-card p-5"
    >
      <SmokeyConversation /></div
  ></SmokeyDashboardFrame>
</template>
<script setup>
import SmokeyDashboardFrame from "~/components/smokey/SmokeyDashboardFrame.vue";
import SmokeyConversation from "~/components/smokey/SmokeyConversation.vue";
</script>
