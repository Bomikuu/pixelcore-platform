<template>
  <section class="workspace-page space-y-5">
    <PageHeader :title="editing ? (selectedCategory?.name || 'New category') : 'Categories'" :description="editing ? 'Manage category details, photography, and storefront visibility.' : 'Organize your catalog and choose the categories customers discover in the shop header.'">
      <template #actions><ButtonLink v-if="editing" :to="{ path: '/workspace/sell/categories', query: { ...route.query, edit: undefined } }" variant="outline"><ArrowLeft class="mr-2 h-4 w-4" />Back to categories</ButtonLink><template v-else><Button variant="outline" @click="layoutOpen = true"><PanelTop class="mr-2 h-4 w-4" />Header layout</Button><ButtonLink :to="{ query: { ...route.query, edit: 'new' } }"><Plus class="mr-2 h-4 w-4" />New category</ButtonLink></template></template>
    </PageHeader>
    <StatePanel v-if="loading" kind="loading" title="Loading categories" message="Retrieving categories and media." />
    <StatePanel v-else-if="error" kind="error" title="Categories unavailable" :message="error"><Button variant="outline" @click="load">Try again</Button></StatePanel>
    <StatePanel v-else-if="editing && route.query.edit !== 'new' && !selectedCategory" kind="error" title="Category unavailable" message="Return to the category list and choose an existing category." />
    <CategoryEditor v-else-if="editing" :key="String(route.query.edit)" :category="selectedCategory" :assets="assets" @uploaded="assets.unshift($event)" @saved="saved" />
    <template v-else>
      <div class="flex flex-wrap gap-x-8 gap-y-3 border-y py-4 text-sm"><span class="inline-flex items-center gap-2"><Shapes class="h-4 w-4 text-muted-foreground" /><strong class="tabular-nums">{{ categories.length }}</strong> categories</span><span class="inline-flex items-center gap-2"><Eye class="h-4 w-4 text-muted-foreground" /><strong class="tabular-nums">{{ categories.filter(item => item.is_active && item.show_in_header).length }}</strong> in the header</span><span class="inline-flex items-center gap-2"><GalleryHorizontalEnd class="h-4 w-4 text-muted-foreground" />{{ savedLayout === 'carousel' ? 'Carousel navigation' : 'Grid navigation' }}</span></div>
      <CatalogGroupList kind="categories" :items="categories" :slug="business.activeBusiness?.slug" />
    </template>
    <Dialog v-model:open="layoutOpen"><DialogContent class="sm:max-w-xl"><DialogHeader><DialogTitle>Shop header layout</DialogTitle><DialogDescription>Choose how your categories appear when customers open the shop menu.</DialogDescription></DialogHeader><div class="grid gap-3 sm:grid-cols-2"><Button v-for="option in layouts" :key="option.value" type="button" variant="outline" class="h-auto min-h-36 whitespace-normal p-5 text-left" :class="layout === option.value ? 'border-primary bg-primary/5' : ''" :aria-pressed="layout === option.value" @click="layout = option.value"><span><component :is="option.icon" class="mb-4 h-5 w-5" /><strong class="block">{{ option.label }}</strong><span class="mt-2 block text-xs leading-5 text-muted-foreground">{{ option.description }}</span></span></Button></div><DialogFooter><Button variant="outline" @click="layoutOpen = false">Cancel</Button><Button :disabled="savingLayout" @click="saveLayout">{{ savingLayout ? 'Saving...' : 'Save layout' }}</Button></DialogFooter></DialogContent></Dialog>
  </section>
</template>
<script setup>
import { ArrowLeft, Eye, GalleryHorizontalEnd, Grid2X2, PanelTop, Plus, Shapes } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'
import CategoryEditor from '~/components/storefront/CategoryEditor.vue'
import CatalogGroupList from '~/components/storefront/CatalogGroupList.vue'
const route = useRoute()
const router = useRouter()
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const categories = ref([])
const assets = ref([])
const loading = ref(true)
const error = ref('')
const layoutOpen = ref(false)
const savingLayout = ref(false)
const layout = ref('grid')
const savedLayout = ref('grid')
const editing = computed(() => Boolean(route.query.edit))
const selectedCategory = computed(() => categories.value.find((item) => item.public_id === route.query.edit) || null)
const layouts = [
  { value: 'grid', label: 'Category grid', description: 'Show the selection together with large category images.', icon: Grid2X2 },
  { value: 'carousel', label: 'Category carousel', description: 'Let customers scroll horizontally through a larger selection.', icon: GalleryHorizontalEnd },
]
watch(layoutOpen, (open) => { if (open) layout.value = savedLayout.value })
onMounted(load)
async function load() {
  loading.value = true; error.value = ''
  try {
    if (!business.activeBusiness) await business.loadBusinesses()
    const id = business.activeBusiness.public_id
    const [categoryResponse, assetResponse] = await Promise.all([apiFetch(`businesses/${id}/categories/?page_size=100`), apiFetch(`businesses/${id}/assets/?page_size=100`)])
    categories.value = categoryResponse.results || []; assets.value = assetResponse.results || []
    savedLayout.value = business.activeBusiness.branding?.storefront?.header?.category_layout || 'grid'
    layout.value = savedLayout.value
  } catch (exception) { error.value = exception?.data?.error?.message || 'Category settings could not be loaded.' }
  finally { loading.value = false }
}
async function saved(value) {
  const index = categories.value.findIndex((item) => item.public_id === value.public_id)
  if (index >= 0) categories.value[index] = value
  else categories.value.unshift(value)
  toast({ title: 'Category saved', description: `${value.name} has been updated.` })
  await router.replace({ query: { ...route.query, edit: value.public_id } })
}
async function saveLayout() {
  savingLayout.value = true
  try {
    const branding = JSON.parse(JSON.stringify(business.activeBusiness.branding || {}))
    branding.storefront ||= {}
    branding.storefront.header = { ...(branding.storefront.header || {}), category_layout: layout.value }
    await business.updateIdentity({ branding })
    savedLayout.value = layout.value; layoutOpen.value = false
    toast({ title: 'Header layout saved', description: 'The storefront menu now uses your chosen layout.' })
  } catch (exception) { toast({ title: 'Header update failed', description: exception?.data?.error?.message || 'Try again.', variant: 'destructive' }) }
  finally { savingLayout.value = false }
}
</script>
