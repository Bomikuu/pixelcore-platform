import { onScopeDispose, ref, shallowRef } from "vue";

export const ATTENDANCE_CONFIRMATION_MS = 5000;

export function useAttendanceConfirmation(onReturn = () => {}) {
  const confirmation = shallowRef(null);
  const secondsRemaining = ref(0);
  let returnTimer;
  let countdownTimer;

  function clearConfirmation() {
    clearTimeout(returnTimer);
    clearInterval(countdownTimer);
    confirmation.value = null;
    secondsRemaining.value = 0;
  }

  function showConfirmation(response, timeZone) {
    clearConfirmation();
    const employee = response.employee || {};
    const name = employee.display_name || response.employee_name || "Employee";
    const loggedOut = response.action === "clock_out";
    const timestamp = loggedOut ? response.record.clock_out : response.record.clock_in;
    const date = new Date(timestamp);

    confirmation.value = {
      name,
      initials: name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase(),
      imageUrl: employee.profile_image_url || "",
      jobTitle: employee.job_title || "",
      message: `${name}, you have logged ${loggedOut ? "out" : "in"}.`,
      actionLabel: loggedOut ? "Clock-out recorded" : "Clock-in recorded",
      time: Number.isNaN(date.getTime()) ? "" : new Intl.DateTimeFormat("en-PH", {
        hour: "numeric",
        minute: "2-digit",
        timeZone,
      }).format(date),
      timestamp,
    };
    const deadline = Date.now() + ATTENDANCE_CONFIRMATION_MS;
    secondsRemaining.value = ATTENDANCE_CONFIRMATION_MS / 1000;
    countdownTimer = setInterval(() => {
      secondsRemaining.value = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
    }, 1000);
    returnTimer = setTimeout(() => {
      clearConfirmation();
      onReturn();
    }, ATTENDANCE_CONFIRMATION_MS);
  }

  onScopeDispose(clearConfirmation);
  return { confirmation, secondsRemaining, showConfirmation, clearConfirmation };
}
