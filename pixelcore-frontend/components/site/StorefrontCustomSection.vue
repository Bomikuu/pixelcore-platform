<template><section v-if="advanced.custom_html" class="mx-auto max-w-[var(--content-max-width)] px-4 py-8 sm:px-6 lg:px-10"><SandboxedCustomization :html="advanced.custom_html" :css="advanced.custom_css" title="Additional business content" height-class="h-64" /></section></template>
<script setup>
import SandboxedCustomization from '@/components/business/SandboxedCustomization.vue'
const props = defineProps({ identity: { type: Object, required: true } })
const advanced = computed(() => props.identity.branding?.advanced || {})
</script>
