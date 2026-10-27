<template>
  <section class="analytics-page workspace-page space-y-5">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight">Analytics</h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Track sales, product performance, and operations for your business.
        </p>
      </div>
      <div class="flex max-w-full flex-wrap items-center gap-2">
        <Popover v-model:open="rangeOpen">
          <PopoverTrigger as-child>
            <Button
              variant="outline"
              type="button"
              class="h-10 gap-2 bg-card text-xs"
              :disabled="!business.activeBusiness"
              aria-label="Choose reporting date range"
            >
              <CalendarDays class="h-4 w-4 shrink-0" aria-hidden="true" />
              <span class="min-w-0 truncate">{{ rangeLabel }}</span>
              <ChevronDown class="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            </Button>
          </PopoverTrigger>
          <PopoverContent
            align="end"
            class="w-[min(22rem,calc(100vw-2rem))] p-4"
          >
            <form novalidate @submit.prevent="applyRange">
              <h2 class="text-sm font-bold">Reporting period</h2>
              <p class="mt-1 text-xs leading-5 text-muted-foreground">
                Dates follow
                {{ business.activeBusiness?.timezone || "Asia/Manila" }}.
              </p>
              <div class="mt-3 flex flex-wrap gap-1.5">
                <Button
                  v-for="preset in presets"
                  :key="preset.key"
                  variant="outline"
                  size="sm"
                  type="button"
                  class="h-8 px-2 text-xs"
                  @click="choosePreset(preset.key)"
                  >{{ preset.label }}</Button
                >
              </div>
              <div class="mt-4 grid grid-cols-2 gap-3">
                <div>
                  <Label for="analytics-from">From</Label
                  ><Input
                    id="analytics-from"
                    v-model="dateFrom"
                    class="mt-1.5 min-w-0"
                    type="date"
                    :aria-invalid="Boolean(rangeError)"
                    :aria-describedby="
                      rangeError ? 'analytics-range-error' : undefined
                    "
                  />
                </div>
                <div>
                  <Label for="analytics-to">To</Label
                  ><Input
                    id="analytics-to"
                    v-model="dateTo"
                    class="mt-1.5 min-w-0"
                    type="date"
                    :aria-invalid="Boolean(rangeError)"
                    :aria-describedby="
                      rangeError ? 'analytics-range-error' : undefined
                    "
                  />
                </div>
              </div>
              <p
                v-if="rangeError"
                id="analytics-range-error"
                class="mt-3 text-xs leading-5 text-destructive"
                role="alert"
              >
                {{ rangeError }}
              </p>
              <Button type="submit" class="mt-4 w-full">Apply range</Button>
            </form>
          </PopoverContent>
        </Popover>
        <Button
          variant="outline"
          type="button"
          class="h-10 gap-2 bg-card"
          :disabled="loading || !report || Boolean(error)"
          @click="exportReport"
          ><Download class="h-4 w-4" aria-hidden="true" /> Export</Button
        >
      </div>
    </header>

    <Tabs v-model="activeTab">
      <div class="overflow-x-auto pb-1">
        <TabsList
          class="h-auto w-max justify-start gap-1.5 bg-transparent p-0"
          aria-label="Analytics sections"
        >
          <TabsTrigger
            v-for="tab in tabs"
            :key="tab.value"
            :value="tab.value"
            class="h-9 min-w-24 rounded-lg border bg-background px-4 text-xs data-[state=active]:border-primary data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-none"
            >{{ tab.label }}</TabsTrigger
          >
        </TabsList>
      </div>
      <TabsContent :value="activeTab" class="mt-4 space-y-4 outline-none">
        <template v-if="loading">
          <p class="sr-only" role="status">
            Calculating analytics for the selected period.
          </p>
          <div class="analytics-metrics" aria-hidden="true">
            <div
              v-for="item in 6"
              :key="item"
              class="rounded-xl border bg-card p-5"
            >
              <Skeleton class="h-9 w-9 rounded-lg" /><Skeleton
                class="mt-4 h-3 w-24"
              /><Skeleton class="mt-3 h-7 w-28" /><Skeleton
                class="mt-4 h-3 w-32"
              />
            </div>
          </div>
          <div class="grid gap-4 xl:grid-cols-[1.25fr_1fr]" aria-hidden="true">
            <Skeleton class="h-[22rem] rounded-xl" /><Skeleton
              class="h-[22rem] rounded-xl"
            />
          </div>
        </template>
        <StatePanel
          v-else-if="error"
          kind="error"
          title="Analytics unavailable"
          :message="error"
          ><Button variant="outline" type="button" @click="load"
            >Try again</Button
          ></StatePanel
        >
        <StatePanel
          v-else-if="!report"
          kind="empty"
          title="Choose a business"
          message="Select a business from the workspace to view its analytics."
        />
        <template v-else>
          <TooltipProvider :delay-duration="180">
            <dl class="analytics-metrics">
              <AnalyticsMetric
                v-for="metric in metrics"
                :key="metric.label"
                v-bind="metric"
              />
            </dl>
          </TooltipProvider>

          <div
            v-if="['overview', 'sales'].includes(activeTab)"
            class="grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]"
          >
            <AnalyticsSalesChart
              v-model:interval="chartInterval"
              :points="salesPoints"
              :currency="currency"
            />
            <AnalyticsCategoryChart
              :categories="analytics.categories || []"
              :currency="currency"
            />
          </div>

          <div
            class="grid items-start gap-4"
            :class="
              activeTab === 'overview'
                ? '2xl:grid-cols-[minmax(0,1.1fr)_minmax(0,.8fr)_minmax(0,1.1fr)]'
                : activeTab === 'sales'
                  ? 'xl:grid-cols-[minmax(0,.8fr)_minmax(0,1.2fr)]'
                  : ''
            "
          >
            <section
              v-if="['overview', 'products'].includes(activeTab)"
              class="min-w-0 overflow-hidden rounded-xl border bg-card"
              aria-labelledby="products-heading"
            >
              <div
                class="flex items-center justify-between gap-3 px-5 pb-3 pt-5"
              >
                <div>
                  <h2 id="products-heading" class="text-sm font-extrabold">
                    Top products
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-muted-foreground">
                    Ranked by recorded item sales.
                  </p>
                </div>
                <ButtonLink
                  to="/workspace/sell"
                  variant="outline"
                  size="sm"
                  class="h-8 shrink-0 px-2 text-xs"
                  >Catalog<ArrowUpRight class="ml-1 h-3 w-3" aria-hidden="true"
                /></ButtonLink>
              </div>
              <div v-if="topProducts.length" class="overflow-x-auto px-3 pb-3">
                <Table class="min-w-[24rem] text-xs">
                  <TableHeader
                    ><TableRow class="bg-muted/25"
                      ><TableHead class="h-9 w-8 px-2">#</TableHead
                      ><TableHead class="h-9 px-2">Product</TableHead
                      ><TableHead class="h-9 px-2 text-right">Units</TableHead
                      ><TableHead class="h-9 px-2 text-right"
                        >Sales</TableHead
                      ></TableRow
                    ></TableHeader
                  >
                  <TableBody>
                    <TableRow
                      v-for="(item, index) in topProducts"
                      :key="`${item.offering_public_id}-${item.name}`"
                    >
                      <TableCell class="px-2 py-2.5 text-muted-foreground">{{
                        index + 1
                      }}</TableCell>
                      <TableCell class="px-2 py-2.5"
                        ><div class="flex min-w-36 items-center gap-2">
                          <img
                            v-if="item.image_url"
                            :src="item.image_url"
                            alt=""
                            class="h-9 w-9 shrink-0 rounded-md bg-muted object-cover"
                            loading="lazy"
                          /><span
                            v-else
                            class="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-muted"
                            ><Package
                              class="h-4 w-4 text-muted-foreground"
                              aria-hidden="true" /></span
                          ><span
                            class="min-w-0 break-words font-semibold leading-5"
                            >{{ item.name }}</span
                          >
                        </div></TableCell
                      >
                      <TableCell class="px-2 py-2.5 text-right tabular-nums">{{
                        count(item.quantity)
                      }}</TableCell>
                      <TableCell
                        class="whitespace-nowrap px-2 py-2.5 text-right font-bold tabular-nums"
                        >{{ money(item.sales) }}</TableCell
                      >
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
              <div v-else class="px-5 py-14 text-center">
                <Package
                  class="mx-auto h-7 w-7 text-muted-foreground"
                  aria-hidden="true"
                />
                <p class="mt-3 text-sm font-semibold">
                  No product sales in this period
                </p>
                <p class="mt-2 text-xs leading-5 text-muted-foreground">
                  Products and services appear here after an order records an
                  item.
                </p>
              </div>
            </section>

            <section
              v-if="['overview', 'sales'].includes(activeTab)"
              class="min-w-0 rounded-xl border bg-card p-5"
              aria-labelledby="status-heading"
            >
              <h2 id="status-heading" class="text-sm font-extrabold">
                Order status
              </h2>
              <p class="mt-1 text-xs leading-5 text-muted-foreground">
                {{ count(analytics.orders_placed) }} orders placed · includes
                cancellations
              </p>
              <div v-if="statusBreakdown.length" class="mt-5 space-y-4">
                <div v-for="status in statusBreakdown" :key="status.key">
                  <div class="flex items-center justify-between gap-3 text-xs">
                    <span>{{ status.label }}</span
                    ><strong class="tabular-nums">{{
                      count(status.count)
                    }}</strong>
                  </div>
                  <div
                    class="mt-2 h-1.5 overflow-hidden rounded-full bg-muted"
                    aria-hidden="true"
                  >
                    <div
                      class="h-full rounded-full"
                      :class="
                        status.key === 'cancelled' || status.key === 'refunded'
                          ? 'bg-muted-foreground'
                          : 'bg-[var(--brand-primary)]'
                      "
                      :style="{ width: `${status.percent}%` }"
                    />
                  </div>
                </div>
              </div>
              <div v-else class="py-14 text-center">
                <ShoppingCart
                  class="mx-auto h-7 w-7 text-muted-foreground"
                  aria-hidden="true"
                />
                <p class="mt-3 text-sm font-semibold">
                  No orders in this period
                </p>
                <p class="mt-2 text-xs leading-5 text-muted-foreground">
                  Choose another date range to review earlier activity.
                </p>
              </div>
            </section>

            <section
              v-if="['overview', 'sales'].includes(activeTab)"
              class="min-w-0 overflow-hidden rounded-xl border bg-card"
              aria-labelledby="recent-heading"
            >
              <div
                class="flex items-center justify-between gap-3 px-5 pb-3 pt-5"
              >
                <div>
                  <h2 id="recent-heading" class="text-sm font-extrabold">
                    Recent orders
                  </h2>
                  <p class="mt-1 text-xs leading-5 text-muted-foreground">
                    Latest orders in this reporting period.
                  </p>
                </div>
                <ButtonLink
                  to="/workspace/orders"
                  variant="outline"
                  size="sm"
                  class="h-8 shrink-0 px-2 text-xs"
                  >View all</ButtonLink
                >
              </div>
              <div v-if="recentOrders.length" class="overflow-x-auto px-3 pb-3">
                <Table class="min-w-[24rem] text-xs">
                  <TableHeader
                    ><TableRow class="bg-muted/25"
                      ><TableHead class="h-9 px-2">Order / customer</TableHead
                      ><TableHead class="h-9 px-2 text-right">Amount</TableHead
                      ><TableHead class="h-9 px-2 text-right"
                        >Status</TableHead
                      ></TableRow
                    ></TableHeader
                  >
                  <TableBody
                    ><TableRow
                      v-for="order in recentOrders"
                      :key="order.public_id"
                      ><TableCell class="px-2 py-3"
                        ><strong class="block font-semibold">{{
                          order.number
                        }}</strong
                        ><span
                          class="mt-1 block max-w-40 break-words text-muted-foreground"
                          >{{ order.customer_name }}</span
                        ></TableCell
                      ><TableCell
                        class="whitespace-nowrap px-2 py-3 text-right font-bold tabular-nums"
                        >{{ money(order.grand_total) }}</TableCell
                      ><TableCell class="px-2 py-3 text-right"
                        ><Badge
                          :variant="
                            ['cancelled', 'refunded'].includes(order.status)
                              ? 'outline'
                              : 'secondary'
                          "
                          class="whitespace-nowrap text-[0.625rem]"
                          >{{ statusLabel(order.status) }}</Badge
                        ></TableCell
                      ></TableRow
                    ></TableBody
                  >
                </Table>
              </div>
              <div v-else class="px-5 py-14 text-center">
                <ReceiptText
                  class="mx-auto h-7 w-7 text-muted-foreground"
                  aria-hidden="true"
                />
                <p class="mt-3 text-sm font-semibold">No recent orders</p>
                <p class="mt-2 text-xs leading-5 text-muted-foreground">
                  Orders placed in your selected date range will appear here.
                </p>
              </div>
            </section>
          </div>

          <section
            v-if="['overview', 'operations'].includes(activeTab)"
            class="rounded-xl border bg-card p-5"
            aria-labelledby="operations-heading"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 id="operations-heading" class="text-sm font-extrabold">
                  Operational summary
                </h2>
                <p class="mt-1 text-xs leading-5 text-muted-foreground">
                  Bookings follow this period. Inventory and invoices show their
                  current position.
                </p>
              </div>
              <ButtonLink
                to="/workspace/tracker"
                variant="outline"
                size="sm"
                class="h-8 text-xs"
                >Business tracker<ArrowUpRight
                  class="ml-1 h-3 w-3"
                  aria-hidden="true"
              /></ButtonLink>
            </div>
            <dl class="mt-5 grid gap-x-6 gap-y-4 sm:grid-cols-2 xl:grid-cols-4">
              <div
                v-for="item in summary"
                :key="item.label"
                class="border-t pt-3"
              >
                <dt class="text-xs text-muted-foreground">{{ item.label }}</dt>
                <dd class="mt-2 text-lg font-extrabold tabular-nums">
                  {{ item.value }}
                </dd>
              </div>
            </dl>
          </section>
          <p
            class="flex flex-wrap items-center gap-x-3 gap-y-1 text-[0.6875rem] leading-5 text-muted-foreground"
          >
            <span class="inline-flex items-center gap-1.5"
              ><ShieldCheck class="h-3.5 w-3.5" aria-hidden="true" />Actual
              recorded transactions</span
            ><span
              >{{ report.timezone || business.activeBusiness?.timezone }} ·
              {{ rangeLabel }}</span
            ><span>Operational report; not an accounting statement.</span>
          </p>
        </template>
      </TabsContent>
    </Tabs>
  </section>
