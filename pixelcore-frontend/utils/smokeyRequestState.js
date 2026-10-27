import { terminalStates } from "./smokeyAssistant.js";

export function createSmokeyRequestController({
  onChange,
  schedule = setTimeout,
  unschedule = clearTimeout,
  newKey = () => crypto.randomUUID(),
}) {
  let client,
    epoch = 0,
    timer,
    current = { state: "idle" },
    submission = null,
    stopRequested = false;
  const publish = (value) => {
    current = { ...value };
    onChange(current);
  };
  const clear = () => {
    if (timer) unschedule(timer);
    timer = null;
  };
  const errorMessage = (error) =>
    error?.data?.error?.message ||
    error?.message ||
    "Connection interrupted. Recover this request before submitting again.";
  const poll = async (token) => {
    const id = current.id;
    try {
      const next = await client.poll(id);
      if (token !== epoch) return;
      publish(next);
      if (!terminalStates.has(next.state))
        timer = schedule(() => poll(token), 1500);
    } catch (error) {
      if (token === epoch)
        publish({
          ...current,
          interrupted: true,
          transport_error: errorMessage(error),
        });
    }
  };
  return {
    setBusiness(nextClient) {
      epoch++;
      clear();
      client = nextClient;
      submission = null;
      stopRequested = false;
      publish({ state: "idle" });
    },
    async submit(prompt, plan = null, recover = false) {
      if (
        !client ||
        (["queued", "searching", "generating"].includes(current.state) &&
          !current.interrupted)
      )
        return;
      const token = ++epoch;
      clear();
      if (!recover) stopRequested = false;
      if (!recover || !submission)
        submission = {
          body: { prompt, ...(plan ? { plan } : {}) },
          key: newKey(),
        };
      publish({ state: "queued", prompt: submission.body.prompt });
      try {
        const next = await client.start(submission.body, submission.key);
        if (token !== epoch) return;
        publish(next);
        if (stopRequested && !terminalStates.has(next.state)) {
          const stopped = await client.stop(next.id);
          if (token === epoch) publish(stopped);
        } else if (!terminalStates.has(next.state))
          timer = schedule(() => poll(token), 1500);
      } catch (error) {
        if (token === epoch)
          publish({
            ...current,
            interrupted: true,
            transport_error: errorMessage(error),
          });
      }
    },
    async stop() {
      if (terminalStates.has(current.state) || current.state === "idle") return;
      stopRequested = true;
      clear();
      if (!current.id) return;
      const token = ++epoch;
      try {
        const next = await client.stop(current.id);
        if (token === epoch) publish(next);
      } catch (error) {
        if (token === epoch)
          publish({
            ...current,
            interrupted: true,
            transport_error: errorMessage(error),
          });
      }
    },
    resume() {
      if (current.id) {
        clear();
        publish({ ...current, interrupted: false, transport_error: null });
        poll(epoch);
      } else if (submission)
        return this.submit(submission.body.prompt, submission.body.plan, true);
    },
    dispose() {
      epoch++;
      clear();
      client = null;
    },
  };
}
