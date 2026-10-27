import test from "node:test";
import assert from "node:assert/strict";
import {
  createDeliveryPoller,
  DELIVERY_REFRESH_MS,
  locationIsStale,
  pointCoordinates,
} from "./deliveryTracking.js";
import { accountHome } from "./accountHome.js";

function harness(load, canRun = () => true) {
  const timers = new Map();
  let id = 0;
  const poller = createDeliveryPoller({
    load,
    canRun,
    setTimer: (fn, delay) => {
      timers.set(++id, { fn, delay });
      return id;
    },
    clearTimer: (key) => timers.delete(key),
  });
  return {
    poller,
    timers,
    tick: async () => {
      const next = [...timers.values()][0];
      timers.clear();
      next?.fn();
      await new Promise((resolve) => setImmediate(resolve));
    },
  };
}

test("automatic refresh waits 30 seconds after a completed request", async () => {
  let requests = 0;
  const { poller, timers, tick } = harness(async () => {
    requests++;
  });
  await poller.refresh();
  assert.equal(requests, 1);
  assert.equal([...timers.values()][0].delay, DELIVERY_REFRESH_MS);
  assert.equal(DELIVERY_REFRESH_MS, 30000);
  await tick();
  assert.equal(requests, 2);
  poller.stop();
});
test("concurrent refreshes share one request and one timer", async () => {
  let finish,
    requests = 0;
  const { poller, timers } = harness(() => {
    requests++;
    return new Promise((resolve) => {
      finish = resolve;
    });
  });
  const a = poller.refresh(),
    b = poller.refresh();
  await Promise.resolve();
  assert.equal(requests, 1);
  assert.equal(a, b);
  finish();
  await a;
  assert.equal(timers.size, 1);
  poller.stop();
});
test("hidden or offline pages pause and can resume", async () => {
  let visible = true,
    requests = 0;
  const { poller, timers } = harness(
    async () => {
      requests++;
    },
    () => visible,
  );
  await poller.refresh();
  visible = false;
  poller.pause();
  await poller.refresh();
  assert.equal(timers.size, 0);
  assert.equal(requests, 1);
  visible = true;
  await poller.refresh();
  assert.equal(requests, 2);
  poller.stop();
});
test("unmount stops timers including an in-flight request", async () => {
  let finish;
  const { poller, timers } = harness(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const pending = poller.refresh();
  await Promise.resolve();
  poller.stop();
  finish();
  await pending;
  assert.equal(timers.size, 0);
});
test("terminal deliveries do not schedule another refresh", async () => {
  let done = false;
  const { poller, timers } = harness(
    async () => {
      done = true;
    },
    () => !done,
  );
  await poller.refresh();
  assert.equal(timers.size, 0);
});
test("transient failures can retry on the next 30-second tick", async () => {
  let attempts = 0;
  const { poller, timers } = harness(async () => {
    attempts++;
    if (attempts === 1) throw new Error("offline");
  });
  await assert.rejects(poller.refresh());
  assert.equal(timers.size, 1);
  await poller.refresh();
  assert.equal(attempts, 2);
  poller.stop();
});
test("GPS positions become stale after ninety seconds", () => {
  const now = Date.now();
  assert.equal(
    locationIsStale({ received_at: new Date(now - 90000).toISOString() }, now),
    false,
  );
  assert.equal(
    locationIsStale({ received_at: new Date(now - 90001).toISOString() }, now),
    true,
  );
  assert.equal(locationIsStale(null, now), true);
});
test("map coordinate validation preserves zero and rejects invalid points", () => {
  assert.deepEqual(pointCoordinates({ latitude: 0, longitude: 0 }), [0, 0]);
  for (const value of [
    null,
    { latitude: null, longitude: 0 },
    { latitude: 91, longitude: 0 },
    { latitude: 1, longitude: Infinity },
  ])
    assert.equal(pointCoordinates(value), null);
});
test("independent riders open the rider portal without a workspace membership", () => {
  assert.equal(
    accountHome({
      has_delivery_access: true,
      businesses: [],
      needs_onboarding: false,
    }),
    "/rider/deliveries",
  );
  assert.equal(
    accountHome({ has_delivery_access: true, businesses: [{ role: "staff" }] }),
    "/employee",
  );
  assert.equal(
    accountHome({ has_delivery_access: true, businesses: [{ role: "owner" }] }),
    "/workspace",
  );
  assert.equal(accountHome({ needs_onboarding: true }), "/onboarding");
});

test("map updates reuse markers and remove revoked or completed positions", async () => {
  const { syncDeliveryMarkers } = await import("./deliveryTracking.js");
  let created = 0,
    removed = 0;
  class Popup {
    setText(text) {
      this.text = text;
      return this;
    }
  }
  class Marker {
    constructor() {
      created++;
    }
    setLngLat(coordinates) {
      this.coordinates = coordinates;
      return this;
    }
    setPopup(popup) {
      this.popup = popup;
      return this;
    }
    getPopup() {
      return this.popup;
    }
    addTo() {
      return this;
    }
    getElement() {
      return { setAttribute() {} };
    }
    remove() {
      removed++;
    }
  }
  const markers = new Map(),
    map = {};
  const point = {
    key: "rider",
    coordinates: [121, 14],
    label: "Rider",
    color: "teal",
  };
  syncDeliveryMarkers(map, { Marker, Popup }, markers, [point]);
  const marker = markers.get("rider");
  syncDeliveryMarkers(map, { Marker, Popup }, markers, [
    { ...point, coordinates: [121.1, 14.1] },
  ]);
  assert.equal(created, 1);
  assert.equal(markers.get("rider"), marker);
  assert.deepEqual(marker.coordinates, [121.1, 14.1]);
  syncDeliveryMarkers(map, { Marker, Popup }, markers, []);
  assert.equal(removed, 1);
  assert.equal(markers.size, 0);
});
