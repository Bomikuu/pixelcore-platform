<template>
  <main class="min-h-dvh bg-muted/25">
    <header class="border-b bg-background">
      <div
        class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6"
      >
        <div class="flex items-center gap-3">
          <Bike class="h-7 w-7 text-primary" aria-hidden="true" />
          <div>
            <p class="font-extrabold">My deliveries</p>
            <p class="text-xs text-muted-foreground">
              {{ auth.user?.first_name || auth.user?.email }}
            </p>
          </div>
        </div>
        <nav class="flex flex-wrap gap-2" aria-label="Rider account">
          <ButtonLink
            class="gap-2"
            v-if="auth.user?.businesses?.length"
            variant="outline"
            :to="home"
            >{{
              home === "/employee" ? "Employee portal" : "Workspace"
            }}</ButtonLink
          ><Button class="gap-2" variant="ghost" type="button" @click="signOut"
            ><LogOut class="h-4 w-4" aria-hidden="true" /> Sign out</Button
          >
        </nav>
      </div>
    </header>
    <div class="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
      <PageHeader
        title="Your delivery route"
        description="Open an assigned order, collect it when ready, and share your location while on the way."
      />
      <DeliveryRefresh
        :busy="busy"
        :paused="paused"
        :last-updated="lastUpdated"
        @refresh="refresh"
      />
      <Alert v-if="error" variant="destructive"
        ><AlertTitle>Delivery updates unavailable</AlertTitle
        ><AlertDescription
          >{{ error }} Displayed details may be out of date.</AlertDescription
        ></Alert
      >
      <p v-if="actionError" role="alert" class="text-sm text-destructive">
        {{ actionError }}
      </p>
      <p v-if="notice" role="status" class="text-sm text-primary">
        {{ notice }}
      </p>
      <section
        v-if="data?.invitations.length"
        class="rounded-xl border bg-card p-5"
        aria-labelledby="invitations-title"
      >
        <h2 id="invitations-title" class="font-bold">Rider invitations</h2>
        <p class="mt-2 text-sm text-muted-foreground">
          Accept delivery-only access for these businesses. Your business
          workspace access stays separate.
        </p>
        <ul class="mt-4 divide-y">
          <li
            v-for="invite in data.invitations"
            :key="invite.public_id"
            class="flex flex-wrap items-center justify-between gap-3 py-3"
          >
            <p class="text-sm font-semibold">{{ invite.business_name }}</p>
            <Button
              class="gap-2"
              type="button"
              size="sm"
              :disabled="mutating"
              @click="accept(invite)"
              >{{ mutating ? "Saving…" : "Accept invitation" }}</Button
            >
          </li>
        </ul>
      </section>
      <StatePanel
        v-if="busy && !data"
        kind="loading"
        title="Loading assigned deliveries"
        message="Checking delivery access and active jobs."
      />
      <StatePanel
        v-else-if="data && !data.results.length"
        title="No assigned deliveries"
        message="Your active deliveries will appear here when a business assigns you. If you were invited, sign in with that verified email and accept the invitation above."
      />
      <div
        v-else-if="data?.results.length"
        class="grid items-start gap-5 lg:grid-cols-[19rem_minmax(0,1fr)]"
      >
        <section
          class="overflow-hidden rounded-xl border bg-card"
          aria-label="Assigned deliveries"
        >
          <div class="border-b p-4">
            <h2 class="font-bold">
              {{ data.results.length }} active
              {{ data.results.length === 1 ? "delivery" : "deliveries" }}
            </h2>
            <p v-if="sharing" class="mt-2 text-xs text-muted-foreground">
              Stop location sharing before switching jobs.
            </p>
          </div>
          <div class="divide-y">
            <Button
              v-for="job in data.results"
              :key="job.public_id"
              type="button"
              variant="ghost"
              class="gap-2 h-auto w-full justify-start whitespace-normal rounded-none p-4 text-left"
              :class="
                selected?.public_id === job.public_id ? 'bg-primary/10' : ''
              "
              :disabled="
                (sharing || gpsBusy) && selected?.public_id !== job.public_id
              "
              :aria-pressed="selected?.public_id === job.public_id"
              @click="selectDelivery(job.public_id)"
              ><span class="w-full"
                ><span class="flex flex-wrap items-center justify-between gap-2"
                  ><strong>{{ job.order_number }}</strong
                  ><Badge variant="secondary">{{
                    deliveryStages[job.stage]
                  }}</Badge></span
                ><span
                  class="mt-2 block text-xs font-normal text-muted-foreground"
                  >{{ job.business_name }}</span
                ><span class="mt-2 block text-sm font-normal leading-6">{{
                  job.address || "Ask the business for the drop-off address."
                }}</span></span
              ></Button
            >
          </div>
        </section>
        <div v-if="selected" class="min-w-0 space-y-5">
          <DeliveryMap
            :deliveries="[selected]"
            :selected-id="selected.public_id"
          />
          <DeliveryDetail :delivery="selected">
            <div class="mt-5 space-y-4">
              <p
                v-if="selected.stage === 'preparing'"
                class="text-sm text-muted-foreground"
              >
                The business is preparing this order. Start the delivery when it
                is marked ready for pickup.
              </p>
              <Button
                class="gap-2"
                v-if="selected.stage === 'ready'"
                type="button"
                :disabled="mutating"
                @click="changeStage('out_for_delivery')"
                ><PackageCheck class="h-4 w-4" aria-hidden="true" />{{
                  mutating ? "Saving…" : "Collected · Start delivery"
                }}</Button
              >
              <template v-if="selected.stage === 'out_for_delivery'">
                <div class="space-y-3 rounded-lg bg-muted/50 p-4">
                  <h3 class="text-sm font-bold">
                    Share GPS during this delivery
                  </h3>
                  <p class="text-xs leading-5 text-muted-foreground">
                    Your assigned business and this customer can see your
                    position. Updates send every 30 seconds while this page is
                    active. Keep your screen on; sharing stops when the delivery
                    ends.
                  </p>
                  <div class="flex flex-wrap gap-2">
                    <Button
                      class="gap-2"
                      v-if="!sharing"
                      type="button"
                      variant="outline"
                      :disabled="gpsBusy || mutating"
                      @click="startGps"
                      ><LocateFixed class="h-4 w-4" aria-hidden="true" />{{
                        gpsBusy
                          ? "Getting GPS position…"
                          : "Start sharing location"
                      }}</Button
                    ><Button
                      class="gap-2"
                      v-else
                      type="button"
                      variant="outline"
                      @click="stopGps"
                      ><Radio class="h-4 w-4" aria-hidden="true" />Stop sharing
                      location</Button
                    ><Badge v-if="sharing" variant="secondary">{{
                      paused ? "Uploads paused" : "Sharing every 30 seconds"
                    }}</Badge>
                  </div>
                  <p v-if="lastSent" class="text-xs text-muted-foreground">
                    Last sent
                    {{
                      new Intl.DateTimeFormat("en-PH", {
                        timeStyle: "short",
                      }).format(new Date(lastSent))
                    }}
                  </p>
                  <p
                    v-if="gpsError"
                    role="alert"
                    class="text-sm text-destructive"
                  >
                    {{ gpsError }}
                  </p>
                </div>
                <Button
                  class="gap-2"
                  type="button"
                  :disabled="mutating"
                  @click="confirmDelivered = true"
                  ><CheckCircle2 class="h-4 w-4" aria-hidden="true" /> Mark
                  delivered</Button
                >
              </template>
            </div>
          </DeliveryDetail>
        </div>
      </div>
    </div>
    <Dialog v-model:open="confirmDelivered"
      ><DialogContent
        ><DialogHeader
          ><DialogTitle>Has the customer received the order?</DialogTitle
          ><DialogDescription
            >This completes delivery {{ confirmationJob?.order_number }} and
            ends GPS sharing. Record any required payment through the business's
            existing payment process.</DialogDescription
          ></DialogHeader
        >
        <p v-if="actionError" role="alert" class="text-sm text-destructive">
          {{ actionError }}
        </p>
        <DialogFooter
          ><Button
            class="gap-2"
            type="button"
            variant="outline"
            :disabled="mutating"
            @click="confirmDelivered = false"
            >Go back</Button
          ><Button
            class="gap-2"
            type="button"
            :disabled="mutating"
            @click="changeStage('delivered', confirmationJob)"
            >{{ mutating ? "Saving…" : "Confirm delivered" }}</Button
          ></DialogFooter
        ></DialogContent
      ></Dialog
    >
  </main>
