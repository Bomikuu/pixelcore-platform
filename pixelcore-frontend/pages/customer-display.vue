<template>
  <main
    class="min-h-dvh bg-[var(--display-ink)] text-[var(--display-paper)]"
    :style="displayStyle"
  >
    <DevicePairingPanel
      v-if="!deviceToken"
      v-model="code"
      title="Customer order display"
      description="A presentation-safe view for the person at the counter—never a copy of the cashier or admin workspace."
      :details="[
        'Show only the basket from one explicitly linked counter.',
        'Rotate published promotions and business branding beside the order.',
        'Move from live totals to a clear completed receipt automatically.',
      ]"
      audience="Customer-facing screen"
      action-label="Pair customer display"
      :working="pairing"
      :message="message"
      illustration="customer"
      @submit="pair"
    />

    <section
      v-else
      class="grid min-h-dvh lg:grid-cols-[minmax(0,1.3fr)_minmax(25rem,.7fr)]"
    >
      <section
        class="relative isolate flex min-h-[42vh] flex-col overflow-hidden p-7 sm:p-10 lg:min-h-dvh lg:p-12"
      >
        <img
          v-if="activeAd?.image_url || brandCover"
          :src="activeAd?.image_url || brandCover"
          alt=""
          class="absolute inset-0 -z-20 h-full w-full object-cover"
        />
        <div
          class="absolute inset-0 -z-10 bg-[linear-gradient(110deg,rgba(8,24,22,.9)_0%,rgba(8,24,22,.58)_58%,rgba(8,24,22,.28)_100%)]"
          aria-hidden="true"
        />
        <header class="flex items-center justify-between gap-5">
          <div class="flex items-center gap-3">
            <img
              v-if="payload?.business?.logo_url"
              :src="payload.business.logo_url"
              alt=""
              class="h-10 w-10 rounded-lg bg-white object-cover"
            />
            <div>
              <p class="font-extrabold">
                {{ payload?.business?.display_name || "Customer display" }}
              </p>
              <p
                v-if="payload?.station_name"
                class="mt-0.5 text-xs text-white/55"
              >
                {{ payload.station_name }}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            class="text-white/55 hover:bg-white/10 hover:text-white"
            type="button"
            @click="unpair"
            >Disconnect</Button
          >
        </header>

        <div class="my-auto max-w-3xl py-12">
          <p
            v-if="activeAd"
            class="text-sm font-bold uppercase tracking-[.14em] text-[var(--display-accent)]"
          >
            Now at {{ payload?.business?.display_name }}
          </p>
          <h1
            class="mt-3 max-w-3xl text-4xl font-extrabold leading-[1.04] tracking-[-.035em] sm:text-6xl lg:text-7xl"
          >
            {{
              activeAd?.heading ||
              payload?.business?.tagline ||
              `Welcome to ${payload?.business?.display_name || "our store"}`
            }}
          </h1>
          <p
            v-if="activeAd?.message"
            class="mt-5 max-w-2xl text-lg leading-8 text-white/72"
          >
            {{ activeAd.message }}
          </p>
        </div>

        <footer class="flex items-center justify-between gap-4">
          <div
            v-if="ads.length > 1"
            class="flex gap-2"
            aria-label="Advertisement rotation"
          >
            <span
              v-for="(ad, index) in ads"
              :key="ad.public_id"
              class="h-1.5 rounded-full transition-[width,background-color] duration-200"
              :class="
                index === adIndex
                  ? 'w-8 bg-[var(--display-accent)]'
                  : 'w-3 bg-white/30'
              "
            />
          </div>
          <span v-else />
          <p class="text-xs text-white/55">Live order display</p>
        </footer>
      </section>

      <aside
        class="flex min-h-[58vh] flex-col bg-[#fbfaf6] text-[#142522] lg:min-h-dvh"
        aria-live="polite"
      >
        <header
          class="flex items-center justify-between border-b border-black/10 px-6 py-5 sm:px-8"
        >
          <div>
            <p class="text-sm font-extrabold">{{ orderHeading }}</p>
            <p class="mt-0.5 text-xs text-black/50">
              Prices update from the counter
            </p>
          </div>
          <Badge
            variant="outline"
            class="border-black/15 bg-white text-[#142522]"
            >{{
              connectionState === "reconnecting"
                ? "Reconnecting…"
                : payload?.linked
                  ? "Connected"
                  : "Waiting for station"
            }}</Badge
          >
        </header>

        <div v-if="currentOrder" class="flex flex-1 flex-col p-6 sm:p-8">
          <div
            class="grid h-12 w-12 place-items-center rounded-full bg-emerald-100 text-emerald-700"
          >
            <Check class="h-6 w-6" aria-hidden="true" />
          </div>
          <h2 class="mt-5 text-3xl font-extrabold tracking-[-.025em]">
            Thank you
          </h2>
          <p class="mt-2 text-sm text-black/55">
            Order {{ currentOrder.number }} is complete.
          </p>
          <div class="mt-7 divide-y border-y border-black/10">
            <article
              v-for="item in currentOrder.items"
              :key="item.public_id"
              class="flex gap-3 py-4"
            >
              <div
                class="h-14 w-14 shrink-0 overflow-hidden rounded-lg bg-black/5"
              >
                <img
                  v-if="item.image_url"
                  :src="item.image_url"
                  :alt="item.name"
                  class="h-full w-full object-cover"
                /><Package
                  v-else
                  class="m-4 h-6 w-6 text-black/25"
                  aria-hidden="true"
                />
              </div>
              <div class="min-w-0 flex-1">
                <p class="font-bold">{{ item.quantity }} × {{ item.name }}</p>
                <p class="mt-1 text-xs text-black/45">
                  {{ item.offering_snapshot?.variant_name || "Standard" }}
                </p>
              </div>
              <strong class="shrink-0 tabular-nums">{{
                money(item.line_total)
              }}</strong>
            </article>
          </div>
          <OrderTotals class="mt-auto" :order="currentOrder" />
        </div>

        <div
          v-else-if="cart?.items?.length"
          class="flex flex-1 flex-col overflow-hidden"
        >
          <div class="min-h-0 flex-1 overflow-y-auto px-6 sm:px-8">
            <article
              v-for="(item, index) in cart.items"
              :key="`${item.offering_public_id}-${index}`"
              class="flex gap-3 border-b border-black/10 py-4"
            >
              <div
                class="h-14 w-14 shrink-0 overflow-hidden rounded-lg bg-black/5"
              >
                <img
                  v-if="item.image_url"
                  :src="item.image_url"
                  :alt="item.name"
                  class="h-full w-full object-cover"
                /><Package
                  v-else
                  class="m-4 h-6 w-6 text-black/25"
                  aria-hidden="true"
                />
              </div>
              <div class="min-w-0 flex-1">
                <p class="font-bold">{{ item.quantity }} × {{ item.name }}</p>
                <p
                  v-if="item.variant_name || item.options?.length"
                  class="mt-1 truncate text-xs text-black/45"
                >
                  {{
                    [
                      item.variant_name,
                      ...(item.options || []).map((option) => option.name),
                    ]
                      .filter(Boolean)
                      .join(" · ")
                  }}
                </p>
              </div>
              <strong class="shrink-0 tabular-nums">{{
                money(item.line_total)
              }}</strong>
            </article>
          </div>
          <div class="border-t border-black/10 bg-white px-6 py-6 sm:px-8">
            <dl class="space-y-2 text-sm">
              <div class="flex justify-between">
                <dt class="text-black/55">Subtotal</dt>
                <dd class="font-semibold tabular-nums">
                  {{ money(cart.subtotal) }}
                </dd>
              </div>
              <div
                v-if="Number(cart.discount_total)"
                class="flex justify-between text-emerald-700"
              >
                <dt>Promotion</dt>
                <dd class="font-semibold tabular-nums">
                  −{{ money(cart.discount_total) }}
                </dd>
              </div>
              <div class="flex justify-between pt-2 text-3xl font-extrabold">
                <dt>Total</dt>
                <dd class="tabular-nums">{{ money(cart.grand_total) }}</dd>
              </div>
            </dl>
          </div>
        </div>

        <div v-else class="grid flex-1 place-items-center p-8 text-center">
          <div>
            <ShoppingBag
              class="mx-auto h-10 w-10 text-black/20"
              aria-hidden="true"
            />
            <h2 class="mt-5 text-2xl font-extrabold">
              {{
                payload?.linked
                  ? "Ready for the next order"
                  : "Waiting for a counter"
              }}
            </h2>
            <p class="mx-auto mt-2 max-w-sm text-sm leading-6 text-black/50">
              {{
                payload?.linked
                  ? "Items, options, promotions, and the server-priced total will appear here."
                  : "Link this display to a POS station from Sell → POS setup."
              }}
            </p>
          </div>
        </div>
      </aside>
    </section>
  </main>
