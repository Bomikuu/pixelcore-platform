<script setup>
definePageMeta({ layout: 'storefront' })

const route = useRoute()

await navigateTo(
  {
    path: `/site/${route.params.slug}/account`,
    query: { tab: 'wishlist' },
  },
  { redirectCode: 301 },
)
</script>
