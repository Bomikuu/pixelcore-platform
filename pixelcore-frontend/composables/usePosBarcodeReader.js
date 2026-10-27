import { onMounted, onScopeDispose } from "vue";

export function usePosBarcodeReader({ enabled, onScan }) {
  let buffer = "";
  let lastKeyAt = 0;

  function handleKey(event) {
    if (event.defaultPrevented || event.isComposing || event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
    const target = event.target;
    if (!enabled() || target?.closest?.('input, textarea, select, [contenteditable="true"], [role="combobox"]') || document.querySelector('[role="dialog"][data-state="open"], [role="menu"][data-state="open"]')) {
      buffer = "";
      return;
    }
    const now = performance.now();
    if (now - lastKeyAt > (event.key === "Enter" ? 300 : 100)) buffer = "";
    lastKeyAt = now;
    if (event.key === "Enter") {
      const code = buffer;
      buffer = "";
      if (code.length >= 3) {
        event.preventDefault();
        onScan(code);
      }
    } else if (event.key.length === 1) {
      if (event.key === " " && buffer.length) event.preventDefault();
      buffer = (buffer + event.key).slice(-120);
    } else {
      buffer = "";
    }
  }

  onMounted(() => window.addEventListener("keydown", handleKey));
  onScopeDispose(() => {
    if (typeof window !== "undefined") window.removeEventListener("keydown", handleKey);
  });
}
