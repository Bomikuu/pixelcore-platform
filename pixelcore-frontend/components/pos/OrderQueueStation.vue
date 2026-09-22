<template>
  <main class="min-h-dvh bg-muted/30 text-foreground">
    <DevicePairingPanel
      v-if="!deviceToken"
      v-model="code"
      :title="pairingTitle"
      :description="pairingDescription"
      :details="pairingDetails"
      :audience="pairingAudience"
      :action-label="`Pair ${screenName}`"
      :working="pairing"
      :message="message"
      :icon="mode === 'delivery' ? Truck : PackageCheck"
      @submit="pair"
    />

    <section v-else class="min-h-dvh">
      <header class="sticky top-0 z-30 border-b bg-background/95 backdrop-blur">
        <div
          class="flex min-h-16 flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6"
        >
          <div class="flex min-w-0 items-center gap-3">
            <img
              v-if="payload?.business?.logo_url"
              :src="payload.business.logo_url"
              alt=""
              class="h-10 w-10 rounded-lg border object-cover"
            />
            <div
              v-else
              class="grid h-10 w-10 place-items-center rounded-lg bg-primary font-extrabold text-primary-foreground"
            >
              <PackageCheck
                v-if="mode === 'preparation'"
                class="h-5 w-5"
                aria-hidden="true"
              /><Truck v-else class="h-5 w-5" aria-hidden="true" />
            </div>
            <div class="min-w-0">
              <h1 class="truncate font-extrabold">{{ screenTitle }}</h1>
              <p class="truncate text-xs text-muted-foreground">
                {{ payload?.device?.name || screenName }} ·
                {{ payload?.business?.display_name }}
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <Badge variant="outline" class="gap-1.5"
              ><span
                class="h-2 w-2 rounded-full"
                :class="
                  connectionState === 'connected'
                    ? 'bg-emerald-500'
                    : 'bg-amber-500'
                "
                aria-hidden="true"
              />{{
                connectionState === "connected" ? "Live" : "Reconnecting"
              }}</Badge
            ><span
              class="hidden text-sm font-semibold tabular-nums text-muted-foreground sm:inline"
              >{{ currentTime }}</span
            ><Button
              variant="outline"
              size="sm"
              type="button"
              @click="toggleFullscreen"
              ><Maximize2 class="h-4 w-4" aria-hidden="true" /> Full
              screen</Button
            ><Button
              variant="ghost"
              size="icon"
              type="button"
              aria-label="Unpair screen"
              @click="unpair"
              ><Unplug class="h-4 w-4" aria-hidden="true"
            /></Button>
          </div>
        </div>
        <div
          class="grid grid-cols-3 border-t"
          :class="mode === 'preparation' ? 'bg-amber-50/70' : 'bg-sky-50/70'"
        >
          <div
            v-for="lane in lanes"
            :key="lane.key"
            class="border-r px-4 py-3 last:border-r-0 sm:px-6"
          >
            <p class="text-xs font-semibold text-muted-foreground">
              {{ lane.label }}
            </p>
            <p class="mt-0.5 text-xl font-extrabold tabular-nums">
              {{ ordersByStage(lane.key).length }}
            </p>
          </div>
        </div>
      </header>

      <StatePanel
        v-if="loading && !payload"
        class="m-6"
        kind="loading"
        :title="`Opening ${screenName}`"
        message="Retrieving confirmed orders and their current fulfillment state."
      />
      <StatePanel
        v-else-if="fatalError"
        class="m-6"
        kind="error"
        :title="`${screenName} unavailable`"
        :message="fatalError"
        ><Button type="button" @click="load">Reconnect</Button></StatePanel
      >
      <section v-else class="p-4 sm:p-6" aria-live="polite">
        <Alert v-if="connectionState === 'reconnecting'" class="mb-4"
          ><WifiOff class="h-4 w-4" aria-hidden="true" /><AlertTitle
            >Connection interrupted</AlertTitle
          ><AlertDescription
            >The last queue remains visible. PixelCore will keep retrying
            automatically.</AlertDescription
          ></Alert
        >
        <div class="grid items-start gap-4 lg:grid-cols-3">
          <section
            v-for="lane in lanes"
            :key="lane.key"
            :aria-labelledby="`${mode}-${lane.key}`"
            class="min-w-0 rounded-xl border bg-background"
          >
            <header
              class="flex items-center justify-between border-b px-4 py-3"
            >
              <div>
                <h2 :id="`${mode}-${lane.key}`" class="font-extrabold">
                  {{ lane.label }}
                </h2>
                <p class="mt-0.5 text-xs text-muted-foreground">
                  {{ lane.description }}
                </p>
              </div>
              <Badge variant="secondary">{{
                ordersByStage(lane.key).length
              }}</Badge>
            </header>
            <div v-if="ordersByStage(lane.key).length" class="divide-y">
              <article
                v-for="order in ordersByStage(lane.key)"
                :key="order.public_id"
                class="p-4"
              >
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <p class="text-lg font-extrabold">{{ order.number }}</p>
                    <p class="mt-1 text-xs text-muted-foreground">
                      {{ elapsed(order.placed_at) }} ·
                      {{ fulfillmentLabel(order.fulfillment_type) }}
                    </p>
                  </div>
                  <StatusPill :value="order.payment_status" />
                </div>
                <div class="mt-4 space-y-3">
                  <div
                    v-for="item in order.items"
                    :key="item.public_id"
                    class="flex gap-3"
                  >
                    <img
                      v-if="item.image_url"
                      :src="item.image_url"
                      alt=""
                      class="h-11 w-11 shrink-0 rounded-lg border object-cover"
                    />
                    <div
                      v-else
                      class="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-secondary"
                    >
                      <Package
                        class="h-4 w-4 text-muted-foreground"
                        aria-hidden="true"
                      />
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="font-bold">
                        <span class="tabular-nums">{{ item.quantity }}×</span>
                        {{ item.name }}
                      </p>
                      <p
                        v-if="selectedOptions(item).length"
                        class="mt-0.5 line-clamp-2 text-xs text-muted-foreground"
                      >
                        {{ selectedOptions(item).join(" · ") }}
                      </p>
                    </div>
                  </div>
                </div>
                <div
                  v-if="mode === 'delivery'"
                  class="mt-4 rounded-lg bg-muted p-3 text-sm"
                >
                  <p class="font-bold">{{ customerName(order) }}</p>
                  <p class="mt-1 leading-5 text-muted-foreground">
                    {{ shippingAddress(order) }}
                  </p>
                  <p
                    v-if="order.customer_snapshot?.phone"
                    class="mt-1 font-semibold"
                  >
                    {{ order.customer_snapshot.phone }}
                  </p>
                </div>
                <div
                  v-else-if="order.customer_snapshot"
                  class="mt-4 flex items-center justify-between border-t pt-3 text-xs"
                >
                  <span class="text-muted-foreground"
                    >For {{ customerName(order) }}</span
                  ><strong class="tabular-nums">{{
                    money(order.grand_total)
                  }}</strong>
                </div>
                <Button
                  v-if="nextAction(order)"
                  class="mt-4 w-full"
                  :variant="lane.key === 'ready' ? 'default' : 'outline'"
                  type="button"
                  :disabled="workingOrderId === order.public_id"
                  @click="updateOrder(order, nextAction(order).value)"
                  ><component
                    :is="nextAction(order).icon"
                    class="h-4 w-4"
                    aria-hidden="true"
                  />{{
                    workingOrderId === order.public_id
                      ? "Updating…"
                      : nextAction(order).label
                  }}</Button
                >
                <p
                  v-else
                  class="mt-4 rounded-lg bg-muted px-3 py-2 text-center text-xs font-semibold text-muted-foreground"
                >
                  Awaiting the delivery team
                </p>
              </article>
            </div>
            <div v-else class="px-4 py-10 text-center">
              <CircleCheck
                class="mx-auto h-7 w-7 text-muted-foreground/45"
                aria-hidden="true"
              />
              <p class="mt-3 text-sm font-bold">{{ lane.empty }}</p>
            </div>
          </section>
        </div>
      </section>
    </section>
  </main>