</template>
<script setup>
import {
  Bike,
  CheckCircle2,
  LocateFixed,
  LogOut,
  PackageCheck,
  Radio,
} from "lucide-vue-next";
import DeliveryMap from "~/components/deliveries/DeliveryMap.vue";
import DeliveryDetail from "~/components/deliveries/DeliveryDetail.vue";
import DeliveryRefresh from "~/components/deliveries/DeliveryRefresh.vue";
import { accountHome } from "~/utils/accountHome";
import { deliveryError, deliveryStages } from "~/utils/deliveryTracking";
definePageMeta({ layout: false });
useHead({ title: "My deliveries · PixelCore" });
const auth = useAuthStore(),
  route = useRoute(),
  router = useRouter();
const { apiFetch } = useApiClient();
const home = computed(() => accountHome(auth.user));
const endpoint = computed(() =>
  auth.isAuthenticated ? "rider/deliveries/" : null,
);
const { data, busy, error, lastUpdated, paused, refresh } =
  useDeliveryResource(endpoint);
const selected = computed(
  () =>
    data.value?.results.find((job) => job.public_id === route.query.delivery) ||
    data.value?.results[0],
);
const {
  sharing,
  busy: gpsBusy,
  error: gpsError,
  lastSent,
  start,
  stop,
} = useRiderLocation(selected);
const mutating = ref(false),
  actionError = ref(""),
  notice = ref(""),
  confirmationJob = ref(null);
