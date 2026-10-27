<template>
  <Dialog :open="open" @update:open="$emit('update:open', $event)">
    <DialogContent class="max-h-[90dvh] max-w-lg overflow-y-auto" @open-auto-focus="startCamera">
      <DialogHeader>
        <DialogTitle class="flex items-center gap-2"><ScanBarcode class="h-5 w-5 text-primary" aria-hidden="true" /> Scan a product</DialogTitle>
        <DialogDescription>Point the camera at a product barcode or QR code. You can also enter its barcode or SKU below.</DialogDescription>
      </DialogHeader>
      <div class="relative aspect-[4/3] overflow-hidden rounded-xl bg-foreground">
        <video ref="video" autoplay muted playsinline class="h-full w-full object-cover" aria-label="Live barcode camera preview" />
        <div v-if="phase === 'scanning'" class="pointer-events-none absolute inset-x-8 inset-y-12 rounded-xl border-2 border-white/80" aria-hidden="true" />
        <div v-if="phase !== 'scanning'" class="absolute inset-0 grid place-items-center p-6 text-center text-background">
          <div>
            <LoaderCircle v-if="phase === 'requesting'" class="mx-auto h-8 w-8 animate-spin motion-reduce:animate-none" aria-hidden="true" />
            <CameraOff v-else class="mx-auto h-8 w-8" aria-hidden="true" />
            <p class="mt-3 text-sm leading-6">{{ phase === 'requesting' ? 'Opening camera… Allow access when your browser asks.' : cameraError || 'Camera preview is paused.' }}</p>
          </div>
        </div>
      </div>
      <div class="flex items-center justify-between gap-3 text-xs text-muted-foreground" role="status" aria-live="polite">
        <span>{{ phase === 'scanning' ? 'Ready to scan · Closes after reading a code' : 'USB and Bluetooth readers also work in catalog search.' }}</span>
        <Button v-if="phase === 'error' || phase === 'paused'" variant="outline" size="sm" type="button" @click="startCamera"><RefreshCw class="h-3.5 w-3.5" aria-hidden="true" /> Retry camera</Button>
      </div>
      <form class="border-t pt-4" novalidate @submit.prevent="submitCode">
        <Label for="pos-manual-barcode">Barcode or SKU</Label>
        <div class="mt-2 flex gap-2">
          <Input id="pos-manual-barcode" v-model.trim="manualCode" maxlength="120" autocomplete="off" placeholder="Enter the code" />
          <Button type="submit" :disabled="!manualCode">Find item</Button>
        </div>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { CameraOff, LoaderCircle, RefreshCw, ScanBarcode } from "lucide-vue-next";

const props = defineProps({ open: { type: Boolean, default: false } });
const emit = defineEmits(["update:open", "scan"]);
const video = ref(null);
const manualCode = ref("");
const phase = ref("idle");
const cameraError = ref("");
let stream;
let controls;
let version = 0;

function stopCamera() {
  version += 1;
  controls?.stop();
  controls = undefined;
  stream?.getTracks().forEach((track) => track.stop());
  stream = undefined;
  if (video.value) {
    video.value.pause();
    video.value.srcObject = null;
  }
}

async function startCamera() {
  stopCamera();
  const attempt = version;
  if (!props.open) return;
  phase.value = "requesting";
  cameraError.value = "";
  try {
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      throw new Error("Camera scanning needs HTTPS or localhost. Enter a code below or use a connected reader.");
    }
    const acquired = await navigator.mediaDevices.getUserMedia({ audio: false, video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 } } });
    if (attempt !== version || !props.open) {
      acquired.getTracks().forEach((track) => track.stop());
      return;
    }
    stream = acquired;
    const { BrowserMultiFormatReader } = await import("@zxing/browser");
    if (attempt !== version || !props.open) return;
    const reader = new BrowserMultiFormatReader(undefined, { delayBetweenScanAttempts: 150, delayBetweenScanSuccess: 1000 });
    const scanning = await reader.decodeFromStream(acquired, video.value, (result, _error, activeControls) => {
      if (!result || attempt !== version || !props.open) return;
      controls = activeControls;
      finish(result.getText());
    });
    if (attempt !== version || !props.open) scanning.stop();
    else {
      controls = scanning;
      phase.value = "scanning";
    }
  } catch (error) {
    if (attempt !== version || !props.open) return;
    stopCamera();
    phase.value = "error";
    cameraError.value = error?.name === "NotAllowedError"
      ? "Camera access was denied. Allow it in your browser, or enter a code below."
      : error?.name === "NotFoundError"
        ? "No camera was found. Connect a camera, use a barcode reader, or enter a code below."
        : error?.name === "NotReadableError"
          ? "The camera is busy. Close other camera apps and try again."
          : error?.message || "The camera could not start. Enter a code below or use a connected reader.";
  }
}

function finish(code) {
  const value = String(code || "").trim().slice(0, 120);
  if (!value) return;
  stopCamera();
  emit("update:open", false);
  emit("scan", value);
}
function submitCode() { finish(manualCode.value); }
function pauseWhenHidden() {
  if (props.open && document.hidden) {
    stopCamera();
    phase.value = "paused";
  }
}
watch(() => props.open, (open) => {
  if (!open) stopCamera();
  else manualCode.value = "";
});
onMounted(() => document.addEventListener("visibilitychange", pauseWhenHidden));
onBeforeUnmount(() => {
  stopCamera();
  document.removeEventListener("visibilitychange", pauseWhenHidden);
});
</script>
