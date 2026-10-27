export function workspaceThemePreference(value) {
  return ["light", "dark", "system"].includes(value) ? value : "system";
}

export function resolveWorkspaceTheme(preference, systemDark = false) {
  const selected = workspaceThemePreference(preference);
  return selected === "system" ? (systemDark ? "dark" : "light") : selected;
}

export function isWorkspaceThemeRoute(path) {
  return /^\/(workspace|settings)(\/|$)/.test(path || "");
}
