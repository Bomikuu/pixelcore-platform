<template>
  <SmokeyModulePage v-if="moduleMode" />
  <LegacyPage v-else />
</template>
<script setup>
import SmokeyModulePage from "~/components/smokey/SmokeyModulePage.vue";
import LegacyPage from "~/components/smokey/legacy/smokey-usage.vue";
const moduleMode = useRuntimeConfig().public.smokeyUiMode === "module";
</script>
