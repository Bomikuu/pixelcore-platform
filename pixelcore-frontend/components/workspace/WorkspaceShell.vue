<template>
  <div
    class="min-h-dvh bg-muted/35 lg:grid lg:transition-[grid-template-columns] lg:duration-200"
    :class="
      sidebarCollapsed
        ? 'lg:grid-cols-[5rem_minmax(0,1fr)]'
        : 'lg:grid-cols-[17.5rem_minmax(0,1fr)]'
    "
    :style="shellStyle"
  >
    <Button
      variant="ghost"
      v-if="menuOpen"
      class="fixed inset-0 z-40 bg-foreground/45 lg:hidden"
      type="button"
      aria-label="Close navigation"
      @click="menuOpen = false"
    />

    <aside
      class="fixed inset-y-0 left-0 z-50 flex h-dvh w-[17.5rem] -translate-x-full flex-col overflow-hidden text-[var(--workspace-sidebar-foreground)] transition-transform duration-200 lg:sticky lg:top-0 lg:w-auto lg:translate-x-0"
      :class="menuOpen ? 'translate-x-0' : ''"
      :style="{ backgroundColor: 'var(--workspace-sidebar)' }"
      aria-label="Workspace navigation"
    >
      <div
        class="flex h-16 shrink-0 items-center justify-between border-b border-[color:var(--workspace-sidebar-border)] px-4"
        :class="sidebarCollapsed ? 'lg:gap-1 lg:px-2' : ''"
      >
        <NuxtLink
          to="/workspace"
          class="flex min-w-0 items-center gap-3"
          aria-label="PixelCore dashboard"
          @click="menuOpen = false"
        >
          <span
            class="grid h-9 w-9 shrink-0 grid-cols-2 gap-1 rounded-lg bg-white p-2"
            :class="sidebarCollapsed ? 'lg:h-7 lg:w-7 lg:p-1.5' : ''"
            aria-hidden="true"
            ><i class="rounded-sm bg-[var(--brand-primary)]" /><i
              class="rounded-sm bg-[var(--brand-accent)]" /><i
              class="rounded-sm bg-[var(--brand-accent)]" /><i
              class="rounded-sm bg-[var(--brand-primary)]"
          /></span>
          <span class="min-w-0" :class="sidebarCollapsed ? 'lg:hidden' : ''"
            ><strong class="block text-[15px] leading-none">PixelCore</strong
            ><span
              class="mt-1 block text-[10px] font-semibold uppercase tracking-[.14em] text-[var(--workspace-sidebar-faint)]"
              >Business admin</span
            ></span
          >
        </NuxtLink>
        <TooltipProvider :delay-duration="250">
          <Tooltip>
            <TooltipTrigger as-child>
              <Button
                variant="ghost"
                size="icon"
                class="hidden h-9 w-9 shrink-0 text-[var(--workspace-sidebar-muted)] hover:bg-[var(--workspace-sidebar-overlay)] hover:text-[var(--workspace-sidebar-foreground)] lg:inline-flex"
                :class="sidebarCollapsed ? 'lg:h-8 lg:w-8' : ''"
                type="button"
                :aria-label="
                  sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'
                "
                :aria-expanded="!sidebarCollapsed"
                @click="toggleSidebar"
              >
                <PanelLeftOpen
                  v-if="sidebarCollapsed"
                  class="h-[17px] w-[17px] shrink-0"
                  aria-hidden="true"
                />
                <PanelLeftClose
                  v-else
                  class="h-[17px] w-[17px] shrink-0"
                  aria-hidden="true"
                />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              {{ sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar" }}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <Button
          variant="ghost"
          class="grid h-9 w-9 place-items-center rounded-lg border border-[color:var(--workspace-sidebar-border)] text-[var(--workspace-sidebar-muted)] lg:hidden"
          type="button"
          aria-label="Close navigation"
          @click="menuOpen = false"
          ><X class="h-5 w-5"
        /></Button>
      </div>

      <div
        class="shrink-0 px-3 pb-3 pt-4"
        :class="sidebarCollapsed ? 'lg:px-2' : ''"
      >
        <label class="sr-only" for="active-business">Active business</label>
        <div
          class="relative flex items-center gap-3 rounded-xl bg-[var(--workspace-sidebar-overlay)] p-2.5"
          :class="sidebarCollapsed ? 'lg:justify-center lg:p-2' : ''"
        >
          <div
            class="grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-lg bg-card text-sm font-black text-card-foreground"
          >
            <img
              v-if="business.activeBusiness?.logo"
              :src="business.activeBusiness.logo"
              alt=""
              class="h-full w-full object-cover"
            />
            <span v-else>{{ businessInitial }}</span>
          </div>
          <div
            class="min-w-0 flex-1"
            :class="sidebarCollapsed ? 'lg:hidden' : ''"
          >
            <p class="truncate text-sm font-bold">
              {{ business.activeBusiness?.display_name || "Choose a business" }}
            </p>
            <p
              class="mt-0.5 truncate text-xs text-[var(--workspace-sidebar-muted)]"
            >
              {{ business.activeBusiness?.industry || presetLabel }}
            </p>
          </div>
          <NativeSelect
            id="active-business"
            class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
            :value="business.activeBusiness?.public_id"
            aria-label="Switch active business"
            @change="selectBusiness"
          >
            <option
              v-for="item in business.businesses"
              :key="item.public_id"
              :value="item.public_id"
            >
              {{ item.display_name }}
            </option>
          </NativeSelect>
          <ChevronsUpDown
            class="h-4 w-4 shrink-0 text-[var(--workspace-sidebar-faint)]"
            :class="sidebarCollapsed ? 'lg:hidden' : ''"
            aria-hidden="true"
          />
        </div>
      </div>

      <nav
        class="workspace-nav-scroll min-h-0 flex-1 overflow-y-auto overscroll-contain px-3 pb-4"
        :class="
          sidebarCollapsed ? 'workspace-nav-scroll--collapsed lg:px-2' : ''
        "
        aria-label="Business workspace"
      >
        <section
          v-for="group in navigation"
          :key="group.label"
          class="mt-4 first:mt-1"
        >
          <h2
            class="px-3 text-[10px] font-extrabold uppercase tracking-[.16em] text-[var(--workspace-sidebar-faint)]"
            :class="sidebarCollapsed ? 'lg:hidden' : ''"
          >
            {{ group.label }}
          </h2>
          <div
            class="mt-2 space-y-1"
            :class="sidebarCollapsed ? 'lg:mt-0' : ''"
          >
            <NuxtLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              class="group flex min-h-10 items-center gap-3 rounded-lg px-3 text-[13px] font-semibold text-[var(--workspace-sidebar-muted)] hover:bg-[var(--workspace-sidebar-overlay)] hover:text-[var(--workspace-sidebar-foreground)]"
              :class="[
                isActive(item)
                  ? '!bg-[var(--workspace-sidebar-overlay)] !text-[var(--workspace-sidebar-foreground)]'
                  : '',
                sidebarCollapsed ? 'lg:justify-center lg:px-2' : '',
              ]"
              :title="sidebarCollapsed ? item.label : undefined"
              @click="menuOpen = false"
            >
              <component
                :is="item.icon"
                class="h-[17px] w-[17px] shrink-0"
                :class="
                  isActive(item)
                    ? 'text-[var(--brand-accent)]'
                    : 'text-[var(--workspace-sidebar-faint)] group-hover:text-[var(--workspace-sidebar-muted)]'
                "
                aria-hidden="true"
              />
              <span :class="sidebarCollapsed ? 'lg:sr-only' : ''">{{
                item.label
              }}</span>
            </NuxtLink>
          </div>
        </section>
      </nav>

      <footer
        aria-label="Workspace account controls"
        class="shrink-0 border-t border-[color:var(--workspace-sidebar-border)] p-3"
        :class="sidebarCollapsed ? 'lg:p-2' : ''"
      >
        <div
          class="flex min-w-0 items-center gap-2"
          :class="sidebarCollapsed ? 'lg:flex-col' : ''"
        >
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button
                type="button"
                variant="ghost"
                class="h-12 min-w-0 flex-1 justify-start gap-3 px-2 text-[var(--workspace-sidebar-foreground)] hover:bg-[var(--workspace-sidebar-overlay)] hover:text-[var(--workspace-sidebar-foreground)]"
                :class="
                  sidebarCollapsed
                    ? 'lg:h-10 lg:w-10 lg:flex-none lg:justify-center lg:px-0'
                    : ''
                "
                :title="sidebarCollapsed ? userIdentity.displayName : undefined"
                :aria-label="`Open account menu for ${userIdentity.displayName}`"
              >
                <Avatar
                  class="h-8 w-8 shrink-0 border border-[color:var(--workspace-sidebar-border)]"
                  size="sm"
                >
                  <AvatarFallback
                    class="bg-[var(--workspace-sidebar-overlay)] text-xs font-bold text-[var(--workspace-sidebar-foreground)]"
                  >
                    {{ userIdentity.initials }}
                  </AvatarFallback>
                </Avatar>
                <span
                  class="min-w-0 flex-1 text-left"
                  :class="sidebarCollapsed ? 'lg:hidden' : ''"
                >
                  <span class="block truncate text-sm font-semibold">{{
                    userIdentity.displayName
                  }}</span>
                  <span
                    class="mt-0.5 block truncate text-xs font-normal text-[var(--workspace-sidebar-muted)]"
                    >{{ userIdentity.email || "Workspace account" }}</span
                  >
                </span>
                <ChevronUp
                  class="h-4 w-4 shrink-0 text-[var(--workspace-sidebar-muted)]"
                  :class="sidebarCollapsed ? 'lg:hidden' : ''"
                  aria-hidden="true"
                />
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent
              side="top"
              align="start"
              :side-offset="8"
              :collision-padding="12"
              class="w-72 max-w-[calc(100vw-1.5rem)]"
            >
              <DropdownMenuLabel class="px-3 py-3">
                <span class="block truncate text-sm font-bold">{{
                  userIdentity.displayName
                }}</span>
                <span
                  class="mt-1 block truncate text-xs font-normal text-muted-foreground"
                >
                  {{ userIdentity.email || "Signed-in workspace account" }}
                </span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem as-child>
                <NuxtLink
                  to="/settings/identity"
                  class="cursor-pointer"
                  @click="menuOpen = false"
                >
                  <Store class="h-4 w-4" aria-hidden="true" />
                  Business identity
                </NuxtLink>
              </DropdownMenuItem>
              <DropdownMenuItem as-child>
                <NuxtLink
                  to="/settings/team"
                  class="cursor-pointer"
                  @click="menuOpen = false"
                >
                  <UsersRound class="h-4 w-4" aria-hidden="true" />
                  Team & access
                </NuxtLink>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                class="cursor-pointer text-destructive focus:text-destructive"
                @select="signOutFromSidebar"
              >
                <LogOut class="h-4 w-4" aria-hidden="true" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <WorkspaceThemeToggle
            class="text-[var(--workspace-sidebar-muted)] hover:bg-[var(--workspace-sidebar-overlay)] hover:text-[var(--workspace-sidebar-foreground)]"
          />
        </div>
      </footer>
    </aside>

    <div class="min-w-0">
      <nav
        class="flex min-h-16 items-center justify-between gap-3 border-b bg-[var(--workspace-header)] px-4 sm:px-5 lg:px-6"
        aria-label="Workspace toolbar"
      >
        <div class="flex min-w-0 items-center gap-3">
          <Button
            variant="ghost"
            class="grid h-9 w-9 shrink-0 place-items-center rounded-lg border bg-card lg:hidden"
            type="button"
            aria-label="Open navigation"
            :aria-expanded="menuOpen"
            @click="menuOpen = true"
            ><Menu class="h-5 w-5"
          /></Button>
          <div class="min-w-0">
            <ol
              class="flex min-w-0 items-center gap-2 text-xs font-semibold text-muted-foreground"
              aria-label="Breadcrumb"
            >
              <li
                v-for="(crumb, index) in breadcrumbs"
                :key="`${crumb}-${index}`"
                class="min-w-0 items-center gap-2"
                :class="
                  smokeyHeader && index < breadcrumbs.length - 1
                    ? 'hidden sm:flex'
                    : 'flex'
                "
              >
                <ChevronRight
                  v-if="index"
                  :class="smokeyHeader ? 'hidden sm:block' : ''"
                  class="h-3.5 w-3.5 shrink-0 text-border"
                  aria-hidden="true"
                />
                <component
                  :is="
                    smokeyHeader && index === breadcrumbs.length - 1
                      ? 'h1'
                      : 'span'
                  "
                  class="truncate text-xs"
                  :class="
                    index === breadcrumbs.length - 1 ? 'text-foreground' : ''
                  "
                  :aria-current="
                    index === breadcrumbs.length - 1 ? 'page' : undefined
                  "
                  >{{ crumb }}</component
                >
              </li>
            </ol>
            <p
              v-if="smokeyHeader"
              class="mt-1 hidden truncate text-xs leading-5 text-muted-foreground sm:block"
              :title="smokeyHeader.description"
            >
              {{ smokeyHeader.description }}
            </p>
          </div>
        </div>

        <div class="flex shrink-0 items-center gap-1 sm:gap-2">
          <div class="hidden items-center gap-2 border-r pr-3 sm:flex">
            <Clock3 class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <time :datetime="clock.dateTime" class="text-right tabular-nums">
              <span
                class="block text-sm font-bold leading-none text-foreground"
                >{{ clock.time }}</span
              >
              <span
                class="mt-1 hidden text-[11px] leading-none text-muted-foreground md:block"
                >{{ clock.date }}</span
              >
            </time>
          </div>

          <SmokeyChatToggle v-if="smokeyUiMode === 'module'" />
          <SmokeyAssistantPanel v-else />
          <WorkspaceSearch />
          <WorkspaceQuickActions />

          <OrderNotifications />
        </div>
      </nav>
      <main class="min-w-0"><slot /></main>
    </div>
  </div>
</template>

<script setup>
import SmokeyAssistantPanel from "~/components/smokey/SmokeyAssistantPanel.vue";
import SmokeyChatToggle from "~/components/smokey/SmokeyChatToggle.vue";
import {
  Activity,
  BarChart3,
  Boxes,
  CalendarDays,
  ChevronUp,
  ChevronRight,
  ChevronsUpDown,
  ClipboardList,
  Clock3,
  CreditCard,
  Globe2,
  IdCard,
  LayoutGrid,
  Layers3,
  LayoutDashboard,
  LogOut,
  Menu,
  Megaphone,
  MonitorUp,
  Package,
  PanelLeftClose,
  PanelLeftOpen,
  Settings2,
  Store,
  UserRoundCog,
  Truck,
  UsersRound,
  X,
} from "lucide-vue-next";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  formatWorkspaceClock,
  workspaceUserPresentation,
} from "@/utils/workspaceHeader";

