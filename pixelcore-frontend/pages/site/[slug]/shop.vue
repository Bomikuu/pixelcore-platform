<template>
  <StatePanel v-if="pending" kind="loading" title="Loading shop" message="Retrieving the published catalog." />
  <StatePanel v-else-if="error || !identity" kind="error" title="Shop unavailable" message="This business storefront could not be loaded." />
  <StorefrontFrame v-else :identity="identity" :navigation="navigation" :base="base" full-bleed>
    <MarketplaceCatalog
      v-if="isMarketplace"
      :identity="identity"
      :catalog="catalog"
      :filters="filters"
      :active-filters="activeFilters"
      :page="page"
      :base="base"
      @apply="applyMarketplaceFilters"
      @clear-filter="clearFilter"
      @clear-all="clearAll"
      @change-page="changePage"
    />
    <template v-else>
    <StorefrontFeaturedProductStage v-if="showHighlight" :product="catalog.highlighted" :base="base" :currency="identity.currency" />
    <div class="mx-auto max-w-[var(--content-max-width)] px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
    <div class="flex flex-col gap-8 border-b pb-8 md:flex-row md:items-end md:justify-between">
      <div><h1 class="display-face text-5xl font-semibold tracking-[-0.03em] sm:text-6xl">Shop</h1><p class="mt-3 max-w-2xl text-muted-foreground">Explore {{ identity.display_name }} products through real availability, options, and pricing.</p></div>
      <div class="flex items-center gap-3"><span class="text-sm font-semibold text-muted-foreground">{{ catalog?.count || 0 }} products</span><NativeSelect v-model="filters.ordering" class="w-44" aria-label="Sort products" @change="applyFilters"><option value="newest">Newest</option><option value="price_low">Price: low to high</option><option value="price_high">Price: high to low</option><option value="name">Name</option></NativeSelect></div>
    </div>
    <div class="mt-8">
      <div>
        <div v-if="activeFilters.length" class="mb-6 flex flex-wrap gap-2"><Button v-for="item in activeFilters" :key="item.key" variant="secondary" size="sm" @click="clearFilter(item.key)">{{ item.label }}<X class="ml-2 h-3.5 w-3.5" /></Button><Button variant="ghost" size="sm" @click="clearAll">Clear all</Button></div>
        <div v-if="catalog?.results?.length" class="grid gap-x-4 gap-y-10 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4"><ProductCard v-for="product in catalog.results" :key="product.public_id" :product="product" :base="base" :slug="route.params.slug" :currency="identity.currency" /></div>
        <StatePanel v-else title="No products match" message="Change or clear a filter to see more of this catalog."><Button variant="outline" @click="clearAll">Clear filters</Button></StatePanel>
        <div v-if="catalog?.next || catalog?.previous" class="mt-12 flex justify-center gap-2"><Button variant="outline" :disabled="!catalog.previous" @click="changePage(-1)">Previous</Button><span class="px-3 py-2 text-sm font-bold">Page {{ page }}</span><Button variant="outline" :disabled="!catalog.next" @click="changePage(1)">Next</Button></div>
      </div>
    </div>
    </div>

    <Sheet v-model:open="filterOpen">
      <SheetContent side="right" class="w-[min(28rem,94vw)] overflow-y-auto">
        <SheetHeader><SheetTitle>Filter products</SheetTitle><SheetDescription>Narrow the collection without leaving the catalog.</SheetDescription></SheetHeader>
        <div class="mt-8"><FilterControls /></div>
      </SheetContent>
    </Sheet>
    <Button class="fixed bottom-6 right-5 z-30 h-12 rounded-full px-5 shadow-[0_14px_40px_rgba(0,0,0,0.2)] sm:right-8" type="button" aria-label="Open product filters" @click="filterOpen = true"><SlidersHorizontal class="h-4 w-4" /> Filters <Badge v-if="activeFilters.length" variant="secondary" class="ml-1 min-w-6 justify-center rounded-full">{{ activeFilters.length }}</Badge></Button>
    </template>
  </StorefrontFrame>
</template>

