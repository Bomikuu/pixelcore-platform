export const createSmokeyModuleLifecycle = ({
  load,
  mount,
  onChange = () => {},
}) => {
  let overlayActive = false;
  let runtime,
    current,
    pending,
    dashboard,
    destroyed = false,
    epoch = 0;
  let state = { ready: false, loading: false, error: "", opened: false };
  const publish = (change) => {
    state = { ...state, ...change };
    onChange(state);
  };
  const ensure = async () => {
    if (destroyed || !current) return;
    if (runtime) {
      runtime.updateContext(current);
      return;
    }
    const token = epoch;
    publish({ loading: true, error: "" });
    if (!pending)
      pending = Promise.resolve()
        .then(load)
        .finally(() => {
          pending = null;
        });
    try {
      const loaded = await pending;
      if (destroyed || token !== epoch || !current || runtime) return;
      runtime = mount(loaded, current, (event) => {
        if (destroyed) return;
        if (event.type === "assistant-open") publish({ opened: true });
        if (event.type === "assistant-close") publish({ opened: false });
      });
      runtime.setHostOverlayActive(overlayActive);
      if (dashboard)
        runtime.attachDashboard(dashboard.element, dashboard.route);
      publish({ ready: true, loading: false, error: "" });
    } catch (issue) {
      if (!destroyed && token === epoch)
        publish({
          loading: false,
          ready: false,
          error: issue?.message || "Smokey could not load. Please try again.",
        });
    }
  };
  return {
    updateContext: async (context) => {
      if (destroyed) return;
      current = context;
      await ensure();
    },
    attachDashboard: (element, route) => {
      dashboard = { element, route };
      runtime?.attachDashboard(element, route);
    },
    detachDashboard: () => {
      dashboard = undefined;
      runtime?.detachDashboard();
    },
    setRoute: (route) => {
      if (dashboard) dashboard.route = route;
      runtime?.setRoute(route);
    },
    toggleAssistant: (trigger) => runtime?.toggleAssistant(trigger),
    setHostOverlayActive: (active) => {
      overlayActive = active;
      runtime?.setHostOverlayActive(active);
    },
    retry: () => ensure(),
    getSnapshot: () => state,
    destroy: () => {
      if (destroyed) return;
      destroyed = true;
      epoch++;
      current = undefined;
      dashboard = undefined;
      runtime?.destroy();
      runtime = undefined;
      publish({ ready: false, loading: false, error: "", opened: false });
    },
  };
};
