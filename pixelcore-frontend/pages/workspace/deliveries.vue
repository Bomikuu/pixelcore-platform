<template>
  <section class="workspace-page space-y-5">
    <PageHeader
      title="Deliveries"
      description="Assign riders, follow deliveries, and keep every handoff in view."
    >
      <template #actions
        ><RiderManager
          v-if="businessId && permitted"
          :key="businessId"
          :business-id="businessId"
          :riders="data?.riders || []"
          @changed="refresh"
        /><ButtonLink class="gap-2" variant="outline" to="/rider/deliveries"
          ><Bike class="h-4 w-4" aria-hidden="true" /> Rider portal</ButtonLink
        ></template
      >
    </PageHeader>
    <StatePanel
      v-if="!permitted"
      title="Delivery management is restricted"
      message="An owner, administrator, or manager can open the delivery desk."
    />
    <template v-else>
      <div
        class="flex flex-wrap items-center justify-between gap-3 border-y py-3"
      >
        <div class="flex flex-wrap gap-2" aria-label="Delivery status filters">
          <Button
            class="gap-2"
            v-for="filter in filters"
            :key="filter.value"
            type="button"
            size="sm"
            :variant="stage === filter.value ? 'default' : 'ghost'"
            :aria-pressed="stage === filter.value"
            @click="filterStage(filter.value)"
            >{{ filter.label
            }}<span
              v-if="
                data?.summary &&
                filter.value !== 'active' &&
                filter.value !== 'all'
              "
              class="tabular-nums"
              >{{ data.summary[filter.value] || 0 }}</span
            ></Button
          >
        </div>
        <DeliveryRefresh
          :busy="busy"
          :paused="paused"
          :last-updated="lastUpdated"
          @refresh="refresh"
        />
      </div>
      <Alert v-if="error" variant="destructive"
        ><AlertTitle>Delivery updates unavailable</AlertTitle
        ><AlertDescription
          >{{ error }} Previous details may be out of date.</AlertDescription
        ></Alert
      >
      <p v-if="mutationError" role="alert" class="text-sm text-destructive">
        {{ mutationError }}
      </p>
      <p v-if="notice" role="status" class="text-sm text-primary">
        {{ notice }}
      </p>
      <StatePanel
        v-if="busy && !data"
        kind="loading"
        title="Loading deliveries"
        message="Retrieving delivery orders and rider assignments."
      />
      <StatePanel
        v-else-if="data && !data.results.length"
        title="No deliveries in this view"
        message="Delivery orders appear automatically when they are placed. Try another status to see earlier deliveries."
        ><Button
          class="gap-2"
          v-if="page > 1"
          variant="outline"
          @click="goPage(page - 1)"
          >Previous page</Button
        ></StatePanel
      >
      <div
        v-else-if="data?.results.length"
        class="grid items-start gap-5 xl:grid-cols-[20rem_minmax(0,1fr)]"
      >
        <section
          class="overflow-hidden rounded-xl border bg-card"
          aria-label="Delivery orders"
        >
          <div
            class="flex items-center justify-between gap-3 border-b px-4 py-3"
          >
            <h2 class="text-sm font-bold">
              {{ data.count }}
              {{ data.count === 1 ? "delivery" : "deliveries" }}
            </h2>
            <span class="text-xs text-muted-foreground">Page {{ page }}</span>
          </div>
          <div class="max-h-[38rem] overflow-y-auto divide-y">
            <Button
              v-for="delivery in data.results"
              :key="delivery.public_id"
              type="button"
              variant="ghost"
              class="gap-2 h-auto w-full justify-start rounded-none px-4 py-4 text-left whitespace-normal"
              :class="
                selected?.public_id === delivery.public_id
                  ? 'bg-primary/10'
                  : ''
              "
              :aria-pressed="selected?.public_id === delivery.public_id"
              @click="selectDelivery(delivery.public_id)"
            >
              <span class="w-full min-w-0"
                ><span class="flex items-center justify-between gap-2"
                  ><strong>{{ delivery.order_number }}</strong
                  ><Badge variant="secondary" class="text-[10px]">{{
                    deliveryStages[delivery.stage]
                  }}</Badge></span
                ><span class="mt-2 block text-sm font-normal">{{
                  delivery.customer_name
                }}</span
                ><span
                  class="mt-1 block text-xs font-normal leading-5 text-muted-foreground"
                  >{{ delivery.address || "Address not supplied" }}</span
                ><span
                  class="mt-3 flex items-center gap-2 text-xs text-muted-foreground"
                  ><Bike class="h-3.5 w-3.5 shrink-0" aria-hidden="true" />{{
                    delivery.rider?.display_name || "Unassigned"
                  }}</span
                ></span
              >
            </Button>
          </div>
          <div
            v-if="data.next || data.previous"
            class="flex justify-between gap-2 border-t p-3"
          >
            <Button
              class="gap-2"
              type="button"
              size="sm"
              variant="outline"
              :disabled="!data.previous || busy"
              @click="goPage(page - 1)"
              >Previous</Button
            ><Button
              class="gap-2"
              type="button"
              size="sm"
              variant="outline"
              :disabled="!data.next || busy"
              @click="goPage(page + 1)"
              >Next</Button
            >
          </div>
        </section>
        <div v-if="selected" class="min-w-0 space-y-5">
          <DeliveryMap
            :deliveries="data.results"
            :selected-id="selected.public_id"
          />
          <DeliveryDetail :delivery="selected">
            <div v-if="!selected.terminal" class="mt-5 space-y-5">
              <div class="flex flex-wrap items-end gap-3">
                <div class="min-w-0 flex-1">
                  <Label for="delivery-rider">Assigned rider</Label
                  ><Select v-model="riderId" :disabled="mutating"
                    ><SelectTrigger id="delivery-rider" class="mt-2"
                      ><SelectValue
                        placeholder="Choose a rider" /></SelectTrigger
                    ><SelectContent
                      ><SelectItem value="unassigned">Unassigned</SelectItem
                      ><SelectItem
                        v-for="rider in activeRiders"
                        :key="rider.public_id"
                        :value="rider.public_id"
                        >{{ rider.display_name }} · {{ rider.kind }}</SelectItem
                      ></SelectContent
                    ></Select
                  >
                </div>
                <Button
                  class="gap-2"
                  type="button"
                  variant="outline"
                  :disabled="
                    mutating ||
                    riderId === (selected.rider?.public_id || 'unassigned')
                  "
                  @click="requestAssignment"
                  >Save rider</Button
                >
              </div>
              <div class="flex flex-wrap gap-2">
                <Button
                  class="gap-2"
                  v-if="selected.stage === 'preparing'"
                  type="button"
                  :disabled="mutating"
                  @click="mutate({ action: 'stage', stage: 'ready' })"
                  >Mark ready for pickup</Button
                ><Button
                  class="gap-2"
                  v-if="selected.stage === 'ready'"
                  type="button"
                  :disabled="mutating || !selected.rider?.available"
                  @click="
                    mutate({ action: 'stage', stage: 'out_for_delivery' })
                  "
                  >Start delivery</Button
                ><Button
                  class="gap-2"
                  v-if="selected.stage === 'out_for_delivery'"
                  type="button"
                  :disabled="mutating"
                  @click="confirmAction = 'delivered'"
                  >Mark delivered</Button
                ><Button
                  type="button"
                  variant="ghost"
                  class="gap-2 text-destructive"
                  :disabled="mutating"
                  @click="confirmAction = 'cancelled'"
                  >Cancel delivery</Button
                >
              </div>
              <div class="border-t pt-4">
                <Button
                  class="gap-2"
                  type="button"
                  variant="ghost"
                  size="sm"
                  :aria-expanded="pinOpen"
                  @click="pinOpen = !pinOpen"
                  ><MapPin class="h-4 w-4" aria-hidden="true" />{{
                    selected.destination
                      ? "Update destination pin"
                      : "Set destination pin"
                  }}</Button
                >
                <div v-if="pinOpen" class="mt-3">
                  <Label for="delivery-destination"
                    >Find the drop-off address</Label
                  ><MapboxAddressPicker
                    :key="selected.public_id"
                    id="delivery-destination"
                    v-model="destinationQuery"
                    class="mt-2"
                    :latitude="selected.destination?.latitude"
                    :longitude="selected.destination?.longitude"
                    @selected="saveDestination"
                  />
                  <p class="mt-2 text-xs leading-5 text-muted-foreground">
                    Choose a result to save the map pin. The customer's written
                    address stays visible above.
                  </p>
                </div>
              </div>
            </div>
          </DeliveryDetail>
        </div>
      </div>
    </template>
    <Dialog
      :open="Boolean(confirmAction)"
      @update:open="!$event && (confirmAction = '')"
      ><DialogContent :style="style"
        ><DialogHeader
          ><DialogTitle>{{
            confirmAction === "assign"
              ? "Change the delivery rider?"
              : confirmAction === "cancelled"
                ? "Cancel this delivery?"
                : "Confirm delivery completed?"
          }}</DialogTitle
          ><DialogDescription
            >Order {{ confirmation?.row?.order_number }}.
            {{
              confirmAction === "assign"
                ? "The previous rider will lose access and GPS sharing will stop. The delivery returns to ready for pickup."
                : confirmAction === "cancelled"
                  ? "This cancels the order, releases reserved stock, and stops location sharing. Payment refunds remain a separate action."
                  : "Confirm the customer has received the order. This completes fulfillment, commits inventory, and ends GPS sharing."
            }}</DialogDescription
          ></DialogHeader
        >
        <p v-if="mutationError" role="alert" class="text-sm text-destructive">
          {{ mutationError }}
        </p>
        <DialogFooter
          ><Button
            class="gap-2"
            type="button"
            variant="outline"
            :disabled="mutating"
            @click="confirmAction = ''"
            >Go back</Button
          ><Button
            class="gap-2"
            type="button"
            :variant="confirmAction === 'cancelled' ? 'destructive' : 'default'"
            :disabled="mutating"
            @click="confirmMutation"
            >{{ mutating ? "Saving…" : "Confirm" }}</Button
          ></DialogFooter
        ></DialogContent
      ></Dialog
    >
  </section>
