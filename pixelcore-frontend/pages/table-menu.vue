<script setup>const route = useRoute(); await navigateTo(route.query.slug ? `/site/${route.query.slug}/services` : '/', { redirectCode: 301 })</script>
<template><span class="sr-only">Redirecting to the public booking and catalog experience…</span></template>
