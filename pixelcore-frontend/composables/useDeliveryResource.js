import { createDeliveryPoller, deliveryError } from "~/utils/deliveryTracking";

export function useDeliveryResource(endpoint, options = {}) {
  const { apiFetch } = useApiClient();
  const data = ref(null);
  const busy = ref(false);
  const error = ref("");
  const lastUpdated = ref(null);
  const paused = ref(false);
  let poller;
  let controller;
  let generation = 0;
  let stopWatch;
  const available = () =>
    document.visibilityState !== "hidden" && navigator.onLine !== false;

  function restart() {
    const version = ++generation;
    poller?.stop();
    controller?.abort();
    data.value = null;
    error.value = "";
    busy.value = false;
    lastUpdated.value = null;
    const path = unref(endpoint);
    if (!path) return;
    poller = createDeliveryPoller({
      canRun: () => available() && !options.terminal?.(data.value),
      load: async () => {
        controller = new AbortController();
        busy.value = true;
        try {
          const result = await (options.fetcher || apiFetch)(path, {
            signal: controller.signal,
          });
          if (version !== generation) return;
          data.value = result;
          lastUpdated.value = new Date();
          error.value = "";
        } catch (failure) {
          if (version === generation && failure?.name !== "AbortError")
            error.value = deliveryError(failure);
        } finally {
          if (version === generation) busy.value = false;
        }
      },
    });
    paused.value = !available();
    void poller.refresh();
  }
  function visibility() {
    paused.value = !available();
    if (paused.value) poller?.pause();
    else void poller?.refresh();
  }
  onMounted(() => {
    stopWatch = watch(() => unref(endpoint), restart, { immediate: true });
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("online", visibility);
    window.addEventListener("offline", visibility);
  });
  onBeforeUnmount(() => {
    ++generation;
    stopWatch?.();
    poller?.stop();
    controller?.abort();
    document.removeEventListener("visibilitychange", visibility);
    window.removeEventListener("online", visibility);
    window.removeEventListener("offline", visibility);
  });
  async function refresh() {
    const current = poller;
    if (busy.value) await current?.refresh();
    if (current === poller) await current?.refresh();
  }
  return { data, busy, error, lastUpdated, paused, refresh };
}