const confirmDelivered = computed({
  get: () => Boolean(confirmationJob.value),
  set: (value) => {
    confirmationJob.value = value ? selected.value : null;
  },
});
function selectDelivery(id) {
  if (!sharing.value && !gpsBusy.value)
    router.replace({ query: { ...route.query, delivery: id } });
}
async function startGps() {
  await start();
  await refresh();
}
async function stopGps() {
  await stop();
  await refresh();
}
async function changeStage(stage, row = selected.value) {
  if (mutating.value || !row) return;
  mutating.value = true;
  actionError.value = notice.value = "";
  try {
    await apiFetch(`rider/deliveries/${row.public_id}/`, {
      method: "PATCH",
      body: { revision: row.revision, action: "stage", stage },
    });
    if (stage === "delivered") await stop();
    confirmDelivered.value = false;
    notice.value =
      stage === "delivered"
        ? `Order ${row.order_number} delivered. GPS sharing has ended.`
        : "Delivery started. You can now share your location.";
    await refresh();
  } catch (failure) {
    actionError.value = deliveryError(failure);
    if ((failure?.statusCode || failure?.response?.status) === 409)
      await refresh();
  } finally {
    mutating.value = false;
  }
}
async function accept(invite) {
  if (mutating.value) return;
  mutating.value = true;
  actionError.value = "";
  try {
    await apiFetch(`rider/access/${invite.public_id}/accept/`, {
      method: "POST",
    });
    await auth.loadUser();
    await refresh();
    notice.value = `Rider access accepted for ${invite.business_name}.`;
  } catch (failure) {
    actionError.value = deliveryError(failure);
  } finally {
    mutating.value = false;
  }
}
async function signOut() {
  await stop();
  await auth.logout();
  await navigateTo("/login");
}
</script>
