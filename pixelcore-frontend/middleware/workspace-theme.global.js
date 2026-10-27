import { isWorkspaceThemeRoute } from "~/utils/workspaceTheme";

export default defineNuxtRouteMiddleware((to) => {
  to.meta.colorMode = isWorkspaceThemeRoute(to.path) ? undefined : "light";
});
