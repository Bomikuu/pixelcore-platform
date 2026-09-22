<template>
  <StatePanel v-if="loading" kind="loading" title="Loading editor" message="Retrieving products and media." />
  <StatePanel v-else-if="loadError" kind="error" title="Editor unavailable" :message="loadError"><Button variant="outline" @click="load">Try again</Button></StatePanel>
  <form v-else class="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]" @submit.prevent="submit">
    <Tabs v-model="tab" class="min-w-0">
      <TabsList class="mb-5 flex h-auto w-full justify-start overflow-x-auto p-1 [&_button>span]:inline-flex [&_button>span]:items-center"><TabsTrigger value="details"><FileText class="mr-2 h-4 w-4" />Details</TabsTrigger><TabsTrigger value="products"><Package class="mr-2 h-4 w-4" />Products <span class="ml-2 tabular-nums">{{ form.offering_public_ids.length }}</span></TabsTrigger><TabsTrigger value="hero"><GalleryHorizontalEnd class="mr-2 h-4 w-4" />Hero & carousel</TabsTrigger></TabsList>
      <TabsContent value="details" class="space-y-6">
        <section class="rounded-xl border bg-card p-5 sm:p-6"><h2 class="font-bold">Collection details</h2><p class="mt-1 text-sm text-muted-foreground">A clear name and introduction help customers understand the selection.</p><div class="mt-5 space-y-4">
          <label class="block"><span class="field-label">Name</span><Input v-model.trim="form.name" maxlength="140" required /></label>
          <label class="block"><span class="field-label">URL slug</span><Input v-model.trim="form.slug" pattern="[a-z0-9-]+" placeholder="Generated from the name" /></label>
          <label class="block"><span class="field-label">Description</span><Textarea v-model.trim="form.description" class="min-h-32" maxlength="2000" /></label>
        </div></section>
        <section class="rounded-xl border bg-card p-5 sm:p-6"><h2 class="font-bold">Collection cover</h2><p class="mb-5 mt-1 text-sm leading-6 text-muted-foreground">Used in collection listings and as the hero fallback when no product photography is available.</p><GroupImagePicker v-model="form.cover_asset_public_id" :assets="assets" :fallback="collection?.cover_url || ''" @uploaded="assets.unshift($event)" /></section>
      </TabsContent>
      <TabsContent value="products">
        <section class="overflow-hidden rounded-xl border bg-card"><div class="border-b p-5"><h2 class="font-bold">Choose products</h2><p class="mt-1 text-sm text-muted-foreground">Draft products can be prepared here and appear in the store once published.</p><div class="relative mt-4"><Search class="absolute left-3 top-3 h-4 w-4 text-muted-foreground" /><Input v-model="productSearch" type="search" class="pl-9" placeholder="Search products..." aria-label="Search collection products" /></div></div>
          <div class="max-h-[36rem] overflow-y-auto divide-y"><label v-for="product in filteredProducts" :key="product.public_id" class="flex cursor-pointer items-center gap-4 px-5 py-3 transition-colors hover:bg-muted/40"><NativeCheckbox v-model="form.offering_public_ids" :value="product.public_id" /><img v-if="productImage(product)" :src="productImage(product).url" alt="" class="h-14 w-14 rounded-md bg-muted object-cover" /><Package v-else class="h-14 w-14 rounded-md bg-muted p-4 text-muted-foreground" /><span class="min-w-0 flex-1"><strong class="block text-sm">{{ product.name }}</strong><span class="mt-1 block text-xs text-muted-foreground">{{ product.category_name || 'Uncategorized' }}</span></span><Badge variant="outline">{{ product.status }}</Badge></label></div>
          <StatePanel v-if="!filteredProducts.length" title="No matching products" message="Try another search or create products in the catalog first." />
        </section>
      </TabsContent>
      <TabsContent value="hero" class="space-y-5">
        <section class="rounded-xl border bg-card p-5 sm:p-6"><HeroSlidesEditor v-model="form.hero_settings.slides" :assets="assets" @uploaded="assets.unshift($event)" /></section>
        <section class="rounded-xl border bg-card p-5 sm:p-6"><div class="flex items-start justify-between gap-5"><div><h2 class="font-bold">Full-screen collection hero</h2><p class="mt-1 text-sm leading-6 text-muted-foreground">Available in both Default and Luxury. Turn it off for a compact introduction.</p></div><Switch v-model:checked="form.hero_settings.enabled" aria-label="Enable full-screen collection hero" /></div>
          <div v-if="form.hero_settings.enabled" class="mt-5 space-y-5 border-t pt-5">
            <label class="block"><span class="field-label">Heading</span><Input v-model.trim="form.hero_settings.heading" maxlength="180" :placeholder="form.name || 'Collection name'" /></label>
            <label class="block"><span class="field-label">Introduction</span><Textarea v-model.trim="form.hero_settings.body" maxlength="600" placeholder="A short introduction to this selection" /></label>
            <label class="flex items-center justify-between gap-4"><span><strong class="block text-sm">Auto-play slides</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">Customers can pause the carousel. Reduced motion disables auto-play.</span></span><Switch v-model:checked="form.hero_settings.autoplay" /></label>
            <fieldset v-if="!form.hero_settings.slides?.length"><legend class="font-semibold">Carousel products</legend><p class="mt-1 text-sm leading-6 text-muted-foreground">Select up to five. Leave empty to use the first products in this collection.</p><div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><label v-for="product in selectedProducts" :key="product.public_id" class="cursor-pointer overflow-hidden rounded-lg border transition-colors hover:border-primary"><div class="aspect-[4/3] bg-muted"><img v-if="productImage(product)" :src="productImage(product).url" alt="" class="h-full w-full object-cover" /></div><span class="flex items-center gap-3 p-3 text-sm"><NativeCheckbox v-model="form.hero_settings.offering_ids" :value="product.public_id" :disabled="!form.hero_settings.offering_ids.includes(product.public_id) && form.hero_settings.offering_ids.length >= 5" />{{ product.name }}</span></label></div><p v-if="!selectedProducts.length" class="mt-4 text-sm text-muted-foreground">Choose collection products in the Products tab first.</p></fieldset>
          </div>
        </section>
        <section v-if="form.hero_settings.enabled" class="overflow-hidden rounded-xl border"><div class="flex items-center justify-between bg-card px-5 py-3"><h2 class="text-sm font-bold">Hero preview</h2><span class="text-xs text-muted-foreground">First slide</span></div><div class="relative flex min-h-72 items-end bg-foreground p-6 text-white"><img v-if="previewImage" :src="previewImage" alt="" class="absolute inset-0 h-full w-full object-cover" /><div class="absolute inset-0 bg-gradient-to-t from-black/85 to-black/10" /><div class="relative max-w-lg"><h3 class="text-3xl font-semibold">{{ form.hero_settings.slides?.[0]?.heading || form.hero_settings.heading || form.name || 'Collection name' }}</h3><p class="mt-3 text-sm leading-6 text-white/85">{{ form.hero_settings.slides?.[0]?.body || form.hero_settings.body || form.description }}</p><span class="mt-5 inline-block border border-white px-4 py-2 text-sm">{{ form.hero_settings.slides?.[0]?.label || 'Shop collection' }}</span></div></div></section>
      </TabsContent>
    </Tabs>
    <aside class="space-y-4 xl:sticky xl:top-5">
      <section class="rounded-xl border bg-card p-5"><div class="flex items-center justify-between"><h2 class="font-bold">Publication</h2><Badge :variant="form.is_published ? 'secondary' : 'outline'">{{ form.is_published ? 'Published' : 'Draft' }}</Badge></div><label class="mt-5 flex items-center justify-between gap-4 text-sm"><span>Visible on storefront</span><Switch v-model:checked="form.is_published" /></label><label class="mt-5 block"><span class="field-label">Sort order</span><Input v-model.number="form.sort_order" type="number" min="0" /></label><p class="mt-5 border-t pt-4 text-sm text-muted-foreground">{{ form.offering_public_ids.length }} products selected</p><Button type="submit" class="mt-4 w-full" :disabled="saving"><Save class="mr-2 h-4 w-4" />{{ saving ? 'Saving...' : 'Save collection' }}</Button><p v-if="error" role="alert" class="mt-3 text-sm text-destructive">{{ error }}</p></section>
    </aside>
  </form>
