import test from "node:test";
import assert from "node:assert/strict";
import { mascotPresentation, createSmokeyClient } from "./smokeyAssistant.js";

test("mascot feedback reflects actual source and phase", () => {
  assert.equal(
    mascotPresentation("searching", "attendance").label,
    "Checking attendance records…",
  );
  assert.equal(mascotPresentation("generating").state, "generating");
  assert.equal(mascotPresentation("cancelled").busy, false);
  assert.equal(
    mascotPresentation("searching", "daily", false).label,
    "Understanding your report request…",
  );
});
test("every request is scoped to the selected business", async () => {
  const calls = [];
  const api = createSmokeyClient(async (...args) => calls.push(args), "one");
  await api.start({ prompt: "Today" }, "key");
  assert.equal(calls[0][0], "businesses/one/smokey/generations/");
  assert.equal(calls[0][1].headers["Idempotency-Key"], "key");
});
