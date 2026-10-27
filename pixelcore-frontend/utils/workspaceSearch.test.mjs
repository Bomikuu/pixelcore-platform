import assert from "node:assert/strict";
import test from "node:test";
import {
  workspaceRecordGroups,
  workspaceSearchScopes,
} from "./workspaceSearch.js";

const business = {
  public_id: "selected",
  enabled_modules: ["sell", "operate"],
};
const user = (role) => ({ businesses: [{ public_id: "selected", role }] });

test("record search respects module access and private employee destination roles", () => {
  assert.equal(workspaceSearchScopes(user("owner"), business).length, 4);
  assert.equal(workspaceSearchScopes(user("admin"), business).length, 4);
  assert.deepEqual(
    workspaceSearchScopes(user("manager"), business).map((kind) => kind.id),
    ["products", "promotions", "categories"],
  );
  assert.equal(workspaceSearchScopes(user("staff"), business).length, 3);
  assert.deepEqual(
    workspaceSearchScopes(user("owner"), { ...business, public_id: "other" }),
    [],
  );
  assert.deepEqual(
    workspaceSearchScopes(user("owner"), { ...business, enabled_modules: [] }),
    [],
  );
});

test("records open canonical existing pages and use distinct command item IDs", () => {
  const scopes = workspaceSearchScopes(user("owner"), business);
  const groups = workspaceRecordGroups(
    {
      groups: scopes.map((kind) => ({
        kind: kind.id,
        items: [{ public_id: "same-id", name: "Record", detail: "Code" }],
      })),
    },
    scopes,
  );
  assert.deepEqual(
    groups.map((group) => group.items[0].to),
    [
      "/workspace/sell/catalog/same-id",
      "/workspace/sell/promotions/same-id",
      "/workspace/sell/categories?edit=same-id",
      "/workspace/operate/workforce/employees/same-id",
    ],
  );
  assert.equal(new Set(groups.map((group) => group.items[0].id)).size, 4);
});

test("unknown or disallowed result groups cannot produce links", () => {
  const scopes = workspaceSearchScopes(user("staff"), business);
  const groups = workspaceRecordGroups(
    {
      groups: [
        {
          kind: "employees",
          items: [{ public_id: "private", name: "Employee" }],
        },
        {
          kind: "products",
          items: [
            { name: "Missing ID" },
            { public_id: "../x?edit=y", name: "Encoded" },
          ],
        },
      ],
    },
    scopes,
  );
  assert.equal(groups.flatMap((group) => group.items).length, 1);
  assert.equal(
    groups[0].items[0].to,
    "/workspace/sell/catalog/..%2Fx%3Fedit%3Dy",
  );
  assert.deepEqual(
    workspaceRecordGroups(null, scopes).flatMap((group) => group.items),
    [],
  );
});