<script setup>
import { SlidersHorizontal, X } from 'lucide-vue-next'
import MarketplaceCatalog from '@/components/marketplace/MarketplaceCatalog.vue'
definePageMeta({ layout: 'storefront' })
const route = useRoute()
const router = useRouter()
const filterOpen = ref(false)
const { identity, navigation, pending, error, baseURL, siteBase: base } = useStorefrontContext(route.params.slug)
const isMarketplace = computed(() => identity.value?.branding?.storefront?.layout === 'marketplace')
const filters = reactive({ search: route.query.search || '', category: route.query.category || '', collection: route.query.collection || '', availability: route.query.availability || '', price_min: route.query.price_min || '', price_max: route.query.price_max || '', ordering: route.query.ordering || 'newest' })
const page = computed(() => Number(route.query.page || 1))
const queryString = computed(() => new URLSearchParams(Object.entries({ ...route.query, page: page.value }).filter(([, value]) => value !== '' && value != null)).toString())
const { data: catalog, refresh } = useAsyncData(`commerce:${route.params.slug}`, () => $fetch(`public/${route.params.slug}/storefront/products/?${queryString.value}`, { baseURL }))
useHead(() => ({ title: `Shop | ${identity.value?.display_name || 'Storefront'}`, meta: [{ name: 'description', content: `Browse published products from ${identity.value?.display_name || 'this business'}.` }] }))
watch(() => route.fullPath, () => { Object.assign(filters, { search: route.query.search || '', category: route.query.category || '', collection: route.query.collection || '', availability: route.query.availability || '', price_min: route.query.price_min || '', price_max: route.query.price_max || '', ordering: route.query.ordering || 'newest' }); refresh() })
const activeFilters = computed(() => Object.entries(filters).filter(([key, value]) => value && key !== 'ordering').map(([key, value]) => ({ key, label: key === 'availability' ? 'In stock' : String(value) })))
const showHighlight = computed(() => Boolean(catalog.value?.highlighted && page.value === 1 && activeFilters.value.length === 0 && filters.ordering === 'newest'))
function applyFilters() { filterOpen.value = false; router.push({ query: { ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value)), page: undefined } }) }
function applyMarketplaceFilters(nextFilters) {
  Object.assign(filters, nextFilters)
  if (filters.category === 'all') filters.category = ''
  if (filters.collection === 'all') filters.collection = ''
  applyFilters()
}
function clearFilter(key) { filters[key] = ''; applyFilters() }
function clearAll() { Object.assign(filters, { search: '', category: '', collection: '', availability: '', price_min: '', price_max: '', ordering: 'newest' }); applyFilters() }
function changePage(delta) { router.push({ query: { ...route.query, page: Math.max(1, page.value + delta) } }) }

const FilterControls = defineComponent({
  setup() { return () => h('form', { class: 'space-y-7', onSubmit: (event) => { event.preventDefault(); applyFilters() } }, [
    h('div', [h('label', { class: 'field-label', for: 'catalog-search' }, 'Search'), h(resolveComponent('Input'), { id: 'catalog-search', modelValue: filters.search, 'onUpdate:modelValue': (value) => { filters.search = value }, placeholder: 'Product or brand' })]),
    h('div', [h('label', { class: 'field-label', for: 'catalog-category' }, 'Category'), h(resolveComponent('NativeSelect'), { id: 'catalog-category', modelValue: filters.category, 'onUpdate:modelValue': (value) => { filters.category = value } }, () => [h('option', { value: '' }, 'All categories'), ...(catalog.value?.facets?.categories || []).map((item) => h('option', { value: item.slug }, item.name))])]),
    h('div', [h('label', { class: 'field-label', for: 'catalog-collection' }, 'Collection'), h(resolveComponent('NativeSelect'), { id: 'catalog-collection', modelValue: filters.collection, 'onUpdate:modelValue': (value) => { filters.collection = value } }, () => [h('option', { value: '' }, 'All collections'), ...(catalog.value?.facets?.collections || []).map((item) => h('option', { value: item.slug }, item.name))])]),
    h('fieldset', [h('legend', { class: 'field-label' }, 'Price'), h('div', { class: 'grid grid-cols-2 gap-2' }, [h(resolveComponent('Input'), { modelValue: filters.price_min, 'onUpdate:modelValue': (value) => { filters.price_min = value }, type: 'number', min: 0, placeholder: 'Min', 'aria-label': 'Minimum price' }), h(resolveComponent('Input'), { modelValue: filters.price_max, 'onUpdate:modelValue': (value) => { filters.price_max = value }, type: 'number', min: 0, placeholder: 'Max', 'aria-label': 'Maximum price' })])]),
    h('label', { class: 'flex items-center gap-3 text-sm font-semibold' }, [h(resolveComponent('NativeCheckbox'), { modelValue: filters.availability === 'in_stock', 'onUpdate:modelValue': (checked) => { filters.availability = checked ? 'in_stock' : '' } }), 'In stock only']),
    h(resolveComponent('Button'), { class: 'w-full', type: 'submit' }, () => 'Apply filters'),
  ]) },
})
</script>