</template>
<script setup>
import { Bike, MapPin } from "lucide-vue-next";
import DeliveryMap from "~/components/deliveries/DeliveryMap.vue";
import DeliveryDetail from "~/components/deliveries/DeliveryDetail.vue";
import DeliveryRefresh from "~/components/deliveries/DeliveryRefresh.vue";
import RiderManager from "~/components/deliveries/RiderManager.vue";
import MapboxAddressPicker from "~/components/scheduling/MapboxAddressPicker.vue";
import { deliveryError, deliveryStages } from "~/utils/deliveryTracking";
useHead({ title: "Deliveries · PixelCore" });
const business = useBusinessStore(),
  auth = useAuthStore(),
  route = useRoute(),
  router = useRouter();
const { apiFetch } = useApiClient();
const { style } = useWorkspaceTheme();
const businessId = computed(() => business.activeBusiness?.public_id || "");
const permitted = computed(() =>
  ["owner", "admin", "manager"].includes(
    auth.user?.businesses?.find((m) => m.public_id === businessId.value)?.role,
  ),
);
const stage = computed(() =>
  ["active", "all", ...Object.keys(deliveryStages)].includes(route.query.stage)
    ? route.query.stage
    : "active",
);
const page = computed(() =>
  Math.max(1, Math.floor(Number(route.query.page)) || 1),
);
const endpoint = computed(() =>
  businessId.value && permitted.value
    ? `businesses/${businessId.value}/deliveries/?stage=${stage.value}&page=${page.value}`
    : null,
);
const { data, busy, error, lastUpdated, paused, refresh } =
  useDeliveryResource(endpoint);
