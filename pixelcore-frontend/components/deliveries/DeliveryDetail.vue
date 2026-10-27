<template>
  <section
    class="rounded-xl border bg-card p-5 sm:p-6"
    aria-labelledby="delivery-detail-title"
  >
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 id="delivery-detail-title" class="text-xl font-extrabold">
          Order {{ delivery.order_number }}
        </h2>
        <p class="mt-1 text-sm text-muted-foreground">
          {{ delivery.business_name }}
        </p>
      </div>
      <Badge
        :variant="delivery.stage === 'delivered' ? 'default' : 'secondary'"
        >{{ deliveryStages[delivery.stage] }}</Badge
      >
    </div>
    <dl class="mt-5 grid gap-5 text-sm sm:grid-cols-2">
      <div>
        <dt class="flex items-center gap-2 text-muted-foreground">
          <MapPin class="h-4 w-4" aria-hidden="true" /> Drop-off
        </dt>
        <dd class="mt-2 leading-6">
          {{
            delivery.address ||
            "The business has not supplied a delivery address."
          }}
        </dd>
      </div>
      <div>
        <dt class="flex items-center gap-2 text-muted-foreground">
          <Bike class="h-4 w-4" aria-hidden="true" /> Rider
        </dt>
        <dd class="mt-2 leading-6">
          {{ delivery.rider?.display_name || "Waiting for assignment"
          }}<span
            v-if="delivery.rider && !delivery.rider.available"
            class="block text-muted-foreground"
            >Rider access is inactive</span
          >
        </dd>
      </div>
      <div v-if="delivery.customer_name">
        <dt class="text-muted-foreground">Customer</dt>
        <dd class="mt-2">
          {{ delivery.customer_name
          }}<a
            v-if="
              delivery.customer_phone &&
              /^\+?[\d\s()-]+$/.test(delivery.customer_phone)
            "
            :href="`tel:${delivery.customer_phone}`"
            class="mt-1 block font-medium underline underline-offset-4"
            >{{ delivery.customer_phone }}</a
          >
        </dd>
      </div>
      <div v-if="delivery.payment_status">
        <dt class="text-muted-foreground">Payment</dt>
        <dd class="mt-2 capitalize">
          {{ delivery.payment_status.replaceAll("_", " ") }} ·
          {{ delivery.payment_method || "Not specified"
          }}<span class="mt-1 block font-semibold tabular-nums">{{
            money(delivery.total, delivery.currency)
          }}</span>
        </dd>
      </div>
    </dl>
    <div
      class="mt-5 flex items-start gap-3 border-y py-4 text-sm"
      role="status"
    >
      <Radio class="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
      <div v-if="delivery.terminal">
        <p class="font-semibold">
          {{
            delivery.stage === "delivered"
              ? "Delivery completed"
              : "Delivery cancelled"
          }}
        </p>
        <p class="mt-1 text-muted-foreground">Location sharing has ended.</p>
      </div>
      <div v-else-if="delivery.location">
        <p class="font-semibold">
          {{ stale ? "Location update delayed" : "Rider location received" }}
        </p>
        <p class="mt-1 text-muted-foreground">
          {{ dateTime(delivery.location.received_at) }} · GPS accuracy about
          {{ Math.round(delivery.location.accuracy) }} m
        </p>
        <p v-if="stale" class="mt-1 text-muted-foreground">
          This is the last known position. The rider may be offline or have
          closed the page.
        </p>
      </div>
      <div v-else>
        <p class="font-semibold">
          {{
            delivery.sharing
              ? "Waiting for a GPS position"
              : "Location is not being shared"
          }}
        </p>
        <p class="mt-1 text-muted-foreground">
          {{
            delivery.stage === "out_for_delivery"
              ? "The rider can enable GPS from their delivery portal."
              : "GPS becomes available when the delivery is on the way."
          }}
        </p>
      </div>
    </div>
    <slot />
    <div v-if="delivery.items?.length" class="mt-5">
      <h3 class="text-sm font-bold">Delivery items</h3>
      <ul class="mt-3 space-y-2 text-sm">
        <li
          v-for="(item, index) in delivery.items"
          :key="index"
          class="flex gap-3"
        >
          <span class="min-w-6 font-semibold tabular-nums"
            >{{ item.quantity }}×</span
          ><span>{{ item.name }}</span>
        </li>
      </ul>
    </div>
    <div class="mt-6">
      <h3 class="text-sm font-bold">Delivery timeline</h3>
      <ol class="mt-4 space-y-4">
        <li
          v-for="(event, index) in delivery.events"
          :key="`${event.created_at}:${index}`"
          class="flex gap-3 text-sm"
        >
          <CheckCircle2
            class="mt-0.5 h-4 w-4 shrink-0 text-primary"
            aria-hidden="true"
          />
          <div>
            <p class="font-medium">{{ event.message }}</p>
            <time
              :datetime="event.created_at"
              class="mt-1 block text-xs text-muted-foreground"
              >{{ dateTime(event.created_at) }}</time
            >
          </div>
        </li>
      </ol>
    </div>
  </section>
</template>
<script setup>
import { Bike, CheckCircle2, MapPin, Radio } from "lucide-vue-next";
import { Badge } from "~/components/ui/badge";
import { deliveryStages, locationIsStale } from "~/utils/deliveryTracking";
const props = defineProps({ delivery: { type: Object, required: true } });
const now = ref(Date.now());
let timer;
onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now();
  }, 10000);
});
onBeforeUnmount(() => clearInterval(timer));
const stale = computed(() =>
  locationIsStale(props.delivery.location, now.value),
);
const dateTime = (value) =>
  new Intl.DateTimeFormat("en-PH", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
const money = (value, currency = "PHP") =>
  new Intl.NumberFormat("en-PH", { style: "currency", currency }).format(
    Number(value || 0),
  );
</script>
