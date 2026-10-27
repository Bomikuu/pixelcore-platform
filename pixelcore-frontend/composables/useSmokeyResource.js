import { createSmokeyClient } from "~/utils/smokeyAssistant";

export function useSmokeyResource(path) {
  const business = useBusinessStore();
  const { apiFetch } = useApiClient();
  const data = ref(null),
    error = ref(""),
    loading = ref(false);
  let epoch = 0;
  const request = (suffix, options = {}) =>
    createSmokeyClient(apiFetch, business.activeBusiness?.public_id).request(
      suffix,
      options,
    );
  async function refresh() {
    const token = ++epoch;
    if (
      !toValue(path) ||
      !business.activeBusiness?.enabled_modules?.includes("smokey")
    ) {
      data.value = null;
      loading.value = false;
      return;
    }
    loading.value = true;
    error.value = "";
    try {
      const value = await request(toValue(path));
      if (token === epoch) data.value = value;
    } catch (issue) {
      if (token === epoch)
        error.value =
          issue?.data?.error?.message ||
          "Could not load Smokey. Please try again.";
    } finally {
      if (token === epoch) loading.value = false;
    }
  }
  watch(
    [
      () => business.activeBusiness?.public_id,
      () => business.activeBusiness?.enabled_modules?.includes("smokey"),
      () => toValue(path),
    ],
    () => {
      epoch++;
      data.value = null;
      error.value = "";
      refresh();
    },
    { immediate: true },
  );
  onScopeDispose(() => {
    epoch++;
  });
  return { data, error, loading, refresh, request };
}
