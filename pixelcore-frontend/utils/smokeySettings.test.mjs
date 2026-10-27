import test from "node:test";
import assert from "node:assert/strict";
import {
  validateConnection,
  formatTokenCount,
  canConfigureSmokey,
  initialSmokeyTheme,
} from "./smokeySettings.js";

test("first use is light while saved and in-memory theme choices survive navigation", () => {
  assert.equal(initialSmokeyTheme("system", null, false), "light");
  assert.equal(initialSmokeyTheme("dark", "dark", false), "dark");
  assert.equal(initialSmokeyTheme("system", "system", false), "system");
  assert.equal(initialSmokeyTheme("dark", undefined, true), "dark");
});
test("connection models and credentials are explicit", () => {
  const connection = {
    name: "Office",
    provider: "openai",
    model: "chosen-model",
    secret: "fixture-key",
    permitted_models: ["chosen-model"],
  };
  assert.equal(validateConnection(connection), "");
  assert.match(
    validateConnection({ ...connection, permitted_models: [] }),
    /permitted/,
  );
  assert.match(validateConnection({ ...connection, secret: "" }), /key/);
  assert.equal(validateConnection({ ...connection, secret: "" }, true), "");
});
test("unknown tokens and manager configuration are not misrepresented", () => {
  assert.equal(formatTokenCount(null), "Unknown");
  assert.equal(formatTokenCount(0), "0");
  assert.equal(
    canConfigureSmokey({ permissions: ["generate", "view_reports"] }),
    false,
  );
});
