<template>
  <main class="min-h-screen bg-[#0d1917] text-[#f7f3ea]">
    <form
      v-if="!deviceToken"
      class="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6"
      @submit.prevent="pair"
    >
      <PixelCoreMark />
      <h1 class="display-face mt-10 text-4xl font-semibold">
        Pair this display
      </h1>
      <p class="mt-4 leading-7 text-white/65">
        Enter the single-use code shown in Site → Displays. This screen will
        remember its secure device session.
      </p>
      <label
        class="mt-8 text-xs font-extrabold uppercase tracking-[.14em]"
        for="pairing-code"
        >Setup code</label
      ><Input
        id="pairing-code"
        v-model.trim="code"
        class="mt-2 min-h-14 border border-white/25 bg-transparent px-4 text-center font-mono text-2xl font-bold uppercase tracking-[.2em]"
        maxlength="8"
        autocomplete="one-time-code"
        required
      />
      <p v-if="pairError" class="mt-3 text-sm text-[#ff9b8c]" role="alert">
        {{ pairError }}
      </p>
      <Button
        variant="ghost"
        class="mt-5 min-h-12 bg-[#f2ad45] px-5 font-extrabold text-[#102a2a]"
        :disabled="pairing"
        >{{ pairing ? "Pairing…" : "Pair screen" }}</Button
      >
    </form>
    <section
      v-else-if="session?.publication"
      class="h-screen w-screen overflow-hidden"
    >
      <InteractiveDisplayCanvas
        :settings="session.publication.settings"
        :offerings="session.publication.offerings"
        :assets="session.publication.assets"
        :business-name="session.publication.business_identity?.display_name"
        :background-url="session.publication.background_asset_url || ''"
        :currency="session.publication.business_identity?.currency || 'PHP'"
      />
    </section>
    <section
      v-else
      class="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center px-6 text-center"
    >
      <Monitor class="h-12 w-12 text-[#f2ad45]" aria-hidden="true" />
      <h1 class="display-face mt-6 text-4xl font-semibold">Screen connected</h1>
      <p class="mt-4 leading-7 text-white/65">
        Assign a published display to this device in Site → Displays. This
        screen refreshes automatically.
      </p>
      <Button
        variant="ghost"
        class="mt-6 border border-white/25 px-5 py-3 font-bold"
        type="button"
        @click="loadSession"
        >Check again</Button
      >
    </section>
  </main>
</template>

<script setup>
import { Monitor } from "lucide-vue-next";
import InteractiveDisplayCanvas from "@/components/display/InteractiveDisplayCanvas.vue";
definePageMeta({ layout: "storefront" });
const config = useRuntimeConfig();
const code = ref("");
const pairing = ref(false);
const pairError = ref("");
const deviceToken = ref("");
const session = ref(null);
let timer;
onMounted(() => {
  deviceToken.value = localStorage.getItem("pixelcore_signage_token") || "";
  if (deviceToken.value) {
    loadSession();
    timer = window.setInterval(loadSession, 30000);
  }
});
onBeforeUnmount(() => window.clearInterval(timer));
async function pair() {
  pairing.value = true;
  pairError.value = "";
  try {
    const response = await $fetch("devices/pair/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      body: { pairing_code: code.value, device_type: "signage" },
    });
    if (response.device.device_type !== "signage")
      throw new Error("This setup code belongs to a different device type.");
    deviceToken.value = response.device_token;
    localStorage.setItem("pixelcore_signage_token", response.device_token);
    await loadSession();
    timer = window.setInterval(loadSession, 30000);
  } catch (error) {
    pairError.value =
      error?.data?.error?.message ||
      error.message ||
      "The screen could not be paired.";
  } finally {
    pairing.value = false;
  }
}
async function loadSession() {
  try {
    session.value = await $fetch("devices/displays/session/", {
      baseURL: config.public.apiBaseUrl,
      headers: { "X-Device-Token": deviceToken.value },
    });
  } catch {
    localStorage.removeItem("pixelcore_signage_token");
    deviceToken.value = "";
    session.value = null;
  }
}
</script>
