import { createSmokeyClient } from "./smokeyAssistant.js";
import { createSmokeyRequestController } from "./smokeyRequestState.js";
// Temporary migration fallback, removed only after the module cutover acceptance gates.
export const createLegacySmokeyClient = (app, business, apiFetch) => {
  const state = ref({ state: "idle" }),
    config = ref(null),
    asset = ref(null),
    opened = ref(false);
  let epoch = 0,
    client;
  const controller = createSmokeyRequestController({
    onChange: (value) => {
      state.value = value;
    },
  });
  const refresh = async () => {
    const token = ++epoch,
      id = business.activeBusiness?.public_id;
    if (!id || !business.activeBusiness?.enabled_modules?.includes("smokey")) {
      config.value = null;
      return;
    }
    const source = createSmokeyClient(apiFetch, id),
      next = await source.request("settings/");
    if (token !== epoch) return;
    config.value = next;
    if (asset.value) URL.revokeObjectURL(asset.value);
    asset.value = null;
    if (next.has_mascot_asset && next.mascot?.mode === "custom") {
      const blob = await source.request("asset/", { responseType: "blob" });
      if (token === epoch) asset.value = URL.createObjectURL(blob);
    }
  };
  watch(
    () => business.activeBusiness?.public_id,
    (id) => {
      epoch++;
      opened.value = false;
      config.value = null;
      if (asset.value) URL.revokeObjectURL(asset.value);
      asset.value = null;
      client = id ? createSmokeyClient(apiFetch, id) : null;
      controller.setBusiness(client);
      refresh().catch(() => {});
    },
    { immediate: true },
  );
  watch(
    () => business.activeBusiness?.enabled_modules?.includes("smokey"),
    (enabled) => {
      if (enabled) {
        controller.setBusiness(client);
        refresh().catch(() => {});
      } else {
        epoch++;
        config.value = null;
        opened.value = false;
        controller.setBusiness(null);
      }
    },
  );
  app.hook("app:beforeUnmount", () => {
    controller.dispose();
    if (asset.value) URL.revokeObjectURL(asset.value);
  });
  return { state, config, asset, opened, refresh, controller };
};