</template>

<script setup>
import { Check, Package, ShoppingBag } from "lucide-vue-next";

definePageMeta({ layout: "storefront" });
const config = useRuntimeConfig();
const code = ref("");
const message = ref("");
const deviceToken = ref("");
const payload = ref(null);
const pairing = ref(false);
const adIndex = ref(0);
const connectionState = ref("connecting");
let poller;
let adTimer;
const cart = computed(() => payload.value?.session?.cart);
const currentOrder = computed(() => payload.value?.session?.last_order);
const ads = computed(() => payload.value?.advertisements || []);
const activeAd = computed(() => ads.value[adIndex.value] || null);
const brandCover = computed(() =>
  payload.value?.display_preferences?.show_brand_fallback
    ? payload.value?.business?.cover_image_url
    : "",
);
const orderHeading = computed(() =>
  currentOrder.value
    ? "Receipt"
    : cart.value?.items?.length
      ? "Your order"
      : "Order preview",
);
const displayStyle = computed(() => ({
  "--display-ink":
    activeAd.value?.background ||
    payload.value?.business?.branding?.secondary_color ||
    "#102a2a",
  "--display-accent":
    payload.value?.business?.branding?.accent_color || "#f2ad45",
  "--display-paper": activeAd.value?.foreground || "#f7f3ea",
}));

