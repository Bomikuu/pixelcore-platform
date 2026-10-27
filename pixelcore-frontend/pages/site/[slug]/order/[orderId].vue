<template>
  <StatePanel
    v-if="pending"
    kind="loading"
    title="Confirming order"
    message="Waiting for the latest payment and fulfillment status."
  /><StatePanel
    v-else-if="error || !identity || !order"
    kind="error"
    title="Order unavailable"
    message="This confirmation link is invalid or no longer available."
  /><StorefrontFrame
    v-else
    :identity="identity"
    :navigation="navigation"
    :base="base"
    ><div class="mx-auto max-w-3xl">
      <div class="border-b pb-8">
        <Badge
          :variant="order.payment_status === 'paid' ? 'default' : 'secondary'"
          >{{ paymentLabel }}</Badge
        >
        <h1 class="display-face mt-5 text-5xl font-semibold tracking-[-0.03em]">
          Order received
        </h1>
        <p class="mt-4 leading-7 text-muted-foreground">
          Order {{ order.number }} is recorded. This page updates when the
          payment provider confirms the transaction.
        </p>
      </div>
      <section class="py-8">
        <div
          v-for="item in order.items"
          :key="item.public_id"
          class="flex justify-between gap-6 border-b py-5"
        >
          <div>
            <strong>{{ item.name }}</strong>
            <p class="mt-1 text-sm text-muted-foreground">
              {{ item.sku || "Standard item" }} · Quantity {{ item.quantity }}
            </p>
          </div>
          <strong>{{ money(item.line_total) }}</strong>
        </div>
        <dl class="mt-6 space-y-3 text-sm">
          <div class="flex justify-between">
            <dt class="text-muted-foreground">Payment</dt>
            <dd class="font-bold capitalize">
              {{ order.payment_method || "Pending selection" }}
            </dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-muted-foreground">Fulfillment</dt>
            <dd class="font-bold capitalize">{{ order.fulfillment_type }}</dd>
          </div>
          <div class="flex justify-between border-t pt-4 text-lg">
            <dt class="font-bold">Total</dt>
            <dd class="font-black">{{ money(order.grand_total) }}</dd>
          </div>
        </dl>
      </section>
      <Alert
        ><CheckCircle2 class="h-4 w-4" /><AlertTitle
          >What happens next</AlertTitle
        ><AlertDescription>{{ nextStep }}</AlertDescription></Alert
      ><ButtonLink
        v-if="order.fulfillment_type === 'delivery'"
        :to="`${base}/track/${order.public_id}`"
        class="mt-6"
        >Track delivery</ButtonLink
      ><ButtonAnchor :href="`${base}/shop`" class="mt-8"
        >Continue shopping</ButtonAnchor
      >
    </div></StorefrontFrame
  >
</template>
<script setup>
import { CheckCircle2 } from "lucide-vue-next";
definePageMeta({ layout: "storefront" });
const route = useRoute();
const cart = useCartStore();
cart.hydrate(route.params.slug);
const {
  identity,
  navigation,
  pending: identityPending,
  error: identityError,
  baseURL,
  siteBase: base,
} = useStorefrontContext(route.params.slug);
const {
  data: order,
  pending: orderPending,
  error: orderError,
  refresh,
} = useAsyncData(
  `order:${route.params.orderId}`,
  () =>
    $fetch(`public/${route.params.slug}/orders/${route.params.orderId}/`, {
      baseURL,
      headers: {
        "X-Cart-Token": cart.orderAccessToken(
          route.params.slug,
          route.params.orderId,
        ),
      },
    }),
  { server: false },
);
watch(order, (value) => {
  if (value?.public_id)
    cart.rememberOrder(
      value.public_id,
      cart.orderAccessToken(route.params.slug, value.public_id),
      route.params.slug,
    );
});
const pending = computed(() => identityPending.value || orderPending.value);
const error = computed(() => identityError.value || orderError.value);
const paymentLabel = computed(() =>
  order.value?.payment_status === "paid"
    ? "Payment confirmed"
    : order.value?.payment_status === "pending"
      ? "Payment processing"
      : "Order placed",
);
const nextStep = computed(() =>
  order.value?.payment_status === "paid"
    ? "The business can now prepare fulfillment using the confirmed payment record."
    : order.value?.payment_method === "paymongo"
      ? "Keep this page open briefly while secure payment confirmation arrives."
      : "The business will provide payment or fulfillment instructions using the contact details supplied.",
);
const money = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: identity.value?.currency || "PHP",
  }).format(Number(value || 0));
if (import.meta.client) useOrderPaymentRefresh(order, refresh);
</script>
