import { createDeliveryPoller, deliveryError } from "~/utils/deliveryTracking";

export function useRiderLocation(delivery) {
  const { apiFetch } = useApiClient();
  const sharing = ref(false);
  const busy = ref(false);
  const error = ref("");
  const lastSent = ref(null);
  let session;
  let pendingSession;
  let poller;
  let generation = 0;
  const available = () =>
    document.visibilityState !== "hidden" && navigator.onLine !== false;
  const position = () =>
    new Promise((resolve, reject) => {
      if (!navigator.geolocation)
        return reject(new Error("This browser does not support GPS location."));
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 12000,
      });
    });
  const gpsMessage = (failure) =>
    failure?.code === 1
      ? "Location permission was denied. Enable location access in your browser and try again."
      : failure?.code === 2 || failure?.code === 3
        ? "A GPS position is unavailable. Move somewhere with a clearer signal and retry."
        : failure?.message && !failure?.data
          ? failure.message
          : deliveryError(failure);

  async function send(fix, capturedSession) {
    const result = await apiFetch(
      `rider/deliveries/${capturedSession.id}/location/`,
      {
        method: "POST",
        body: {
          revision: capturedSession.revision,
          latitude: fix.coords.latitude,
          longitude: fix.coords.longitude,
          accuracy: fix.coords.accuracy,
          captured_at: new Date(fix.timestamp).toISOString(),
        },
      },
    );
    lastSent.value = result.received_at;
  }
  async function stop() {
    ++generation;
    poller?.stop();
    const previous = session;
    session = null;
    sharing.value = false;
    if (previous) {
      try {
        await apiFetch(`rider/deliveries/${previous.id}/`, {
          method: "PATCH",
          body: {
            action: "sharing",
            sharing: false,
            revision: previous.revision,
          },
          keepalive: true,
        });
      } catch (failure) {
        if (
          [403, 404, 409].includes(
            failure?.statusCode || failure?.response?.status,
          )
        )
          return;
        error.value =
          "GPS uploads stopped. The server could not confirm stopping sharing; the last position will be marked stale.";
      }
    }
  }
  async function start() {
    if (
      busy.value ||
      sharing.value ||
      !delivery.value ||
      delivery.value.stage !== "out_for_delivery"
    )
      return;
    const version = ++generation;
    const current = {
      id: delivery.value.public_id,
      revision: delivery.value.revision,
    };
    pendingSession = current;
    busy.value = true;
    error.value = "";
    try {
      const fix = await position();
      if (version !== generation || !available()) return;
      await apiFetch(`rider/deliveries/${current.id}/`, {
        method: "PATCH",
        body: { action: "sharing", sharing: true, revision: current.revision },
      });
      session = current;
      if (version !== generation) {
        await stop();
        return;
      }
      await send(fix, current);
      if (version !== generation) return;
      sharing.value = true;
      poller = createDeliveryPoller({
        canRun: () => Boolean(session) && available(),
        load: async () => {
          try {
            const next = await position();
            if (version !== generation || !available()) return;
            await send(next, current);
            error.value = "";
          } catch (failure) {
            error.value = gpsMessage(failure);
            if (
              [403, 404, 409].includes(
                failure?.statusCode || failure?.response?.status,
              )
            )
              await stop();
          }
        },
      });
      poller.schedule();
    } catch (failure) {
      error.value = gpsMessage(failure);
      if (session) await stop();
    } finally {
      pendingSession = null;
      busy.value = false;
    }
  }
  function visibility() {
    if (!available()) poller?.pause();
    else poller?.schedule();
  }
  watch(
    () =>
      [
        delivery.value?.public_id,
        delivery.value?.revision,
        delivery.value?.stage,
      ].join(":"),
    () => {
      const active = session || pendingSession;
      if (
        active &&
        (delivery.value?.public_id !== active.id ||
          delivery.value?.revision !== active.revision ||
          delivery.value?.stage !== "out_for_delivery")
      )
        void stop();
    },
  );
  onMounted(() => {
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("online", visibility);
    window.addEventListener("offline", visibility);
  });
  onBeforeUnmount(() => {
    void stop();
    document.removeEventListener("visibilitychange", visibility);
    window.removeEventListener("online", visibility);
    window.removeEventListener("offline", visibility);
  });
  return { sharing, busy, error, lastSent, start, stop };
}
