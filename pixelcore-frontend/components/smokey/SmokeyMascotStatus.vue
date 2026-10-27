<template>
  <div class="flex items-center gap-3" :aria-busy="presentation.busy">
    <div
      class="relative grid h-16 w-16 shrink-0 place-items-center"
      aria-hidden="true"
    >
      <MessageCircle
        v-if="mascot.mode === 'standard'"
        class="h-9 w-9 text-primary"
      />
      <img
        v-else-if="
          mascot.mode === 'custom' && asset && mascot.asset_type !== 'sprite'
        "
        :src="asset"
        alt=""
        class="max-h-16 max-w-16 object-contain"
      />
      <div
        v-else
        class="smokey-pose h-16 w-12 bg-no-repeat"
        :class="{ 'smokey-busy': presentation.busy }"
        :style="spriteStyle"
      />
      <span
        v-if="presentation.busy"
        class="absolute bottom-0 right-0 h-2 w-2 rounded-full bg-primary"
      />
    </div>
    <p
      class="text-sm leading-6 text-muted-foreground"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      {{ label || presentation.label }}
    </p>
  </div>
</template>
<script setup>
import { MessageCircle } from "lucide-vue-next";
import { mascotPresentation } from "~/utils/smokeyAssistant";
const props = defineProps({
  state: { type: String, default: "idle" },
  kind: { type: String, default: "daily" },
  hasPlan: { type: Boolean, default: true },
  label: { type: String, default: "" },
});
const { config, asset } = useSmokeyAssistant();
const mascot = computed(() => config.value?.mascot || {});
const presentation = computed(() =>
  mascotPresentation(props.state, props.kind, props.hasPlan),
);
const spriteStyle = computed(() => {
  const custom =
    mascot.value.mode === "custom" &&
    asset.value &&
    mascot.value.asset_type === "sprite";
  const columns = custom ? mascot.value.columns || 1 : 4,
    rows = custom ? mascot.value.rows || 1 : 2;
  const frame = custom
    ? mascot.value.frames?.[presentation.value.state] ||
      mascot.value.frames?.idle || [0, 0]
    : presentation.value.state === "generating"
      ? [3, 0]
      : [0, 0];
  return {
    backgroundImage: `url(${custom ? asset.value : "/smokey/office-cat-sprite.webp"})`,
    backgroundSize: `${columns * 100}% ${rows * 100}%`,
    backgroundPosition: `${columns > 1 ? (frame[0] * 100) / (columns - 1) : 0}% ${rows > 1 ? (frame[1] * 100) / (rows - 1) : 0}%`,
  };
});
</script>
<style scoped>
.smokey-pose {
  image-rendering: pixelated;
}
.smokey-busy {
  animation: smokey-think 1.8s ease-in-out infinite;
}
@keyframes smokey-think {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .smokey-busy {
    animation: none;
  }
}
</style>
