<template>
  <div class="garden-botanical" :class="`garden-botanical--${placement}`" aria-hidden="true">
    <span class="garden-botanical__arc" />
    <Sprout class="garden-botanical__sprout" />
    <Flower2 class="garden-botanical__flower" />
  </div>
</template>

<script setup>
import { Flower2, Sprout } from 'lucide-vue-next'

defineProps({
  placement: {
    type: String,
    default: 'corner',
    validator: value => ['corner', 'divider', 'frame'].includes(value),
  },
})
</script>

<style scoped>
.garden-botanical {
  pointer-events: none;
  position: absolute;
  z-index: 2;
  color: var(--event-accent);
  opacity: 0.62;
}

.garden-botanical--corner {
  right: clamp(1.25rem, 4vw, 4rem);
  bottom: clamp(1.25rem, 4vw, 4rem);
  width: clamp(8rem, 20vw, 15rem);
  height: clamp(8rem, 20vw, 15rem);
}

.garden-botanical--frame {
  top: clamp(6rem, 12vh, 9rem);
  left: clamp(1.25rem, 4vw, 4rem);
  width: clamp(7rem, 18vw, 13rem);
  height: clamp(7rem, 18vw, 13rem);
  transform: scaleX(-1) rotate(-7deg);
}

.garden-botanical--divider {
  position: relative;
  width: 8rem;
  height: 4rem;
  margin: 0 auto;
}

.garden-botanical__arc {
  position: absolute;
  inset: 7% 4% 4% 8%;
  border: 1px solid currentColor;
  border-left-color: transparent;
  border-bottom-color: transparent;
  border-radius: 50%;
  transform: rotate(-22deg);
}

.garden-botanical__sprout {
  position: absolute;
  right: 8%;
  bottom: 3%;
  width: 54%;
  height: 54%;
  stroke-width: 1;
  transform: rotate(-18deg);
}

.garden-botanical__flower {
  position: absolute;
  top: 2%;
  left: 4%;
  width: 28%;
  height: 28%;
  stroke-width: 0.9;
  transform: rotate(12deg);
}

.garden-botanical--divider .garden-botanical__arc {
  inset: 35% 3% -25%;
}

.garden-botanical--divider .garden-botanical__sprout {
  right: 18%;
  bottom: -8%;
}

.garden-botanical--divider .garden-botanical__flower {
  top: 20%;
  left: 18%;
}
</style>
