import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { compileScript, parse } from "@vue/compiler-sfc";
import { computed, effectScope, nextTick, ref } from "vue";
import { useAttendanceConfirmation } from "../composables/useAttendanceConfirmation.js";

// Exercise the actual page setup with Nuxt's auto-imports supplied, without a browser.
const { descriptor } = parse(readFileSync(new URL("../pages/attendance-terminal.vue", import.meta.url), "utf8"));
const compiled = compileScript(descriptor, { id: "attendance-terminal-test" });
let setupSource = descriptor.scriptSetup.content;
for (const node of [...compiled.scriptSetupAst].reverse()) {
  if (node.type === "ImportDeclaration") {
    setupSource = setupSource.slice(0, node.start) + setupSource.slice(node.end);
  }
}
const createPage = new Function(
  "ref", "computed", "nextTick", "onMounted", "onBeforeUnmount", "definePageMeta",
  "useRuntimeConfig", "useAttendanceConfirmation", "$fetch", "localStorage", "window",
  `${setupSource}\nreturn { state, working, session, deviceToken, attendanceCode, message, confirmation, codeInput, confirmationHeading, submitCode, pressKey, unpair, loadSession };`,
);

function setup(t, fetch) {
  t.mock.timers.enable({ apis: ["setTimeout", "setInterval", "Date"], now: 1000 });
  const scope = effectScope();
  const beforeUnmount = [];
  const storage = new Map([["pixelcore_attendance_token", "paired-test-token"]]);
  const page = scope.run(() => createPage(
    ref, computed, nextTick, () => {}, (callback) => beforeUnmount.push(callback), () => {},
    () => ({ public: { apiBaseUrl: "https://example.test/api/" } }),
    useAttendanceConfirmation, fetch,
    { removeItem: (key) => storage.delete(key) },
    { clearInterval },
  ));
  page.state.value = "ready";
  page.deviceToken.value = "paired-test-token";
  page.session.value = { business: { timezone: "Asia/Manila" }, device: {} };
  const focus = { code: 0, profile: 0 };
  page.codeInput.value = { focus: () => {
    assert.equal(page.working.value, false, "code entry must be enabled before focus");
    focus.code += 1;
  } };
  page.confirmationHeading.value = { focus: () => { focus.profile += 1; } };
  const unmount = () => {
    beforeUnmount.forEach((callback) => callback());
    scope.stop();
  };
  t.after(unmount);
  return { page, focus, storage, unmount };
}

const success = {
  action: "clock_in", employee_name: "Casey Rivera",
  employee: { display_name: "Casey Rivera", job_title: "Team lead", profile_image_url: null },
  record: { clock_in: "2026-10-26T01:05:00Z" },
};

test("successful code entry shows the profile, then restores the empty terminal and focus", async (t) => {
  const requests = [];
  const { page, focus } = setup(t, async (path, options) => {
    requests.push({ path, options });
    return success;
  });
  page.attendanceCode.value = "123456";
  await page.submitCode();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].options.headers["X-Device-Token"], "paired-test-token");
  assert.deepEqual(requests[0].options.body, { code: "123456" });
  assert.equal(page.attendanceCode.value, "");
  assert.equal(page.confirmation.value.name, "Casey Rivera");
  assert.equal(focus.profile, 1);
  page.pressKey("1");
  await page.submitCode();
  assert.equal(page.attendanceCode.value, "");
  assert.equal(requests.length, 1);
  t.mock.timers.tick(5000);
  await nextTick();
  assert.equal(page.confirmation.value, null);
  assert.equal(page.state.value, "ready");
  assert.equal(focus.code, 1);
  page.pressKey("2");
  assert.equal(page.attendanceCode.value, "2");
});

test("a pending request blocks another submission and keypad edits", async (t) => {
  let resolveRequest;
  let requests = 0;
  const { page } = setup(t, () => {
    requests += 1;
    return new Promise((resolve) => { resolveRequest = resolve; });
  });
  page.attendanceCode.value = "123456";
  const pending = page.submitCode();
  page.pressKey("clear");
  await page.submitCode();
  assert.equal(page.working.value, true);
  assert.equal(page.attendanceCode.value, "123456");
  assert.equal(requests, 1);
  resolveRequest(success);
  await pending;
  assert.equal(page.working.value, false);
});

test("an invalid code keeps the keypad available with an error and no profile", async (t) => {
  const { page, focus } = setup(t, async () => {
    throw { data: { error: { message: "This attendance code is invalid, expired, or already used." } } };
  });
  page.attendanceCode.value = "123456";
  await page.submitCode();
  assert.equal(page.state.value, "ready");
  assert.equal(page.confirmation.value, null);
  assert.equal(page.attendanceCode.value, "");
  assert.match(page.message.value, /invalid, expired/);
  assert.equal(focus.code, 1);
  t.mock.timers.tick(5000);
  await nextTick();
  assert.equal(focus.code, 1);
});

test("a revoked terminal switches to reconnect without showing a profile", async (t) => {
  const { page, focus } = setup(t, async () => {
    throw { response: { status: 403 }, data: { error: { code: "DEVICE_ACCESS_DENIED", message: "Pair this attendance terminal again." } } };
  });
  page.attendanceCode.value = "123456";
  await page.submitCode();
  assert.equal(page.state.value, "error");
  assert.equal(page.confirmation.value, null);
  assert.equal(focus.code, 0);
});

test("disconnect removes the saved device and profile without a delayed focus change", async (t) => {
  const { page, focus, storage } = setup(t, async () => success);
  page.attendanceCode.value = "123456";
  await page.submitCode();
  page.unpair();
  assert.equal(page.confirmation.value, null);
  assert.equal(page.deviceToken.value, "");
  assert.equal(storage.has("pixelcore_attendance_token"), false);
  t.mock.timers.tick(5000);
  await nextTick();
  assert.equal(page.state.value, "unpaired");
  assert.equal(focus.code, 0);
});

test("leaving the page aborts the pending attendance request", async (t) => {
  let requestSignal;
  const { page, unmount } = setup(t, (_path, { signal }) => {
    requestSignal = signal;
    return new Promise((_resolve, reject) => {
      signal.addEventListener("abort", () => reject(new Error("Request aborted")), { once: true });
    });
  });
  page.attendanceCode.value = "123456";
  const pending = page.submitCode();
  unmount();
  await pending;
  assert.equal(requestSignal.aborted, true);
  assert.equal(page.confirmation.value, null);
  assert.equal(page.message.value, "");
});

test("a response arriving after unmount cannot restart the profile timer", async (t) => {
  let resolveRequest;
  const { page, focus, unmount } = setup(t, () => new Promise((resolve) => { resolveRequest = resolve; }));
  page.attendanceCode.value = "123456";
  const pending = page.submitCode();
  unmount();
  resolveRequest(success);
  await pending;
  assert.equal(page.confirmation.value, null);
  t.mock.timers.tick(5000);
  await nextTick();
  assert.equal(focus.code, 0);
  assert.equal(focus.profile, 0);
});