const smokeyUiMode = useRuntimeConfig().public.smokeyUiMode;
const emit = defineEmits(["sign-out"]);
const auth = useAuthStore();
const business = useBusinessStore();
const route = useRoute();
const menuOpen = ref(false);
const sidebarCollapsed = ref(false);
const now = ref(new Date());
let clockTimer;
const { style: shellStyle } = useWorkspaceTheme();
const clock = computed(() =>
  formatWorkspaceClock(
    now.value,
    business.activeBusiness?.timezone || "Asia/Manila",
  ),
);
const userIdentity = computed(() => workspaceUserPresentation(auth.user || {}));

const navigation = [
  {
    label: "Live operations",
    items: [
      {
        label: "Live dashboard",
        to: "/workspace",
        icon: LayoutDashboard,
        match: (currentRoute) => currentRoute.path === "/workspace",
      },
      { label: "Orders", to: "/workspace/orders", icon: ClipboardList },
      { label: "Deliveries", to: "/workspace/deliveries", icon: Truck },
      {
        label: "Product requests",
        to: "/workspace/sell/requests",
        icon: CalendarDays,
      },
    ],
  },
  {
    label: "Business insights",
    items: [
      { label: "Analytics", to: "/workspace/analytics", icon: BarChart3 },
      { label: "Smokey", to: "/workspace/smokey", icon: Activity },
      { label: "Business tracker", to: "/workspace/tracker", icon: Activity },
    ],
  },
  {
    label: "Commerce",
    items: [
      {
        label: "Products & services",
        to: "/workspace/sell",
        icon: Package,
        match: sellView("catalog"),
      },
      {
        label: "Categories",
        to: "/workspace/sell/categories",
        icon: LayoutGrid,
      },
      {
        label: "Collections",
        to: "/workspace/sell/collections",
        icon: Layers3,
      },
      {
        label: "Promotions",
        to: "/workspace/sell/promotions",
        icon: Megaphone,
        match: sellView("promotions"),
      },

      {
        label: "Customers",
        to: "/workspace/sell?view=customers",
        icon: UsersRound,
        match: sellView("customers"),
      },
      { label: "POS setup", to: "/workspace/sell/pos", icon: CreditCard },
    ],
  },
  {
    label: "Operations",
    items: [
      {
        label: "Calendar & reservations",
        to: "/workspace/schedule",
        icon: CalendarDays,
      },
      {
        label: "Operations",
        to: "/workspace/operate",
        icon: Boxes,
        match: (currentRoute) =>
          currentRoute.path.startsWith("/workspace/operate") &&
          !currentRoute.path.startsWith("/workspace/operate/workforce"),
      },
      {
        label: "Workforce",
        to: "/workspace/operate/workforce",
        icon: UserRoundCog,
      },
    ],
  },
  {
    label: "Workspace",
    items: [
      { label: "Appearance & branding", to: "/settings/identity", icon: Store },
      { label: "Business card", to: "/workspace/business-card", icon: IdCard },
      {
        label: "Reservations & rentals",
        to: "/settings/commerce",
        icon: Package,
      },
      { label: "Integrations", to: "/settings/integrations", icon: Settings2 },
      {
        label: "Poster & displays",
        to: "/workspace/site/displays",
        icon: MonitorUp,
      },
      { label: "Site builder", to: "/workspace/site", icon: Globe2 },
    ],
  },
];

