<template><PromotionEditor :key="String(route.params.promotionId)" :promotion-id="String(route.params.promotionId)" /></template>
<script setup>
import PromotionEditor from '~/components/promotions/PromotionEditor.vue'
const route = useRoute()
</script>
