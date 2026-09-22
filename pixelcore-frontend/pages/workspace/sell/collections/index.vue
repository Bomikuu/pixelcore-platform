<template>
  <section class="workspace-page space-y-5">
    <PageHeader title="Collections" description="Build product stories, choose their photography, and shape how customers explore your store."><template #actions><ButtonLink to="/workspace/sell/collections/new"><Plus class="mr-2 h-4 w-4" />New collection</ButtonLink></template></PageHeader>
    <StatePanel v-if="loading" kind="loading" title="Loading collections" message="Retrieving product groups." />
    <StatePanel v-else-if="error" kind="error" title="Collections unavailable" :message="error"><Button variant="outline" @click="load">Try again</Button></StatePanel>
    <template v-else>
      <div class="flex flex-wrap gap-x-8 gap-y-3 border-y py-4 text-sm">
        <span class="inline-flex items-center gap-2"><Layers3 class="h-4 w-4 text-muted-foreground" /><strong class="tabular-nums">{{ collections.length }}</strong> collections</span>
        <span class="inline-flex items-center gap-2"><Globe class="h-4 w-4 text-muted-foreground" /><strong class="tabular-nums">{{ publishedCount }}</strong> published</span>
        <span class="inline-flex items-center gap-2"><FilePenLine class="h-4 w-4 text-muted-foreground" /><strong class="tabular-nums">{{ collections.length - publishedCount }}</strong> drafts</span>
      </div>
      <CatalogGroupList :items="collections" :slug="business.activeBusiness?.slug" />
    </template>
  </section>
</template>
<script setup>
import { FilePenLine, Globe, Layers3, Plus } from 'lucide-vue-next'
import CatalogGroupList from '~/components/storefront/CatalogGroupList.vue'
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const collections = ref([])
const loading = ref(true)
const error = ref('')
const publishedCount = computed(() => collections.value.filter((item) => item.is_published).length)
onMounted(load)
async function load() {
  loading.value = true; error.value = ''
  try {
    if (!business.activeBusiness) await business.loadBusinesses()
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/collections/?page_size=100`)
    collections.value = response.results || []
  } catch (exception) { error.value = exception?.data?.error?.message || 'Collections could not be loaded.' }
  finally { loading.value = false }
}
</script>