</template>
<script setup>
import { FileText, GalleryHorizontalEnd, Package, Save, Search } from 'lucide-vue-next'
import GroupImagePicker from './GroupImagePicker.vue'
import HeroSlidesEditor from '~/components/site/HeroSlidesEditor.vue'
const props = defineProps({ collection: { type: Object, default: null } })
const emit = defineEmits(['saved'])
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const products = ref([])
const assets = ref([])
const loading = ref(true)
const loadError = ref('')
const error = ref('')
const saving = ref(false)
const tab = ref('details')
const productSearch = ref('')
const form = reactive({ name: '', slug: '', description: '', cover_asset_public_id: null, offering_public_ids: [], hero_settings: { enabled: true, heading: '', body: '', offering_ids: [], autoplay: true, slides: [] }, sort_order: 0, is_published: false })
const selectedProducts = computed(() => products.value.filter((product) => form.offering_public_ids.includes(product.public_id)))
const filteredProducts = computed(() => products.value.filter((product) => product.name.toLowerCase().includes(productSearch.value.toLowerCase())))
const previewImage = computed(() => {
  const custom = form.hero_settings.slides?.[0]
  if (custom) return assets.value.find(asset => asset.public_id === (custom.type === 'image' ? custom.asset_id : custom.poster_asset_id))?.file_url || ''
  const first = selectedProducts.value.find((product) => product.public_id === form.hero_settings.offering_ids[0]) || selectedProducts.value[0]
  return productImage(first)?.url || assets.value.find((asset) => asset.public_id === form.cover_asset_public_id)?.file_url || props.collection?.cover_url || ''
})
watch(() => props.collection, (value) => {
  if (!value) return
  Object.assign(form, { name: value.name, slug: value.slug, description: value.description, cover_asset_public_id: value.cover_asset_public_id || null, offering_public_ids: [...value.offering_public_ids], hero_settings: { enabled: true, heading: '', body: '', autoplay: true, ...(value.hero_settings || {}), offering_ids: [...(value.hero_settings?.offering_ids || [])] }, sort_order: value.sort_order, is_published: value.is_published })
}, { immediate: true })
watch(() => form.offering_public_ids, (selected) => { form.hero_settings.offering_ids = form.hero_settings.offering_ids.filter((id) => selected.includes(id)) }, { deep: true })
onMounted(load)
async function load() {
  loading.value = true; loadError.value = ''
  try {
    if (!business.activeBusiness) await business.loadBusinesses()
    const id = business.activeBusiness.public_id
    const response = await apiFetch(`businesses/${id}/assets/?page_size=100`)
    assets.value = response.results || []
    const all = []
    let page = 1
    let responsePage
    do { responsePage = await apiFetch(`businesses/${id}/offerings/?page_size=100&page=${page++}`); all.push(...(responsePage.results || [])) } while (responsePage.next)
    products.value = all
  } catch (exception) { loadError.value = exception?.data?.error?.message || 'Products and media could not be loaded.' }
  finally { loading.value = false }
}
function productImage(product) { return product?.ordered_media?.find((item) => item.role === 'cover') || product?.media?.[0] || null }
async function submit() {
  error.value = ''
  if (!form.name) { tab.value = 'details'; error.value = 'Enter a collection name.'; return }
  saving.value = true
  try {
    const path = props.collection ? `businesses/${business.activeBusiness.public_id}/collections/${props.collection.public_id}/` : `businesses/${business.activeBusiness.public_id}/collections/`
    const saved = await apiFetch(path, { method: props.collection ? 'PATCH' : 'POST', body: form })
    emit('saved', saved)
  } catch (exception) { error.value = exception?.data?.error?.message || 'The collection could not be saved. Check the fields and try again.' }
  finally { saving.value = false }
}
</script>
