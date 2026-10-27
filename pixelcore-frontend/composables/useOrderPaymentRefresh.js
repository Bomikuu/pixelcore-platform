import { onScopeDispose, watch } from "vue";

/** Keep the existing 2.5-second payment confirmation cadence, including delayed client data. */
export function useOrderPaymentRefresh(order, refresh, timers = {}) {
  const setTimer = timers.setTimer || setTimeout;
  const clearTimer = timers.clearTimer || clearTimeout;
  let timer;
  let running = false;
  let disposed = false;
  function schedule() {
    clearTimer(timer);
    if (!disposed && !running && order.value?.payment_status === "pending")
      timer = setTimer(tick, 2500);
  }
  async function tick() {
    if (disposed || running || order.value?.payment_status !== "pending")
      return;
    running = true;
    try {
      await refresh();
    } catch {
      /* useAsyncData owns the visible request error. */
    } finally {
      running = false;
      schedule();
    }
  }
  watch(() => order.value?.payment_status, schedule, { immediate: true });
  onScopeDispose(() => {
    disposed = true;
    clearTimer(timer);
  });
}
