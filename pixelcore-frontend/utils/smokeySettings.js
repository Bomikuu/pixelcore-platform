export function validateConnection(value, replacing = false) {
  if (!value.name?.trim()) return "Give this connection a name.";
  if (!["openai", "anthropic", "gemini", "openrouter"].includes(value.provider))
    return "Choose a supported provider.";
  if (!value.model?.trim()) return "Choose a model.";
  if (!replacing && !value.secret?.trim())
    return "Supply your provider API key.";
  if (
    !Array.isArray(value.permitted_models) ||
    !value.permitted_models.includes(value.model)
  )
    return "Include the selected model in permitted models.";
  return "";
}
export function formatTokenCount(value) {
  return value == null ? "Unknown" : new Intl.NumberFormat().format(value);
}
export function canConfigureSmokey(config) {
  return config?.permissions?.includes("configure") || false;
}
export function metricLabel(key) {
  return key
    .replaceAll("_", " ")
    .replace(/^./, (letter) => letter.toUpperCase());
}

export function initialSmokeyTheme(current, saved, initialized) {
  return initialized || ["light", "dark", "system"].includes(saved)
    ? current
    : "light";
}
