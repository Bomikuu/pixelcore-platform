import test from "node:test";
import assert from "node:assert/strict";
import { parseSmokeyRoute, smokeyRoutePath } from "./smokeyModuleRoutes.js";
import { createSmokeyModuleLifecycle } from "./smokeyModuleLifecycle.js";
const context = (org, revision = 1) => ({
  identity: {
    hostId: "pixelcore",
    organizationId: org,
    actorId: "1",
    revision,
  },
  theme: "light",
});
test("one pending load mounts only latest identity and reuses runtime across routes", async () => {
  let finish,
    loads = 0,
    mounts = 0,
    destroys = 0;
  const contexts = [],
    routes = [];
  const pending = new Promise((resolve) => {
    finish = resolve;
  });
  const lifecycle = createSmokeyModuleLifecycle({
    load: async () => {
      loads++;
      return pending;
    },
    mount: (_loaded, ctx) => {
      mounts++;
      contexts.push(ctx);
      return {
        updateContext: (ctx) => contexts.push(ctx),
        attachDashboard: (_el, route) => routes.push(route),
        detachDashboard() {},
        toggleAssistant() {},
        setHostOverlayActive() {},
        destroy: () => destroys++,
      };
    },
  });
  const first = lifecycle.updateContext(context("A"));
  const second = lifecycle.updateContext(context("B", 2));
  finish({});
  await Promise.all([first, second]);
  assert.equal(loads, 1);
  assert.equal(mounts, 1);
  assert.equal(contexts[0].identity.organizationId, "B");
  lifecycle.attachDashboard({}, { section: "reports", reportId: "saved" });
  lifecycle.detachDashboard();
  lifecycle.attachDashboard({}, { section: "usage" });
  assert.equal(mounts, 1);
  assert.equal(routes.length, 2);
  await lifecycle.updateContext({ ...context("B", 2), theme: "dark" });
  assert.equal(mounts, 1);
  lifecycle.destroy();
  assert.equal(destroys, 1);
});
test("logout while loading prevents late mount and a later session can retry", async () => {
  let finish,
    mounts = 0;
  const pending = new Promise((resolve) => {
    finish = resolve;
  });
  const lifecycle = createSmokeyModuleLifecycle({
    load: () => pending,
    mount: () => {
      mounts++;
      return { destroy() {} };
    },
  });
  const loading = lifecycle.updateContext(context("A"));
  lifecycle.destroy();
  finish({});
  await loading;
  assert.equal(mounts, 0);
});

test("load failure can retry and an already-open host overlay suppresses chat on mount", async () => {
  let attempts = 0,
    suppressed = false;
  const lifecycle = createSmokeyModuleLifecycle({
    load: async () => {
      if (++attempts === 1) throw new Error("Offline");
      return {};
    },
    mount: () => ({
      updateContext() {},
      setHostOverlayActive: (active) => {
        suppressed = active;
      },
      destroy() {},
    }),
  });
  lifecycle.setHostOverlayActive(true);
  await lifecycle.updateContext(context("A"));
  assert.equal(lifecycle.getSnapshot().ready, false);
  assert.match(lifecycle.getSnapshot().error, /Offline/);
  await lifecycle.retry();
  assert.equal(lifecycle.getSnapshot().ready, true);
  assert.equal(suppressed, true);
  assert.equal(attempts, 2);
  lifecycle.destroy();
});

test("all six sections and saved report URLs round-trip without a second navigation", () => {
  const reportId = "d51ab7b1-ef20-564f-b7cf-45ca445828c5";
  for (const route of [
    ...[
      "overview",
      "assistant",
      "reports",
      "connections",
      "appearance",
      "usage",
    ].map((section) => ({ section })),
    { section: "reports", reportId },
  ])
    assert.deepEqual(parseSmokeyRoute(smokeyRoutePath(route)), route);
  assert.equal(
    smokeyRoutePath({ section: "https://evil.test" }),
    "/workspace/smokey",
  );
  assert.deepEqual(parseSmokeyRoute("/workspace/smokey/reports/../secret"), {
    section: "reports",
  });
});