const filters = [
  { value: "active", label: "Active" },
  ...Object.entries(deliveryStages).map(([value, label]) => ({ value, label })),
  { value: "all", label: "All" },
];
const selected = computed(
  () =>
    data.value?.results.find((d) => d.public_id === route.query.delivery) ||
    data.value?.results[0],
);
const activeRiders = computed(
  () => data.value?.riders.filter((r) => r.available) || [],
);
const riderId = ref("unassigned"),
  mutating = ref(false),
  mutationError = ref(""),
  notice = ref(""),
  confirmation = ref(null),
  pinOpen = ref(false),
  destinationQuery = ref("");
const confirmAction = computed({
  get: () => confirmation.value?.action || "",
  set: (action) => {
    confirmation.value = action
      ? {
          action,
          businessId: businessId.value,
          row: selected.value,
          riderId: riderId.value,
        }
      : null;
  },
});
watch(
  () => [selected.value?.public_id, selected.value?.rider?.public_id].join(":"),
  () => {
    riderId.value = selected.value?.rider?.public_id || "unassigned";
    pinOpen.value = false;
    destinationQuery.value = selected.value?.address || "";
  },
);
watch(businessId, () => {
  confirmAction.value = "";
  notice.value = mutationError.value = "";
});
function filterStage(value) {
  router.replace({
    query: {
      ...route.query,
      stage: value,
      page: undefined,
      delivery: undefined,
    },
  });
}
function goPage(value) {
  router.replace({
    query: { ...route.query, page: value, delivery: undefined },
  });
}
function selectDelivery(id) {
  router.replace({ query: { ...route.query, delivery: id } });
}
async function mutate(body, row = selected.value, id = businessId.value) {
  if (mutating.value || !row) return;
  mutating.value = true;
  mutationError.value = notice.value = "";
  try {
    await apiFetch(`businesses/${id}/deliveries/${row.public_id}/`, {
      method: "PATCH",
      body: { ...body, revision: row.revision },
    });
    if (businessId.value !== id) return;
    confirmAction.value = "";
    notice.value = "Delivery updated.";
    await refresh();
  } catch (failure) {
    if (businessId.value === id) {
      mutationError.value = deliveryError(failure);
      if ((failure?.statusCode || failure?.response?.status) === 409)
        await refresh();
    }
  } finally {
    mutating.value = false;
  }
}
function requestAssignment() {
  if (selected.value?.stage === "out_for_delivery")
    confirmAction.value = "assign";
  else
    void mutate({
      action: "assign",
      rider_id: riderId.value === "unassigned" ? null : riderId.value,
    });
}
function confirmMutation() {
  const captured = confirmation.value;
  if (!captured) return;
  void mutate(
    captured.action === "assign"
      ? {
          action: "assign",
          rider_id: captured.riderId === "unassigned" ? null : captured.riderId,
        }
      : { action: "stage", stage: captured.action },
    captured.row,
    captured.businessId,
  );
}
function saveDestination(point) {
  void mutate({
    action: "destination",
    latitude: point.latitude,
    longitude: point.longitude,
  });
}
</script>