onMounted(() => {
  deviceToken.value =
    localStorage.getItem("pixelcore_customer_display_token") || "";
  if (deviceToken.value) start();
});
onBeforeUnmount(stopTimers);
watch(() => payload.value?.display_preferences?.rotation_seconds, resetAdTimer);

async function start() {
  stopTimers();
  await load();
  if (deviceToken.value) poller = window.setInterval(load, 2500);
  resetAdTimer();
}
async function pair() {
  if (pairing.value || code.value.length !== 8) return;
  pairing.value = true;
  message.value = "";
  try {
    const response = await $fetch("devices/pair/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      body: { pairing_code: code.value, device_type: "customer_display" },
    });
    if (response.device.device_type !== "customer_display")
      throw new Error("This setup code belongs to another device.");
    deviceToken.value = response.device_token;
    localStorage.setItem(
      "pixelcore_customer_display_token",
      response.device_token,
    );
    await start();
  } catch (error) {
    message.value =
      error?.data?.error?.message || error.message || "Pairing failed.";
  } finally {
    pairing.value = false;
  }
}
async function load() {
  try {
    payload.value = await $fetch("public/devices/customer-display/", {
      baseURL: config.public.apiBaseUrl,
      headers: { "X-Device-Token": deviceToken.value },
    });
    connectionState.value = "connected";
    message.value = "";
    if (adIndex.value >= ads.value.length) adIndex.value = 0;
  } catch (error) {
    if (error?.response?.status === 403) {
      stopTimers();
      localStorage.removeItem("pixelcore_customer_display_token");
      deviceToken.value = "";
      payload.value = null;
      message.value = "This display was disconnected. Pair it again.";
    } else {
      connectionState.value = "reconnecting";
      message.value =
        "Connection interrupted. The last order remains visible while PixelCore reconnects.";
    }
  }
}
function resetAdTimer() {
  window.clearInterval(adTimer);
  const seconds = payload.value?.display_preferences?.rotation_seconds || 10;
  if (ads.value.length > 1)
    adTimer = window.setInterval(() => {
      adIndex.value = (adIndex.value + 1) % ads.value.length;
    }, seconds * 1000);
}
function stopTimers() {
  window.clearInterval(poller);
  window.clearInterval(adTimer);
}
function unpair() {
  stopTimers();
  localStorage.removeItem("pixelcore_customer_display_token");
  deviceToken.value = "";
  payload.value = null;
}
const money = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: payload.value?.business?.currency || "PHP",
  }).format(Number(value || 0));
</script>