</template>

<script setup>
import {
  CircleCheck,
  Maximize2,
  Package,
  PackageCheck,
  Play,
  Send,
  Truck,
  Unplug,
  WifiOff,
} from "lucide-vue-next";
import { toast } from "@/components/ui/toast";

const props = defineProps({
  expectedType: { type: String, required: true },
  tokenKey: { type: String, required: true },
});
const config = useRuntimeConfig();
const deviceToken = ref("");
const code = ref("");
const payload = ref(null);
const message = ref("");
const fatalError = ref("");
const pairing = ref(false);
const loading = ref(false);
const connectionState = ref("connecting");
const workingOrderId = ref("");
const currentTime = ref("");
let poller;
let clockTimer;
let knownOrderIds = new Set();
const mode = computed(() =>
  props.expectedType === "dispatch_display" ? "delivery" : "preparation",
);
const screenName = computed(() =>
  mode.value === "delivery" ? "delivery screen" : "fulfillment screen",
);
const screenTitle = computed(() =>
  mode.value === "delivery" ? "Delivery board" : "Fulfillment queue",
);
const queueDescription = computed(() =>
  mode.value === "delivery"
    ? "incoming delivery orders"
    : "confirmed orders that require preparation or packing",
);
const pairingTitle = computed(() =>
  mode.value === "delivery" ? "Delivery operations" : "Order fulfillment",
);
const pairingDescription = computed(() =>
  mode.value === "delivery"
    ? "A dedicated dispatch view for incoming delivery orders and final handoff."
    : "A dedicated preparation view for packing, production, inventory, or service teams.",
);
const pairingDetails = computed(() =>
  mode.value === "delivery"
    ? [
        "See delivery-only orders with customer and address details.",
        "Move work through incoming, packing, ready, and delivered.",
        "Keep delivery completion separate from cashier checkout.",
      ]
    : [
        "Receive confirmed orders without opening the admin workspace.",
        "Move work through new, in-progress, ready, and collected.",
        "Show product images, quantities, options, and elapsed time.",
      ],
);
const pairingAudience = computed(() =>
  mode.value === "delivery"
    ? "Dispatch or delivery team"
    : "Packing, inventory, production, or service team",
);
const orders = computed(() => payload.value?.orders || []);
const lanes = computed(() =>
  mode.value === "delivery"
    ? [
        {
          key: "new",
          label: "Incoming",
          description: "Confirmed delivery orders",
          empty: "No incoming deliveries",
        },
        {
          key: "active",
          label: "Packing",
          description: "Orders being prepared",
          empty: "Nothing being packed",
        },
        {
          key: "ready",
          label: "Ready to dispatch",
          description: "Awaiting handoff or delivery",
          empty: "No orders awaiting dispatch",
        },
      ]
    : [
        {
          key: "new",
          label: "New",
          description: "Confirmed and waiting",
          empty: "No new orders",
        },
        {
          key: "active",
          label: "In progress",
          description: "Being prepared or packed",
          empty: "Nothing in progress",
        },
        {
          key: "ready",
          label: "Ready",
          description: "Awaiting collection or handoff",
          empty: "Nothing waiting for handoff",
        },
      ],
);

