export const terminalStates = new Set([
  "succeeded",
  "empty",
  "failed",
  "cancelled",
]);

export function mascotPresentation(state, kind = "daily", hasPlan = true) {
  const labels = {
    idle: "Ready when you are.",
    queued: "Waiting to start…",
    searching: hasPlan
      ? {
          attendance: "Checking attendance records…",
          late: "Checking recorded late arrivals…",
          sales: "Checking recorded sales…",
        }[kind] || "Checking business records…"
      : "Understanding your report request…",
    generating: "Writing your summary…",
    succeeded: "Your report is ready.",
    empty: "Search complete.",
    failed: "I couldn’t finish this request.",
    cancelled: "Generation stopped.",
  };
  return {
    state:
      { queued: "idle", succeeded: "success", failed: "error" }[state] || state,
    label: labels[state] || labels.idle,
    busy: ["queued", "searching", "generating"].includes(state),
  };
}

export function createSmokeyClient(apiFetch, businessId) {
  const root = `businesses/${businessId}/smokey/`;
  return {
    request: (path, options = {}) =>
      apiFetch(root + path, { timeout: 15000, ...options }),
    start: (body, key) =>
      apiFetch(root + "generations/", {
        method: "POST",
        timeout: 15000,
        body,
        headers: { "Idempotency-Key": key },
      }),
    poll: (id) => apiFetch(root + `generations/${id}/`, { timeout: 15000 }),
    stop: (id) =>
      apiFetch(root + `generations/${id}/cancel/`, {
        method: "POST",
        timeout: 15000,
      }),
  };
}