</template>

<script setup>
import {
  ArrowUpRight,
  Banknote,
  BarChart3,
  CalendarDays,
  ChevronDown,
  Download,
  Package,
  ReceiptText,
  ShieldCheck,
  ShoppingCart,
  Tag,
  WalletCards,
} from "lucide-vue-next";
import AnalyticsMetric from "~/components/workspace/analytics/AnalyticsMetric.vue";
import AnalyticsSalesChart from "~/components/workspace/analytics/AnalyticsSalesChart.vue";
import AnalyticsCategoryChart from "~/components/workspace/analytics/AnalyticsCategoryChart.vue";
import {
  analyticsCsv,
  analyticsMetricDefinitions,
  dateKeyInZone,
  groupSalesActivity,
  shiftDate,
  validReportRange,
} from "~/utils/analytics";

useHead({ title: "Analytics · PixelCore" });
const business = useBusinessStore();
const { apiFetch } = useApiClient();
const route = useRoute();
const router = useRouter();
const report = ref(null);
const loading = ref(true);
const error = ref("");
const rangeOpen = ref(false);
const rangeError = ref("");
const dateFrom = ref("");
const dateTo = ref("");
const appliedFrom = ref("");
const appliedTo = ref("");
const tabs = [
  { value: "overview", label: "Overview" },
  { value: "sales", label: "Sales" },
  { value: "products", label: "Products" },
  { value: "operations", label: "Operations" },
];
const presets = [
  { key: "month", label: "This month" },
  { key: "7", label: "Last 7 days" },
  { key: "30", label: "Last 30 days" },
];
let mounted = false;
let requestVersion = 0;
let controller;