onMounted(() => {
  deviceToken.value = localStorage.getItem(props.tokenKey) || "";
  updateClock();
  clockTimer = window.setInterval(updateClock, 30000);
  if (deviceToken.value) start();
});
onBeforeUnmount(() => {
  window.clearInterval(poller);
  window.clearInterval(clockTimer);
});

async function pair() {
  if (pairing.value || code.value.length !== 8) return;
  pairing.value = true;
  message.value = "";
  try {
    const response = await $fetch("devices/pair/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      body: { pairing_code: code.value, device_type: props.expectedType },
    });
    if (response.device.device_type !== props.expectedType)
      throw new Error(`This code belongs to another device type.`);
    deviceToken.value = response.device_token;
    localStorage.setItem(props.tokenKey, response.device_token);
    await start();
  } catch (error) {
    message.value =
      error?.data?.error?.message || error.message || "Pairing failed.";
  } finally {
    pairing.value = false;
  }
}
async function start() {
  window.clearInterval(poller);
  await load();
  if (deviceToken.value) poller = window.setInterval(load, 5000);
}
async function load() {
  loading.value = true;
  try {
    const response = await $fetch("devices/orders/queue/", {
      baseURL: config.public.apiBaseUrl,
      headers: { "X-Device-Token": deviceToken.value },
    });
    const nextIds = new Set(response.orders.map((order) => order.public_id));
    const arrivals = response.orders.filter(
      (order) => !knownOrderIds.has(order.public_id),
    );
    if (knownOrderIds.size && arrivals.length)
      toast({
        title: `${arrivals.length} new order${arrivals.length === 1 ? "" : "s"}`,
        description: arrivals.map((order) => order.number).join(", "),
      });
    knownOrderIds = nextIds;
    payload.value = response;
    connectionState.value = "connected";
    fatalError.value = "";
  } catch (error) {
    if (error?.response?.status === 403) {
      unpair();
      message.value =
        "This screen was revoked or expired. Enter a new setup code.";
    } else if (payload.value) connectionState.value = "reconnecting";
    else fatalError.value = "PixelCore could not load this order queue.";
  } finally {
    loading.value = false;
  }
}
async function updateOrder(order, action) {
  workingOrderId.value = order.public_id;
  try {
    const updated = await $fetch(`devices/orders/${order.public_id}/status/`, {
      baseURL: config.public.apiBaseUrl,
      method: "PATCH",
      headers: { "X-Device-Token": deviceToken.value },
      body: { action },
    });
    if (updated.status === "fulfilled")
      payload.value.orders = orders.value.filter(
        (item) => item.public_id !== order.public_id,
      );
    else Object.assign(order, updated);
    toast({
      title:
        action === "start"
          ? "Work started"
          : action === "ready"
            ? "Order marked ready"
            : "Order completed",
      description: order.number,
    });
  } catch (error) {
    toast({
      title: "Order not updated",
      description:
        error?.data?.error?.message || "Refresh the queue and try again.",
      variant: "destructive",
    });
    await load();
  } finally {
    workingOrderId.value = "";
  }
}
function orderStage(order) {
  const status = order.fulfillments?.[0]?.status;
  return status === "ready"
    ? "ready"
    : order.status === "processing"
      ? "active"
      : "new";
}
function ordersByStage(stage) {
  return orders.value.filter((order) => orderStage(order) === stage);
}
function nextAction(order) {
  const stage = orderStage(order);
  if (stage === "new")
    return {
      value: "start",
      label: mode.value === "delivery" ? "Start packing" : "Start preparing",
      icon: Play,
    };
  if (stage === "active")
    return {
      value: "ready",
      label: mode.value === "delivery" ? "Ready to dispatch" : "Mark ready",
      icon: Send,
    };
  if (
    stage === "ready" &&
    (mode.value === "delivery" || order.fulfillment_type !== "delivery")
  )
    return {
      value: "complete",
      label: mode.value === "delivery" ? "Mark delivered" : "Mark collected",
      icon: CircleCheck,
    };
  return null;
}
function selectedOptions(item) {
  return (item.offering_snapshot?.selected_options || []).map(
    (option) => option.name,
  );
}
function customerName(order) {
  return (
    [order.customer_snapshot?.first_name, order.customer_snapshot?.last_name]
      .filter(Boolean)
      .join(" ") || "Walk-in customer"
  );
}
function shippingAddress(order) {
  const address = order.shipping_snapshot || {};
  return (
    [address.line1, address.city, address.region].filter(Boolean).join(", ") ||
    "Delivery address not provided"
  );
}
function fulfillmentLabel(value) {
  return (
    { delivery: "Delivery", pickup: "Pickup", none: "On premises" }[value] ||
    "Order"
  );
}
function elapsed(value) {
  const minutes = Math.max(
    0,
    Math.floor((Date.now() - new Date(value).getTime()) / 60000),
  );
  return minutes < 1
    ? "Just now"
    : minutes < 60
      ? `${minutes} min waiting`
      : `${Math.floor(minutes / 60)}h ${minutes % 60}m waiting`;
}
function updateClock() {
  currentTime.value = new Intl.DateTimeFormat("en-PH", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date());
}
function toggleFullscreen() {
  if (!document.fullscreenElement)
    document.documentElement.requestFullscreen?.();
  else document.exitFullscreen?.();
}
function unpair() {
  window.clearInterval(poller);
  localStorage.removeItem(props.tokenKey);
  deviceToken.value = "";
  payload.value = null;
  knownOrderIds = new Set();
  code.value = "";
}
const money = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: payload.value?.business?.currency || "PHP",
  }).format(Number(value || 0));
</script>
