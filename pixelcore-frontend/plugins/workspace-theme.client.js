import { businessThemeStyle } from "~/utils/businessTheme";
import { isWorkspaceThemeRoute } from "~/utils/workspaceTheme";

export default defineNuxtPlugin({
  name: "workspace-theme",
  enforce: "post",
  dependsOn: ["pinia"],
  setup() {
    const { preference, isDark, style } = useWorkspaceTheme();
    const business = useBusinessStore();
    const route = useRoute();
    const colorMode = useColorMode();
    if (colorMode.preference !== preference.value)
      colorMode.preference = preference.value;
    watch(
      [style, () => route.path],
      () => {
        const workspace = isWorkspaceThemeRoute(route.path);
        const dark = workspace && isDark.value;
        const root = document.documentElement;
        const tokens = workspace
          ? style.value
          : businessThemeStyle(business.activeBusiness || {}, {
              workspace: true,
            });
        Object.entries(tokens).forEach(([property, value]) =>
          root.style.setProperty(property, value),
        );
        const branding = business.activeBusiness?.branding || {};
        root.style.fontSize =
          branding.workspace?.use_business_branding === false
            ? ""
            : branding.typography?.base_font_size || "";
        root.style.colorScheme = dark ? "dark" : "light";
        root.dataset.workspaceTheme = workspace
          ? dark
            ? "dark"
            : "light"
          : "light";
      },
      { immediate: true, flush: "sync" },
    );
  },
});
