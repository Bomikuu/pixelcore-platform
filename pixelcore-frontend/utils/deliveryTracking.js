export const DELIVERY_REFRESH_MS = 30_000;
export const DELIVERY_STALE_MS = 90_000;
export const deliveryStages = {
  preparing: "Preparing",
  ready: "Ready for pickup",
  out_for_delivery: "Out for delivery",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

export function locationIsStale(point, now = Date.now()) {
  const received = Date.parse(point?.received_at || "");
  return !Number.isFinite(received) || now - received > DELIVERY_STALE_MS;
}

export function pointCoordinates(point) {
  if (point?.latitude == null || point?.longitude == null) return null;
  const lat = Number(point.latitude);
  const lng = Number(point.longitude);
  return Number.isFinite(lat) &&
    Number.isFinite(lng) &&
    Math.abs(lat) <= 90 &&
    Math.abs(lng) <= 180
    ? [lng, lat]
    : null;
}

export function deliveryError(error) {
  const details = error?.data?.error?.details || error?.data;
  const detail =
    details &&
    Object.values(details).find(
      (value) => typeof value === "string" || Array.isArray(value),
    );
  return (
    error?.data?.error?.message ||
    (Array.isArray(detail) ? detail[0] : detail) ||
    "The delivery could not be updated. Refresh and try again."
  );
}

/** One request at a time; schedule from completion, never accumulate interval ticks. */
export function createDeliveryPoller({
  load,
  canRun = () => true,
  setTimer = setTimeout,
  clearTimer = clearTimeout,
}) {
  let timer;
  let pending;
  let disposed = false;
  function pause() {
    clearTimer(timer);
    timer = undefined;
  }
  function schedule() {
    pause();
    if (!disposed && canRun())
      timer = setTimer(() => {
        void refresh();
      }, DELIVERY_REFRESH_MS);
  }
  function refresh() {
    pause();
    if (disposed || !canRun()) return Promise.resolve();
    if (pending) return pending;
    pending = Promise.resolve()
      .then(load)
      .finally(() => {
        pending = null;
        schedule();
      });
    return pending;
  }
  function stop() {
    disposed = true;
    pause();
  }
  return { refresh, pause, schedule, stop };
}

/** Mutate existing map markers without creating another map or requesting a static image. */
export function syncDeliveryMarkers(map, library, markers, points) {
  const wanted = new Set(points.map((point) => point.key));
  for (const [key, marker] of markers) {
    if (!wanted.has(key)) {
      marker.remove();
      markers.delete(key);
    }
  }
  for (const point of points) {
    let marker = markers.get(point.key);
    if (!marker) {
      marker = new library.Marker({ color: point.color })
        .setLngLat(point.coordinates)
        .setPopup(new library.Popup({ offset: 25 }).setText(point.label))
        .addTo(map);
      marker.getElement().setAttribute("aria-label", point.label);
      markers.set(point.key, marker);
    } else {
      marker.setLngLat(point.coordinates);
      marker.getPopup().setText(point.label);
      marker.getElement().setAttribute("aria-label", point.label);
    }
  }
}
