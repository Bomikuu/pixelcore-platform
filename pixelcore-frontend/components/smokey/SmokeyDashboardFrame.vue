<template>
  <section class="workspace-page space-y-6">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">{{ title }}</h1>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">
          {{ description }}
        </p>
      </div>
      <SmokeyThemeSelect />
    </header>
    <nav
      aria-label="Smokey sections"
      class="flex gap-1 overflow-x-auto border-b"
    >
      <NuxtLink
        v-for="item in links"
        :key="item.path"
        :to="item.path"
        class="shrink-0 border-b-2 px-3 py-3 text-sm font-medium"
        :class="
          active(item.path)
            ? 'border-primary text-primary'
            : 'border-transparent text-muted-foreground hover:text-foreground'
        "
        :aria-current="active(item.path) ? 'page' : undefined"
        >{{ item.label }}</NuxtLink
      >
    </nav>
    <p v-if="error" role="alert" class="text-sm text-destructive">
      {{ error }}
    </p>
    <div v-if="enabled" :key="business.activeBusiness?.public_id"><slot /></div>
    <div v-else class="max-w-xl space-y-4 py-12">
      <SmokeyMascotStatus />
      <h2 class="text-xl font-semibold">Meet your business assistant</h2>
      <p class="text-sm leading-6 text-muted-foreground">
        Enable Smokey, connect your own AI provider, and ask for reports from
        your business records. Your provider bills you directly.
      </p>
      <Button
        v-if="canConfigure"
        :disabled="enabling || !business.activeBusiness"
        @click="enable"
        >{{ enabling ? "Enabling Smokey…" : "Enable Smokey" }}</Button
      >
      <p v-else class="text-sm text-muted-foreground">
        Ask a business owner or administrator to enable Smokey.
      </p>
    </div>
  </section>
</template>
<script setup>
import { workspaceCreateRole } from "~/utils/workspaceQuickActions";
import SmokeyThemeSelect from "./SmokeyThemeSelect.vue";
import SmokeyMascotStatus from "./SmokeyMascotStatus.vue";
defineProps({
  title: { type: String, default: "Smokey" },
  description: {
    type: String,
    default: "Reports grounded in your business records.",
  },
});
const business = useBusinessStore(),
  auth = useAuthStore(),
  route = useRoute();
const { apiFetch } = useApiClient(),
  { refresh } = useSmokeyAssistant();
const error = ref(""),
  enabling = ref(false);
const enabled = computed(() =>
  business.activeBusiness?.enabled_modules?.includes("smokey"),
);
const canConfigure = computed(() =>
  ["owner", "admin"].includes(
    workspaceCreateRole(auth.user, business.activeBusiness),
  ),
);
const links = [
  { label: "Overview", path: "/workspace/smokey" },
  ...["assistant", "reports", "appearance", "connections", "usage"].map(
    (key) => ({
      label:
        key === "connections"
          ? "AI connections"
          : key[0].toUpperCase() + key.slice(1),
      path: "/workspace/smokey/" + key,
    }),
  ),
];
const active = (path) =>
  path === "/workspace/smokey"
    ? route.path === path
    : route.path.startsWith(path);
async function enable() {
  enabling.value = true;
  error.value = "";
  try {
    await apiFetch(
      `businesses/${business.activeBusiness.public_id}/capabilities/smokey/`,
      { method: "PATCH", body: { status: "active" } },
    );
    await business.loadBusinesses();
    await refresh();
  } catch (issue) {
    error.value =
      issue?.data?.error?.message ||
      "Could not enable Smokey. Confirm the module is installed on the server.";
  } finally {
    enabling.value = false;
  }
}
</script>
