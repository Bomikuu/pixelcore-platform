import assert from "node:assert/strict";
import test from "node:test";
import { readOrderAccess, rememberOrderAccess } from "./orderAccess.js";
const order = "00000000-0000-4000-8000-000000000001";
const storage = () => {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) || null,
    setItem: (key, value) => values.set(key, value),
  };
};

test("a new cart never overwrites an earlier order's guest authorization", () => {
  const store = storage();
  rememberOrderAccess(
    store,
    "shop-a",
    order,
    "original-cart-token-for-order",
    1000,
  );
  store.setItem(
    "pixelcore-cart:shop-a",
    JSON.stringify({ token: "new-cart-token" }),
  );
  assert.equal(
    readOrderAccess(store, "shop-a", order, 2000),
    "original-cart-token-for-order",
  );
  assert.equal(readOrderAccess(store, "shop-b", order, 2000), "");
});
test("guest tokens expire after 30 days and keep only 20 orders", () => {
  const store = storage();
  for (let i = 1; i <= 21; i++)
    rememberOrderAccess(
      store,
      "shop",
      `00000000-0000-4000-8000-${String(i).padStart(12, "0")}`,
      `cart-token-number-${i}`,
      i,
    );
  assert.equal(readOrderAccess(store, "shop", order, 30), "");
  const last = "00000000-0000-4000-8000-000000000021";
  assert.equal(
    readOrderAccess(store, "shop", last, 30),
    "cart-token-number-21",
  );
  assert.equal(readOrderAccess(store, "shop", last, 30 * 86400000 + 21), "");
});
test("blocked or corrupt storage never fails checkout or accepts invalid tokens", () => {
  const blocked = {
    getItem() {
      throw new Error("blocked");
    },
    setItem() {
      throw new Error("blocked");
    },
  };
  assert.equal(
    rememberOrderAccess(blocked, "shop", order, "valid-synthetic-token"),
    false,
  );
  assert.equal(readOrderAccess(blocked, "shop", order), "");
  const corrupt = storage();
  corrupt.setItem("pixelcore-order-access:shop", "{bad");
  assert.equal(readOrderAccess(corrupt, "shop", order), "");
  assert.equal(
    rememberOrderAccess(corrupt, "shop", "invalid", "valid-synthetic-token"),
    false,
  );
});
