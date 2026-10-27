import assert from "node:assert/strict";
import test from "node:test";
import { effectScope, nextTick, ref } from "vue";
import { useOrderPaymentRefresh } from "./useOrderPaymentRefresh.js";

function setup(order, refresh) {
  const callbacks = new Map();
  let id = 0;
  const scope = effectScope();
  scope.run(() =>
    useOrderPaymentRefresh(order, refresh, {
      setTimer: (fn, delay) => {
        callbacks.set(++id, { fn, delay });
        return id;
      },
      clearTimer: (key) => callbacks.delete(key),
    }),
  );
  return {
    callbacks,
    scope,
    tick: async () => {
      const callback = [...callbacks.values()][0];
      callbacks.clear();
      await callback?.fn();
    },
  };
}

test("payment polling starts when client data resolves after setup", async () => {
  const order = ref(null);
  let requests = 0;
  const ctx = setup(order, async () => {
    requests++;
  });
  assert.equal(ctx.callbacks.size, 0);
  order.value = { payment_status: "pending" };
  await nextTick();
  assert.equal([...ctx.callbacks.values()][0].delay, 2500);
  await ctx.tick();
  assert.equal(requests, 1);
  ctx.scope.stop();
});
test("payment refreshes do not overlap and stop after paid", async () => {
  const order = ref({ payment_status: "pending" });
  let resolve,
    requests = 0;
  const ctx = setup(order, () => {
    requests++;
    return new Promise((done) => {
      resolve = done;
    });
  });
  const running = ctx.tick();
  assert.equal(requests, 1);
  assert.equal(ctx.callbacks.size, 0);
  order.value = { payment_status: "paid" };
  await nextTick();
  resolve();
  await running;
  assert.equal(ctx.callbacks.size, 0);
  ctx.scope.stop();
});
test("leaving a confirmation page cancels polling even during a request", async () => {
  let resolve;
  const ctx = setup(
    ref({ payment_status: "pending" }),
    () =>
      new Promise((done) => {
        resolve = done;
      }),
  );
  const running = ctx.tick();
  ctx.scope.stop();
  resolve();
  await running;
  assert.equal(ctx.callbacks.size, 0);
});
