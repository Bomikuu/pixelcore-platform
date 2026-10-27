import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = (
  await readFile(new URL("./useRiderLocation.js", import.meta.url), "utf8")
)
  .replace(/^import .*;\n/gm, "")
  .replace("export function useRiderLocation", "function useRiderLocation");

function setup(api) {
  let receiveFix, changed;
  const calls = [];
  const env = {
    ref: (value) => ({ value }),
    useApiClient: () => ({
      apiFetch: async (path, options) => {
        calls.push({ path, ...options });
        return api
          ? api(path, options)
          : { received_at: new Date().toISOString() };
      },
    }),
    document: {
      visibilityState: "visible",
      addEventListener() {},
      removeEventListener() {},
    },
    navigator: {
      onLine: true,
      geolocation: {
        getCurrentPosition(resolve) {
          receiveFix = resolve;
        },
      },
    },
    window: { addEventListener() {}, removeEventListener() {} },
    watch: (_getter, callback) => {
      changed = callback;
    },
    onMounted() {},
    onBeforeUnmount() {},
    createDeliveryPoller: () => ({ schedule() {}, stop() {}, pause() {} }),
    deliveryError: () => "Request failed",
  };
  const useRiderLocation = new Function(
    ...Object.keys(env),
    source + "\nreturn useRiderLocation;",
  )(...Object.values(env));
  const selected = {
    value: { public_id: "job-a", revision: 1, stage: "out_for_delivery" },
  };
  const gps = useRiderLocation(selected);
  return {
    gps,
    selected,
    calls,
    switchJob: () => {
      selected.value = {
        public_id: "job-b",
        revision: 1,
        stage: "out_for_delivery",
      };
      changed();
    },
    resolveFix: () =>
      receiveFix({
        coords: { latitude: 14.6, longitude: 121, accuracy: 5 },
        timestamp: Date.now(),
      }),
  };
}

test("switching delivery during GPS permission invalidates the pending startup", async () => {
  const { gps, switchJob, resolveFix, calls } = setup();
  const pending = gps.start();
  assert.equal(gps.busy.value, true);
  switchJob();
  assert.equal(gps.busy.value, true); // A second startup must wait for the old permission request.
  await gps.start();
  resolveFix();
  await pending;
  assert.equal(gps.sharing.value, false);
  assert.equal(gps.busy.value, false);
  assert.deepEqual(calls, []);
});

test("changing jobs during sharing authorization clears the original server session", async () => {
  let authorize;
  const pendingAuthorization = new Promise((resolve) => {
    authorize = resolve;
  });
  const ctx = setup((_path, options) =>
    options.body.sharing === true ? pendingAuthorization : {},
  );
  const pending = ctx.gps.start();
  ctx.resolveFix();
  await Promise.resolve();
  await Promise.resolve();
  assert.equal(ctx.calls.length, 1);
  ctx.switchJob();
  authorize({});
  await pending;
  assert.deepEqual(
    ctx.calls.map((call) => call.body.sharing),
    [true, false],
  );
  assert.equal(
    ctx.calls.every((call) => call.path.includes("job-a")),
    true,
  );
  assert.equal(ctx.gps.sharing.value, false);
  assert.equal(ctx.gps.busy.value, false);
});
