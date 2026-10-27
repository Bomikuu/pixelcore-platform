import assert from "node:assert/strict";
import test from "node:test";
import { effectScope } from "vue";
import { useAttendanceConfirmation } from "./useAttendanceConfirmation.js";

const response = (action = "clock_in") => ({
  action,
  employee_name: "Casey Rivera",
  employee: {
    display_name: "Casey Rivera",
    job_title: "Team lead",
    profile_image_url: "https://example.test/casey.png",
    email: "private@example.test",
  },
  record: {
    clock_in: "2026-10-26T01:05:00Z",
    clock_out: "2026-10-26T09:15:00Z",
  },
});

function setup(t) {
  t.mock.timers.enable({ apis: ["setTimeout", "setInterval", "Date"], now: 1000 });
  let returns = 0;
  const scope = effectScope();
  const terminal = scope.run(() => useAttendanceConfirmation(() => { returns += 1; }));
  t.after(() => scope.stop());
  return { ...terminal, scope, returns: () => returns };
}

test("clock-in shows the employee profile and uses the business timezone", (t) => {
  const terminal = setup(t);
  terminal.showConfirmation(response(), "Asia/Manila");
  assert.deepEqual(terminal.confirmation.value, {
    name: "Casey Rivera",
    initials: "CR",
    imageUrl: "https://example.test/casey.png",
    jobTitle: "Team lead",
    message: "Casey Rivera, you have logged in.",
    actionLabel: "Clock-in recorded",
    time: "9:05 AM",
    timestamp: "2026-10-26T01:05:00Z",
  });
  assert.equal(terminal.secondsRemaining.value, 5);
});

test("clock-out uses its own action and timestamp", (t) => {
  const terminal = setup(t);
  terminal.showConfirmation(response("clock_out"), "Asia/Manila");
  assert.equal(terminal.confirmation.value.message, "Casey Rivera, you have logged out.");
  assert.equal(terminal.confirmation.value.actionLabel, "Clock-out recorded");
  assert.equal(terminal.confirmation.value.time, "5:15 PM");
});

test("profile stays for five seconds, then clears before returning to code entry", (t) => {
  const terminal = setup(t);
  terminal.showConfirmation(response(), "Asia/Manila");
  t.mock.timers.tick(1000);
  assert.equal(terminal.secondsRemaining.value, 4);
  t.mock.timers.tick(3999);
  assert.notEqual(terminal.confirmation.value, null);
  assert.equal(terminal.returns(), 0);
  t.mock.timers.tick(1);
  assert.equal(terminal.confirmation.value, null);
  assert.equal(terminal.secondsRemaining.value, 0);
  assert.equal(terminal.returns(), 1);
  t.mock.timers.tick(10000);
  assert.equal(terminal.returns(), 1);
});

test("missing photo and title use initials and support the previous API response", (t) => {
  const terminal = setup(t);
  const legacyResponse = response();
  delete legacyResponse.employee;
  terminal.showConfirmation(legacyResponse, "Asia/Manila");
  assert.equal(terminal.confirmation.value.initials, "CR");
  assert.equal(terminal.confirmation.value.imageUrl, "");
  assert.equal(terminal.confirmation.value.jobTitle, "");
});

test("disconnect clears the employee immediately and cancels the pending return", (t) => {
  const terminal = setup(t);
  terminal.showConfirmation(response(), "Asia/Manila");
  t.mock.timers.tick(2000);
  terminal.clearConfirmation();
  assert.equal(terminal.confirmation.value, null);
  t.mock.timers.tick(10000);
  assert.equal(terminal.returns(), 0);
  assert.equal(terminal.secondsRemaining.value, 0);
});

test("leaving the page clears profile data and cancels timers", (t) => {
  const terminal = setup(t);
  terminal.showConfirmation(response(), "Asia/Manila");
  terminal.scope.stop();
  assert.equal(terminal.confirmation.value, null);
  t.mock.timers.tick(10000);
  assert.equal(terminal.returns(), 0);
});

test("a replacement confirmation receives its full five seconds", (t) => {
  const terminal = setup(t);
  terminal.showConfirmation(response(), "Asia/Manila");
  t.mock.timers.tick(4000);
  terminal.showConfirmation(response("clock_out"), "Asia/Manila");
  t.mock.timers.tick(1000);
  assert.equal(terminal.returns(), 0);
  assert.equal(terminal.confirmation.value.actionLabel, "Clock-out recorded");
  t.mock.timers.tick(4000);
  assert.equal(terminal.confirmation.value, null);
  assert.equal(terminal.returns(), 1);
});