const activeNavigation = computed(() =>
  navigation
    .flatMap((group) =>
      group.items.map((item) => ({ ...item, group: group.label })),
    )
    .find((item) => isActive(item)),
);
const smokeyHeader = computed(() => {
  if (
    smokeyUiMode !== "module" ||
    !/^\/workspace\/smokey(?:\/|$)/.test(route.path)
  )
    return null;
  const section = route.path.split("/")[3] || "overview";
  const entries = {
    overview: {
      title: "Overview",
      description: "Your assistant, connections, and usage at a glance.",
    },
    assistant: {
      title: "Ask Smokey",
      description: "Useful answers from your authorized business records.",
    },
    connections: {
      title: "AI connections",
      description: "Choose the AI behind your business reports.",
    },
    usage: {
      title: "Usage & limits",
      description:
        "Understand AI activity and stay within your application limits.",
    },
    reports: {
      title: "Reports",
      description: "Revisit the answers saved by your business.",
    },
    appearance: {
      title: "Appearance",
      description: "Make your assistant feel at home.",
    },
  };
  return entries[section] || entries.overview;
});
const breadcrumbs = computed(() => {
  if (route.path === "/workspace") return ["Live dashboard"];
  const item = activeNavigation.value;
  const crumbs = item ? [item.group, item.label] : ["PixelCore"];
  if (smokeyHeader.value)
    crumbs.push(
      route.path.startsWith("/workspace/smokey/reports/")
        ? "Saved report"
        : smokeyHeader.value.title,
    );
  if (route.path === "/workspace/sell/products/new") crumbs.push("Add product");
  if (route.path.startsWith("/workspace/sell/catalog/"))
    crumbs.push("Edit product");
  if (route.path === "/workspace/sell/promotions/new")
    crumbs.push("Create promotion");
  else if (/^\/workspace\/sell\/promotions\/[^/]+/.test(route.path))
    crumbs.push("Edit promotion");
  if (route.path === "/workspace/operate/workforce/employees/new")
    crumbs.push("Create employee");
  else if (
    /^\/workspace\/operate\/workforce\/employees\/[^/]+$/.test(route.path)
  )
    crumbs.push("Employee profile");
  return crumbs;
});
const businessInitial = computed(
  () => business.activeBusiness?.display_name?.charAt(0)?.toUpperCase() || "P",
);
const presetLabel = computed(() =>
  `${business.activeBusiness?.industry_preset || "general"} business`.replace(
    /^./,
    (letter) => letter.toUpperCase(),
  ),
);

