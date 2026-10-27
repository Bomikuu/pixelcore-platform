import { businessThemeStyle } from "~/utils/businessTheme";
import {
  resolveWorkspaceTheme,
  workspaceThemePreference,
} from "~/utils/workspaceTheme";

export function useWorkspaceTheme() {
  const colorMode = useColorMode();
  const preference = computed({
    get: () => workspaceThemePreference(colorMode.preference),
    set: (value) => {
      colorMode.preference = workspaceThemePreference(value);
    },
  });
  const business = useBusinessStore();
  const isDark = computed(
    () => resolveWorkspaceTheme(colorMode.value) === "dark",
  );
  const style = computed(() =>
    businessThemeStyle(business.activeBusiness || {}, {
      workspace: true,
      dark: isDark.value,
    }),
  );
  function toggle() {
    preference.value = isDark.value ? "light" : "dark";
  }
  return { preference, isDark, style, toggle };
}
