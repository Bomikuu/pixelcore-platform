<template>
  <StatePanel
    v-if="identityPending"
    kind="loading"
    title="Loading delivery tracking"
    message="Preparing this business's tracking page."
  />
  <StatePanel
    v-else-if="identityError || !identity"
    kind="error"
    title="Business unavailable"
    message="This tracking page could not be loaded."
  />
  <StorefrontFrame
    v-else
    :identity="identity"
    :navigation="navigation"
    :base="base"
  >
    <div class="mx-auto max-w-4xl space-y-5">
      <PageHeader
        title="Track your delivery"
        description="Follow your order from preparation to your door."
      />
      <DeliveryRefresh
        :busy="busy"
        :paused="paused"
        :last-updated="lastUpdated"
        :terminal="Boolean(data?.delivery?.terminal)"
        @refresh="refresh"
      />
      <Alert v-if="error" variant="destructive"
        ><AlertTitle>{{
          data ? "Delivery update delayed" : "Delivery tracking unavailable"
        }}</AlertTitle
        ><AlertDescription>{{
          data
            ? "We could not refresh this delivery. The previous details are shown below."
            : "Sign in with the account that placed this order, or open this link on the device used at checkout."
        }}</AlertDescription></Alert
      >
      <ButtonLink
        class="gap-2"
        v-if="error && !auth.isAuthenticated && !data"
        variant="outline"
        :to="`/login?next=${encodeURIComponent(route.fullPath)}`"
        >Sign in to track order</ButtonLink
      >
      <StatePanel
        v-if="busy && !data"
        kind="loading"
        title="Finding your delivery"
        message="Checking your order and latest tracking details."
      />
      <template v-if="data?.delivery"
        ><DeliveryMap
          :deliveries="[data.delivery]"
          :selected-id="data.delivery.public_id"
        /><DeliveryDetail :delivery="data.delivery" />
        <p class="text-xs leading-5 text-muted-foreground">
          The map shows the last position shared by your rider, rather than a
          predicted arrival time. GPS updates refresh every 30 seconds while the
          page is active.
        </p></template
      >
      <NuxtLink
        :to="`${base}/account?tab=orders`"
        class="inline-flex items-center gap-2 text-sm font-semibold underline underline-offset-4"
        ><ArrowLeft class="h-4 w-4" aria-hidden="true" /> Back to my
        orders</NuxtLink
      >
    </div>
  </StorefrontFrame>
</template>
<script setup>
import { ArrowLeft } from "lucide-vue-next";
import DeliveryMap from "~/components/deliveries/DeliveryMap.vue";
import DeliveryDetail from "~/components/deliveries/DeliveryDetail.vue";
import DeliveryRefresh from "~/components/deliveries/DeliveryRefresh.vue";
definePageMeta({ layout: "storefront" });
useHead({ title: "Track your delivery · PixelCore" });
const route = useRoute(),
  auth = useAuthStore(),
  cart = useCartStore();
cart.hydrate(route.params.slug);
const {
  identity,
  navigation,
  pending: identityPending,
  error: identityError,
  siteBase: base,
} = useStorefrontContext(route.params.slug);
const { apiFetch } = useApiClient();
const endpoint = computed(
  () => `public/${route.params.slug}/orders/${route.params.orderId}/tracking/`,
);
const { data, busy, error, lastUpdated, paused, refresh } = useDeliveryResource(
  endpoint,
  {
    terminal: (value) => Boolean(value?.delivery?.terminal),
    fetcher: (path, options) =>
      apiFetch(path, {
        ...options,
        headers: {
          "X-Cart-Token":
            cart.orderAccessToken(route.params.slug, route.params.orderId) ||
            "",
        },
      }),
  },
);
</script>