onMounted(() => {
  sidebarCollapsed.value =
    window.localStorage.getItem("pixelcore-sidebar-collapsed") === "true";
  clockTimer = window.setInterval(() => {
    now.value = new Date();
  }, 30_000);
});

onBeforeUnmount(() => {
  if (clockTimer) window.clearInterval(clockTimer);
});

function sellView(view) {
  return (currentRoute) => {
    if (
      view === "catalog" &&
      /^\/workspace\/sell\/(catalog|products)(\/|$)/.test(currentRoute.path)
    )
      return true;
    if (
      view === "promotions" &&
      currentRoute.path.startsWith("/workspace/sell/promotions")
    )
      return true;
    return (
      currentRoute.path === "/workspace/sell" &&
      String(currentRoute.query.view || "catalog") === view
    );
  };
}
function isActive(item) {
  return item.match
    ? item.match(route)
    : route.path === item.to.split("?")[0] ||
        (item.to !== "/workspace" &&
          route.path.startsWith(`${item.to.split("?")[0]}/`));
}
function selectBusiness(event) {
  const selected = business.businesses.find(
    (item) => item.public_id === event.target.value,
  );
  if (selected) business.setActiveBusiness(selected);
}
function signOutFromSidebar() {
  menuOpen.value = false;
  emit("sign-out");
}
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value;
  window.localStorage.setItem(
    "pixelcore-sidebar-collapsed",
    String(sidebarCollapsed.value),
  );
}
</script>
