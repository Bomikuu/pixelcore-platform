import test from "node:test";
import assert from "node:assert/strict";
import {
  createPixelCoreSmokeyAdapter,
  pixelCoreSmokeyOperation,
} from "./smokeyHostAdapter.js";
const id = "11111111-1111-4111-8111-111111111111";
const identity = {
  hostId: "pixelcore",
  organizationId: id,
  actorId: "1",
  revision: 1,
};
const input = (operation) => ({
  operation,
  identity,
  params: {
    connectionId: id,
    reportId: id,
    generationId: id,
    tableKey: "attendance",
  },
});
test("report row search and page sizes survive the host adapter with validation", () => {
  const request = input("reports.rows");
  const path = pixelCoreSmokeyOperation({
    ...request,
    params: {
      ...request.params,
      search: "Tote / blue: large",
      page_size: 20,
      offset: 20,
    },
  }).path;
  const url = new URL(path, "https://example.test");
  assert.equal(url.searchParams.get("search"), "Tote / blue: large");
  assert.equal(url.searchParams.get("page_size"), "20");
  assert.equal(url.searchParams.get("offset"), "20");
  assert.throws(
    () =>
      pixelCoreSmokeyOperation({
        ...request,
        params: { ...request.params, page_size: 999 },
      }),
    { code: "INVALID_PARAMETER" },
  );
  assert.throws(
    () =>
      pixelCoreSmokeyOperation({
        ...request,
        params: { ...request.params, search: "a".repeat(101) },
      }),
    { code: "INVALID_PARAMETER" },
  );
});
test("all operations use captured business paths and explicit HTTP methods", () => {
  const operations = {
    "integration.get": "GET",
    "module.enable": "PATCH",
    "settings.get": "GET",
    "settings.update": "PATCH",
    "connections.list": "GET",
    "connections.create": "POST",
    "connections.update": "PATCH",
    "connections.delete": "DELETE",
    "connections.models": "GET",
    "connections.check": "POST",
    "models.discover": "POST",
    "generations.create": "POST",
    "generations.get": "GET",
    "generations.cancel": "POST",
    "reports.list": "GET",
    "reports.get": "GET",
    "reports.rows": "GET",
    "reports.delete": "DELETE",
    "usage.get": "GET",
    "asset.get": "GET",
    "asset.upload": "POST",
  };
  for (const [name, method] of Object.entries(operations)) {
    const operation = pixelCoreSmokeyOperation(input(name));
    assert.equal(operation.method, method);
    assert.ok(operation.path.startsWith("businesses/" + id + "/"));
  }
  assert.throws(() => pixelCoreSmokeyOperation(input("https://evil.test")), {
    code: "INVALID_OPERATION",
  });
  assert.throws(
    () =>
      pixelCoreSmokeyOperation({
        ...input("reports.get"),
        params: { reportId: "../auth" },
      }),
    { code: "INVALID_PARAMETER" },
  );
  assert.throws(
    () =>
      pixelCoreSmokeyOperation({
        ...input("reports.rows"),
        params: { reportId: id, tableKey: "../secret" },
      }),
    { code: "INVALID_PARAMETER" },
  );
});
test("late old-context result is rejected; binary and void values are retained", async () => {
  let current = { identity };
  let resolve;
  const pending = new Promise((yes) => {
    resolve = yes;
  });
  const adapter = createPixelCoreSmokeyAdapter({
    apiFetch: () => pending,
    currentContext: () => current,
    navigate() {},
    sourceOrigin: "http://localhost",
  });
  const result = adapter.request(input("settings.get"));
  current = { identity: { ...identity, actorId: "2", revision: 2 } };
  resolve({ private: "old" });
  await assert.rejects(result, { code: "STALE_CONTEXT" });
  for (const value of [undefined, new Blob(["private"])]) {
    const client = createPixelCoreSmokeyAdapter({
      apiFetch: async () => value,
      currentContext: () => ({ identity }),
      navigate() {},
      sourceOrigin: "http://localhost",
    });
    assert.equal(
      await client.request(input(value ? "asset.get" : "connections.delete")),
      value,
    );
  }
});
test("only generation creation forwards idempotency, never browser-supplied auth headers", async () => {
  const calls = [];
  const adapter = createPixelCoreSmokeyAdapter({
    apiFetch: async (path, options) => {
      calls.push({ path, options });
    },
    currentContext: () => ({ identity }),
    navigate() {},
    sourceOrigin: "http://localhost",
  });
  await adapter.request({
    ...input("generations.create"),
    idempotencyKey: "stable",
    headers: { Authorization: "untrusted" },
  });
  assert.deepEqual(calls[0].options.headers, { "Idempotency-Key": "stable" });
  await adapter.request({
    ...input("connections.check"),
    idempotencyKey: "not-used",
  });
  assert.deepEqual(calls[1].options.headers, {});
  assert.equal(
    adapter.resolveSourceLink({ href: "javascript:alert(1)" }),
    null,
  );
  assert.equal(adapter.resolveSourceLink({ href: "//evil.test" }), null);
  assert.equal(
    adapter.resolveSourceLink({ href: "/workspace/orders" }),
    "http://localhost/workspace/orders",
  );
});

test("late private asset and upload results are rejected after a business switch", async () => {
  for (const operation of ["asset.get", "asset.upload"]) {
    let current = { identity },
      finish;
    const response = new Promise((resolve) => {
      finish = resolve;
    });
    const adapter = createPixelCoreSmokeyAdapter({
      apiFetch: () => response,
      currentContext: () => current,
      navigate() {},
      sourceOrigin: "http://localhost",
    });
    const pending = adapter.request({
      ...input(operation),
      ...(operation === "asset.upload" ? { body: new FormData() } : {}),
    });
    current = {
      identity: {
        ...identity,
        organizationId: "22222222-2222-4222-8222-222222222222",
        revision: 2,
      },
    };
    finish(
      operation === "asset.get"
        ? new Blob(["private"], { type: "image/webp" })
        : { uploaded: true },
    );
    await assert.rejects(pending, { code: "STALE_CONTEXT" });
  }
});
