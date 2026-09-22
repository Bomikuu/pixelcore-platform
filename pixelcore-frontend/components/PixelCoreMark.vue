<template>
  <span class="inline-flex items-center gap-3">
    <img src="/pixelcore-mark.svg" alt="" class="h-9 w-9" />
    <span v-if="showName" class="text-base font-bold tracking-tight">PixelCore</span>
  </span>
</template>

<script setup>
defineProps({
  showName: { type: Boolean, default: true },
})
</script>
