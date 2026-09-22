<template>
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="platform === 'instagram'">
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="0.8" fill="currentColor" stroke="none" />
    </template>
    <template v-else-if="platform === 'facebook'">
      <path d="M14.5 21v-8h2.8l.5-3h-3.3V8.1c0-.9.3-1.6 1.7-1.6H18V3.8c-.5-.1-1.4-.2-2.5-.2-2.6 0-4.4 1.6-4.4 4.6V10H8v3h3.1v8" />
    </template>
    <template v-else-if="platform === 'tiktok'">
      <path d="M15 4v10.1a4.6 4.6 0 1 1-4-4.6" />
      <path d="M15 4c.5 2.6 2 4.1 4.5 4.5" />
    </template>
    <template v-else-if="platform === 'x' || platform === 'twitter'">
      <path d="M5 4l14 16M19 4L5 20" />
    </template>
    <template v-else-if="platform === 'youtube'">
      <path d="M21 12c0 2.5-.3 4.2-.8 4.8-.7.8-4.1 1.2-8.2 1.2s-7.5-.4-8.2-1.2C3.3 16.2 3 14.5 3 12s.3-4.2.8-4.8C4.5 6.4 7.9 6 12 6s7.5.4 8.2 1.2c.5.6.8 2.3.8 4.8Z" />
      <path d="m10 9 5 3-5 3Z" fill="currentColor" stroke="none" />
    </template>
    <template v-else-if="platform === 'linkedin'">
      <rect x="4" y="9" width="3" height="11" />
      <circle cx="5.5" cy="5.5" r="1.5" fill="currentColor" stroke="none" />
      <path d="M11 20V9h3v1.8c.8-1.2 1.9-2.1 3.7-2.1 2.4 0 3.3 1.6 3.3 4.4V20h-3v-6.2c0-1.5-.5-2.3-1.8-2.3-1.4 0-2.2 1-2.2 2.8V20Z" />
    </template>
    <template v-else>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12h8M12 8v8" />
    </template>
  </svg>
</template>

<script setup>
defineProps({ platform: { type: String, required: true } })
</script>