const activeTab = computed({
  get: () =>
    tabs.some((tab) => tab.value === route.query.tab)
      ? route.query.tab
      : "overview",
  set: (tab) => router.replace({ query: { ...route.query, tab } }),
});
const chartInterval = computed({
  get: () =>
    ["daily", "weekly", "monthly"].includes(route.query.interval)
      ? route.query.interval
      : "daily",
  set: (interval) => router.replace({ query: { ...route.query, interval } }),
});
const currency = computed(
  () => report.value?.currency || business.activeBusiness?.currency || "PHP",
);
const rangeLabel = computed(() =>
  appliedFrom.value && appliedTo.value
    ? `${shortDate(appliedFrom.value)} – ${shortDate(appliedTo.value)}`
    : "Choose dates",
);
const analytics = computed(() => report.value?.analytics || {});
const daily = computed(() => report.value?.daily_activity || []);
const salesPoints = computed(() =>
  groupSalesActivity(daily.value, chartInterval.value),
);
const topProducts = computed(() => analytics.value.top_products || []);
const recentOrders = computed(() => analytics.value.recent_orders || []);
const statusBreakdown = computed(() =>
  (analytics.value.status_breakdown || [])
    .filter((row) => row.count > 0)
    .map((row) => ({
      ...row,
      percent: analytics.value.orders_placed
        ? (row.count / analytics.value.orders_placed) * 100
        : 0,
    })),
);
const metricIcons = {
  Banknote,
  BarChart3,
  CalendarDays,
  Package,
  ReceiptText,
  ShoppingCart,
  Tag,
  WalletCards,
};
const metrics = computed(() =>
  analyticsMetricDefinitions(
    report.value,
    activeTab.value,
    business.activeBusiness?.industry_preset === "restaurant",
  ).map((metric) => ({
    ...metric,
    value:
      metric.format === "money"
        ? money(metric.value)
        : metric.format === "percent"
          ? new Intl.NumberFormat("en-PH", {
              style: "percent",
              maximumFractionDigits: 1,
            }).format(metric.value)
          : count(metric.value),
    icon: metricIcons[metric.icon],
  })),
);
const summary = computed(() =>
  report.value
    ? [
        {
          label:
            business.activeBusiness?.industry_preset === "restaurant"
              ? "Reservations in period"
              : "Bookings in period",
          value: count(report.value.bookings.total),
        },
        {
          label: "Confirmed bookings",
          value: count(report.value.bookings.confirmed),
        },
        {
          label: "Current inventory at cost",
          value: money(report.value.inventory.value_at_cost),
        },
        {
          label: "Current low-stock items",
          value: count(report.value.inventory.low_stock_items),
        },
        {
          label: "Current open invoices",
          value: count(report.value.invoice_aging.open_count),
        },
        {
          label: "Current overdue invoices",
          value: count(report.value.invoice_aging.overdue_count),
        },
        {
          label: "Current invoice balance",
          value: money(report.value.invoice_aging.outstanding),
        },
        {
          label: "Invoice payments in period",
          value: money(report.value.collected_payments),
        },
      ]
    : [],
);

