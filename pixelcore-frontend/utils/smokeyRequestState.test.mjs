import test from "node:test";
import assert from "node:assert/strict";
import { createSmokeyRequestController } from "./smokeyRequestState.js";

test("business switch discards an earlier pending result", async () => {
  let resolve;
  const states = [];
  const controller = createSmokeyRequestController({
    onChange: (value) => states.push(value),
    newKey: () => "key",
  });
  controller.setBusiness({
    start: () =>
      new Promise((done) => {
        resolve = done;
      }),
  });
  const pending = controller.submit("Old business");
  controller.setBusiness({});
  resolve({ state: "succeeded", report_id: "private" });
  await pending;
  assert.equal(states.at(-1).state, "idle");
  assert.equal(
    states.some((item) => item.report_id === "private"),
    false,
  );
});
test("duplicate submissions are suppressed and terminal states stop polling", async () => {
  let calls = 0,
    timer;
  const controller = createSmokeyRequestController({
    onChange: () => {},
    newKey: () => "key",
    schedule: (callback) => {
      timer = callback;
      return 1;
    },
    unschedule: () => {},
  });
  controller.setBusiness({
    start: async () => {
      calls++;
      return { id: "one", state: "queued" };
    },
    poll: async () => ({ id: "one", state: "succeeded" }),
  });
  await controller.submit("Today");
  await controller.submit("Again");
  assert.equal(calls, 1);
  const poll = timer;
  timer = null;
  await poll();
  assert.equal(timer, null);
});
test("recovering an uncertain submission reuses its idempotency key", async () => {
  const keys = [];
  const controller = createSmokeyRequestController({
    onChange: () => {},
    newKey: () => "same-key",
  });
  controller.setBusiness({
    start: async (_, key) => {
      keys.push(key);
      if (keys.length === 1) throw Error("Offline");
      return { state: "succeeded" };
    },
  });
  await controller.submit("Today");
  await controller.resume();
  assert.deepEqual(keys, ["same-key", "same-key"]);
});
test("stop requested before creation returns cancels the resulting request", async () => {
  let resolve,
    stopped = 0;
  const states = [];
  const controller = createSmokeyRequestController({
    onChange: (value) => states.push(value),
    newKey: () => "key",
  });
  controller.setBusiness({
    start: () =>
      new Promise((done) => {
        resolve = done;
      }),
    stop: async () => {
      stopped++;
      return { state: "cancelled" };
    },
  });
  const pending = controller.submit("Today");
  await controller.stop();
  resolve({ id: "one", state: "queued" });
  await pending;
  assert.equal(stopped, 1);
  assert.equal(states.at(-1).state, "cancelled");
});

test("a stop survives recovery after an uncertain creation response", async () => {
  let reject,
    starts = 0,
    stopped = 0;
  const states = [];
  const controller = createSmokeyRequestController({
    onChange: (value) => states.push(value),
    newKey: () => "same-key",
  });
  controller.setBusiness({
    start: () => {
      starts++;
      return starts === 1
        ? new Promise((_, fail) => {
            reject = fail;
          })
        : Promise.resolve({ id: "one", state: "queued" });
    },
    stop: async () => {
      stopped++;
      return { state: "cancelled" };
    },
  });
  const first = controller.submit("Today");
  await controller.stop();
  reject(Error("Connection lost"));
  await first;
  await controller.resume();
  assert.equal(stopped, 1);
  assert.equal(states.at(-1).state, "cancelled");
});
