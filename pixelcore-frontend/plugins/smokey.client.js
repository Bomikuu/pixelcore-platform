import { createLegacySmokeyClient } from "~/utils/smokeyLegacyClient";
import { createPixelCoreSmokeyAdapter } from "~/utils/smokeyHostAdapter";
import { createSmokeyModuleLifecycle } from "~/utils/smokeyModuleLifecycle";
import { loadPixelCoreSmokeyModule } from "~/utils/smokeyModuleLoader";
import { parseSmokeyRoute, smokeyRoutePath } from "~/utils/smokeyModuleRoutes";

export default defineNuxtPlugin({
  name: "smokey-assistant",
  dependsOn: ["pinia"],
  setup(app) {
    const business = useBusinessStore(),
      auth = useAuthStore(),
      route = useRoute(),
      config = useRuntimeConfig();
    const { apiFetch } = useApiClient();
    if (config.public.smokeyUiMode !== "module")
      return {
        provide: { smokey: createLegacySmokeyClient(app, business, apiFetch) },
      };
    const { isDark } = useWorkspaceTheme();
    const status = ref({
      ready: false,
      loading: false,
      error: "",
      opened: false,
    });
    let lifecycle,
      owner,
      context,
      descriptor,
      revision = 0,
      sequence = 0,
      controller,
      page,
      modalObserver;
    const role = () =>
      auth.user?.businesses?.find(
        (entry) => entry.public_id === business.activeBusiness?.public_id,
      )?.role;
    const eligible = () =>
      auth.user &&
      business.activeBusiness &&
      ["owner", "admin", "manager"].includes(role()) &&
      /^\/(workspace|settings)(\/|$)/.test(route.path);
    const routeValue = () => parseSmokeyRoute(route.path);
    const navigate = (next) => navigateTo(smokeyRoutePath(next));
    const teardown = () => {
      sequence++;
      controller?.abort();
      lifecycle?.destroy();
      lifecycle = undefined;
      modalObserver?.disconnect();
      modalObserver = undefined;
      owner?.remove();
      owner = undefined;
      context = undefined;
      descriptor = undefined;
      status.value = { ready: false, loading: false, error: "", opened: false };
    };
    const boot = async () => {
      if (!eligible()) {
        teardown();
        return;
      }
      const token = ++sequence;
      controller?.abort();
      controller = new AbortController();
      revision++;
      const identity = {
        hostId: "pixelcore",
        organizationId: business.activeBusiness.public_id,
        actorId: String(auth.user.id),
        revision,
      };
      context = {
        identity,
        organization: {
          name: business.activeBusiness.display_name,
          timezone: business.activeBusiness.timezone || "Asia/Manila",
        },
        installed: false,
        enabled: false,
        permissions: [],
        reportKinds: [],
        theme: isDark.value ? "dark" : "light",
      };
      // Clear old private state synchronously while resolving the new descriptor.
      if (lifecycle) void lifecycle.updateContext(context);
      status.value = { ...status.value, loading: true, error: "" };
      try {
        descriptor = await apiFetch(
          "businesses/" + identity.organizationId + "/smokey-integration/",
          { signal: controller.signal, timeout: 15000 },
        );
        if (token !== sequence) return;
        if (descriptor.hostApiVersion?.major !== 1)
          throw new Error("This host needs a compatible Smokey module.");
        context = { ...context, ...descriptor };
        if (!lifecycle) {
          owner = document.createElement("div");
          owner.dataset.smokeyOwner = "";
          document.body.append(owner);
          const adapter = createPixelCoreSmokeyAdapter({
            apiFetch,
            currentContext: () => context,
            navigate,
            sourceOrigin: location.origin,
          });
          lifecycle = createSmokeyModuleLifecycle({
            load: () =>
              loadPixelCoreSmokeyModule({
                source: config.public.smokeyUiSource,
                manifestUrl: config.public.smokeyUiManifest,
                hostVersion: descriptor.hostApiVersion,
                signal: AbortSignal.timeout(15000),
              }),
            mount: (loaded, active, onEvent) =>
              loaded.module.mountSmokey({
                owner,
                adapter,
                context: active,
                assetsBaseUrl: loaded.assetsBaseUrl,
                pageHeader: "host",
                stylesheetUrl: loaded.stylesheetUrl,
                onEvent: (event) => {
                  if (!context || !eligible()) return;
                  onEvent(event);
                  if (event.type === "module-enabled")
                    void business.loadBusinesses().catch(() => {
                      status.value = {
                        ...status.value,
                        error:
                          "Smokey was enabled, but the business settings could not refresh. Please try again.",
                      };
                    });
                  if (event.type === "session-expired") {
                    teardown();
                    void auth.loadUser().catch(() => {});
                  }
                  if (event.type === "error") {
                    const failed = lifecycle;
                    queueMicrotask(() => {
                      if (lifecycle !== failed) return;
                      teardown();
                      status.value = {
                        ...status.value,
                        error:
                          "Smokey could not display this view. Please try again.",
                      };
                    });
                  }
                },
              }),
            onChange: (next) => {
              status.value = {
                ...next,
                available: Boolean(context?.installed && context.enabled),
              };
            },
          });
          const syncHostOverlay = () =>
            lifecycle?.setHostOverlayActive(
              Boolean(
                document.querySelector(
                  '[role="dialog"][data-state="open"], [role="alertdialog"][data-state="open"]',
                ),
              ),
            );
          modalObserver = new MutationObserver(syncHostOverlay);
          modalObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ["data-state"],
          });
          syncHostOverlay();
        }
        await lifecycle.updateContext(context);
        if (token === sequence && page)
          lifecycle.attachDashboard(page, routeValue());
      } catch (error) {
        if (token === sequence && error?.name !== "AbortError")
          status.value = {
            ready: false,
            loading: false,
            error:
              error?.data?.error?.message ||
              error?.message ||
              "Smokey could not load.",
            opened: false,
          };
      }
    };
    watch(
      () => [
        auth.user?.id,
        business.activeBusiness?.public_id,
        JSON.stringify(business.activeBusiness?.enabled_modules),
        role(),
        /^\/(workspace|settings)(\/|$)/.test(route.path),
      ],
      boot,
      { immediate: true, flush: "sync" },
    );
    watch(isDark, () => {
      if (context) {
        context = { ...context, theme: isDark.value ? "dark" : "light" };
        void lifecycle?.updateContext(context);
      }
    });
    watch(
      () => route.path,
      () => lifecycle?.setRoute(routeValue()),
    );
    app.hook("app:beforeUnmount", teardown);
    return {
      provide: {
        smokey: {
          status,
          retry: boot,
          toggleAssistant: (element) => lifecycle?.toggleAssistant(element),
          attachDashboard: (element) => {
            page = element;
            lifecycle?.attachDashboard(element, routeValue());
          },
          detachDashboard: () => {
            page = undefined;
            lifecycle?.detachDashboard();
          },
        },
      },
    };
  },
});