function syncRangeFromRoute() {
  const today = dateKeyInZone(
    new Date(),
    business.activeBusiness?.timezone || "Asia/Manila",
  );
  const valid = validReportRange(route.query.from, route.query.to);
  appliedFrom.value = valid ? route.query.from : `${today.slice(0, 7)}-01`;
  appliedTo.value = valid ? route.query.to : today;
  dateFrom.value = appliedFrom.value;
  dateTo.value = appliedTo.value;
  rangeError.value = "";
}
async function applyRange() {
  if (!validReportRange(dateFrom.value, dateTo.value)) {
    rangeError.value =
      "Choose valid dates with the end on or after the start, no more than 366 days apart.";
    return;
  }
  rangeError.value = "";
  rangeOpen.value = false;
  if (dateFrom.value === appliedFrom.value && dateTo.value === appliedTo.value)
    await load();
  else
    await router.replace({
      query: { ...route.query, from: dateFrom.value, to: dateTo.value },
    });
}
function choosePreset(key) {
  const today = dateKeyInZone(
    new Date(),
    business.activeBusiness?.timezone || "Asia/Manila",
  );
  dateTo.value = today;
  dateFrom.value =
    key === "month"
      ? `${today.slice(0, 7)}-01`
      : shiftDate(today, 1 - Number(key));
  rangeError.value = "";
}
async function load() {
  const version = ++requestVersion;
  controller?.abort();
  controller = new AbortController();
  loading.value = true;
  error.value = "";
  report.value = null;
  if (!business.activeBusiness) {
    loading.value = false;
    return;
  }
  try {
    const result = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/reports/`,
      {
        query: { date_from: appliedFrom.value, date_to: appliedTo.value },
        signal: controller.signal,
      },
    );
    if (version === requestVersion) report.value = result;
  } catch (requestError) {
    if (version === requestVersion)
      error.value =
        requestError?.data?.error?.message ||
        "PixelCore could not calculate analytics. Try again or choose another date range.";
  } finally {
    if (version === requestVersion) loading.value = false;
  }
}
onMounted(async () => {
  window.addEventListener("pixelcore:operations-created", handleQuickCreate);
  try {
    if (!business.activeBusiness) await business.loadBusinesses();
    syncRangeFromRoute();
    mounted = true;
    await load();
  } catch {
    loading.value = false;
    error.value =
      "PixelCore could not load your business. Refresh the workspace and try again.";
  }
});
watch(
  () => [business.activeBusiness?.public_id, route.query.from, route.query.to],
  () => {
    if (!mounted) return;
    syncRangeFromRoute();
    load();
  },
);
onBeforeUnmount(() => {
  window.removeEventListener("pixelcore:operations-created", handleQuickCreate);
  mounted = false;
  requestVersion += 1;
  controller?.abort();
});

function handleQuickCreate(event) {
  if (event.detail?.businessId === business.activeBusiness?.public_id) load();
}

function exportReport() {
  if (!report.value || loading.value || error.value) return;
  const rows = [
    ["Business", business.activeBusiness?.display_name],
    ["Period", appliedFrom.value, appliedTo.value],
    ["Section", activeTab.value],
    ["Currency", currency.value],
    ["Timezone", report.value.timezone],
    ["Basis", report.value.basis],
    [],
    ["Metric", "Value"],
    ...metrics.value.map((metric) => [metric.label, metric.value]),
    [],
    ["Date", "Gross sales", "Orders", "Expenses"],
    ...daily.value.map((day) => [
      day.date,
      Number(day.sales),
      Number(day.orders),
      Number(day.expenses),
    ]),
    [],
    ["Product", "Units", "Distinct orders", "Item sales"],
    ...topProducts.value.map((item) => [
      item.name,
      Number(item.quantity),
      Number(item.orders),
      Number(item.sales),
    ]),
    [],
    ["Category", "Item sales"],
    ...(analytics.value.categories || []).map((row) => [
      row.name,
      Number(row.sales),
    ]),
  ];
  const blob = new Blob([analyticsCsv(rows)], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `analytics-${appliedFrom.value}-${appliedTo.value}.csv`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const money = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: currency.value,
  }).format(Number(value || 0));
const count = (value) =>
  new Intl.NumberFormat("en-PH").format(Number(value || 0));
const shortDate = (value) =>
  new Intl.DateTimeFormat("en-PH", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T12:00:00Z`));
const statusLabel = (value) =>
  ({
    pending: "Pending",
    confirmed: "Confirmed",
    processing: "Processing",
    fulfilled: "Fulfilled",
    cancelled: "Cancelled",
    refunded: "Refunded",
  })[value] || value;
</script>

<style scoped>
.analytics-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}
@media (min-width: 768px) {
  .analytics-metrics {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (min-width: 1400px) {
  .analytics-metrics {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}
</style>
