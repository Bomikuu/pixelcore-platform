export function useSmokeyAssistant() {
  return (
    useNuxtApp().$smokey || {
      status: ref({ ready: false, loading: false, error: "", opened: false }),
      retry: async () => {},
      toggleAssistant: () => {},
      attachDashboard: () => {},
      detachDashboard: () => {},
    }
  );
}
