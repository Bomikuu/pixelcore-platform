import assert from "node:assert/strict";
import test from "node:test";
import {
  availableWorkspaceActions,
  loadQuickActionReferences,
  workspaceCreateRole,
} from "./workspaceQuickActions.js";

const business = {
  public_id: "selected",
  enabled_modules: ["sell", "operate"],
};
const manager = {
  businesses: [
    { public_id: "other", role: "owner" },
    { public_id: "selected", role: "manager" },
  ],
};

test("quick actions use the selected membership and enabled modules", () => {
  assert.equal(availableWorkspaceActions(manager, business).length, 8);
  assert.equal(workspaceCreateRole(manager, { public_id: "other" }), "owner");
  assert.deepEqual(
    availableWorkspaceActions(
      {
        businesses: [
          { public_id: "other", role: "owner" },
          { public_id: "selected", role: "staff" },
        ],
      },
      business,
    ),
    [],
  );
  assert.deepEqual(
    availableWorkspaceActions(manager, {
      public_id: "unknown",
      role: "owner",
      enabled_modules: ["sell"],
    }),
    [],
  );
  assert.deepEqual(
    availableWorkspaceActions(manager, { public_id: "selected" }),
    [],
  );
  assert.deepEqual(
    availableWorkspaceActions(manager, {
      ...business,
      enabled_modules: ["sell"],
    }).map((action) => action.id),
    ["product", "promotion"],
  );
  assert.equal(
    availableWorkspaceActions(manager, {
      ...business,
      enabled_modules: ["operate"],
    }).length,
    6,
  );
});

test("supplier forms need no background reference requests", async () => {
  const references = await loadQuickActionReferences(
    () => assert.fail("Unexpected request"),
    "selected",
    "suppliers",
  );
  assert.deepEqual(references.suppliers, []);
});

test("invoice references include later pages and stay on the tenant endpoint", async () => {
  const calls = [];
  const signal = new AbortController().signal;
  const references = await loadQuickActionReferences(
    async (path, options) => {
      calls.push([path, options]);
      return {
        results: [{ public_id: `customer-${options.query.page}` }],
        next:
          options.query.page === 1
            ? "https://untrusted.example/never-follow-this"
            : null,
      };
    },
    "selected",
    "invoices",
    signal,
  );
  assert.equal(references.customers.length, 2);
  assert.ok(
    calls.every(
      ([path, options]) =>
        path === "businesses/selected/customers/" && options.signal === signal,
    ),
  );
  assert.deepEqual(
    calls.map(([, options]) => options.query.page),
    [1, 2],
  );
});

test("purchase order preparation loads only its required choices and active variants", async () => {
  const calls = [];
  const references = await loadQuickActionReferences(
    async (path) => {
      calls.push(path);
      if (path.endsWith("/offerings/"))
        return {
          results: [
            {
              name: "Studio kit",
              variants: [
                { public_id: "active", name: "Large", is_active: true },
                { public_id: "inactive", name: "Old", is_active: false },
              ],
            },
          ],
        };
      return { results: [] };
    },
    "selected",
    "purchase-orders",
  );
  assert.deepEqual(calls.sort(), [
    "businesses/selected/locations/",
    "businesses/selected/offerings/",
    "businesses/selected/suppliers/",
  ]);
  assert.deepEqual(references.variants, [
    { public_id: "active", label: "Studio kit · Large" },
  ]);
});

test("failed or unsupported reference preparation does not produce a partial form", async () => {
  await assert.rejects(
    loadQuickActionReferences(
      async () => {
        throw new Error("Permission changed");
      },
      "selected",
      "invoices",
    ),
    /Permission changed/,
  );
  await assert.rejects(
    loadQuickActionReferences(async () => ({}), "selected", "unknown"),
    /not available/,
  );
});
