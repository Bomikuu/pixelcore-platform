<template>
  <section
    class="relative isolate overflow-hidden rounded-xl border bg-muted/35"
    aria-label="Delivery map"
  >
    <div
      ref="container"
      :class="!token || failure ? 'h-48 sm:h-52' : 'h-[21rem] sm:h-[27rem]'"
      class="w-full"
    />
    <div
      v-if="message"
      class="absolute inset-0 grid place-items-center bg-muted/80 p-6 text-center"
    >
      <div class="max-w-xs">
        <MapPinned
          class="mx-auto h-9 w-9 text-muted-foreground"
          aria-hidden="true"
        />
        <p class="mt-3 font-semibold">{{ message.title }}</p>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">
          {{ message.detail }}
        </p>
      </div>
    </div>
    <div
      v-if="mapReady"
      class="absolute bottom-8 left-3 right-3 flex items-center justify-between gap-2"
    >
      <span
        class="rounded-md border bg-background px-3 py-2 text-xs text-muted-foreground"
        >Teal: rider · Amber: destination</span
      >
      <Button
        class="gap-2"
        variant="outline"
        size="sm"
        type="button"
        @click="recenter"
      >
        <LocateFixed class="h-4 w-4" aria-hidden="true" /> Fit map
      </Button>
    </div>
  </section>
</template>

<script setup>
import { LocateFixed, MapPinned } from "lucide-vue-next";
import { Button } from "~/components/ui/button";
import {
  pointCoordinates,
  syncDeliveryMarkers,
} from "~/utils/deliveryTracking";

const props = defineProps({
  deliveries: { type: Array, default: () => [] },
  selectedId: { type: String, default: "" },
});
const container = ref(null);
const mapReady = ref(false);
const failure = ref("");
const token = useRuntimeConfig().public.mapboxAccessToken;
const points = computed(() =>
  props.deliveries.flatMap((delivery) => {
    const result = [];
    const rider = pointCoordinates(delivery.location);
    const destination = pointCoordinates(delivery.destination);
    if (rider)
      result.push({
        key: `${delivery.public_id}:rider`,
        coordinates: rider,
        label: `${delivery.order_number} · ${delivery.rider?.display_name || "Rider"}`,
        color: "#18766c",
      });
    if (
      destination &&
      (!props.selectedId || delivery.public_id === props.selectedId)
    )
      result.push({
        key: `${delivery.public_id}:destination`,
        coordinates: destination,
        label: `${delivery.order_number} · Destination`,
        color: "#a66813",
      });
    return result;
  }),
);
const message = computed(() =>
  !token
    ? {
        title: "Live map unavailable",
        detail:
          "You can still follow the delivery status, address, and timeline below.",
      }
    : failure.value
      ? {
          title: "The map could not load",
          detail:
            "Delivery details remain available. Refresh the page to retry the map.",
        }
      : !points.value.length
        ? {
            title: "Waiting for a location",
            detail:
              "The map appears when a destination pin is saved or the rider shares a GPS position.",
          }
        : !mapReady.value
          ? {
              title: "Loading the delivery map",
              detail: "Preparing the latest available positions.",
            }
          : null,
);
let map;
let mapbox;
let observer;
let initializing = false;
let disposed = false;
const markers = new Map();

function recenter() {
  if (!map || !points.value.length) return;
  const bounds = new mapbox.LngLatBounds();
  for (const point of points.value) bounds.extend(point.coordinates);
  map.fitBounds(bounds, { padding: 65, maxZoom: 15, duration: 0 });
}
function updateMarkers() {
  if (!map) return;
  syncDeliveryMarkers(map, mapbox, markers, points.value);
}
async function initialize() {
  if (!token || map || initializing || disposed || !points.value.length) return;
  initializing = true;
  try {
    const [library] = await Promise.all([
      import("mapbox-gl"),
      import("mapbox-gl/dist/mapbox-gl.css"),
    ]);
    if (disposed) return;
    mapbox = library.default;
    if (!mapbox.supported()) throw new Error("WebGL unavailable");
    map = new mapbox.Map({
      container: container.value,
      accessToken: token,
      style: "mapbox://styles/mapbox/streets-v12",
      center: points.value[0].coordinates,
      zoom: 13,
    });
    map.addControl(
      new mapbox.NavigationControl({ showCompass: false }),
      "top-right",
    );
    map
      .getCanvas()
      .setAttribute(
        "aria-label",
        "Delivery positions; equivalent status and address details appear below",
      );
    map.on("load", () => {
      if (!disposed) {
        mapReady.value = true;
        updateMarkers();
        recenter();
      }
    });
    map.on("error", () => {
      if (!mapReady.value) failure.value = "unavailable";
    });
    observer = new ResizeObserver(() => map?.resize());
    observer.observe(container.value);
    updateMarkers();
  } catch {
    failure.value = "unavailable";
  } finally {
    initializing = false;
  }
}
onMounted(() => {
  void initialize();
});
watch(points, () => {
  if (map) updateMarkers();
  else if (container.value) void initialize();
});
watch(
  () => props.selectedId,
  () => {
    updateMarkers();
    recenter();
  },
);
onBeforeUnmount(() => {
  disposed = true;
  observer?.disconnect();
  markers.forEach((marker) => marker.remove());
  markers.clear();
  map?.remove();
  map = null;
});
</script>
