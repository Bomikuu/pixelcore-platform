<template>
  <div class="mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 lg:px-8">
    <div class="flex flex-col gap-5 border-b pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <nav class="mb-3 flex items-center gap-2 text-xs text-muted-foreground" aria-label="Breadcrumb">
          <a :href="base || '/'" class="hover:text-primary">Home</a>
          <ChevronRight class="h-3 w-3" aria-hidden="true" />
          <a :href="`${base}/shop`" class="hover:text-primary">Shop</a>
          <template v-if="selectedCategory"><ChevronRight class="h-3 w-3" aria-hidden="true" /><span>{{ selectedCategory.name }}</span></template>
        </nav>
        <h1 class="text-3xl font-semibold tracking-tight sm:text-4xl">{{ selectedCategory?.name || 'Shop every product' }}</h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Search, compare, and browse {{ identity.display_name }} by category, collection, price, and availability.
        </p>
      </div>
      <div class="flex items-center gap-3">
        <span class="whitespace-nowrap text-sm font-semibold text-muted-foreground">{{ catalog?.count || 0 }} products</span>
        <Select v-model="draft.ordering" @update:model-value="apply">
          <SelectTrigger class="w-44" aria-label="Sort products">
            <SelectValue placeholder="Sort products" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="newest">Newest</SelectItem>
            <SelectItem value="price_low">Price: low to high</SelectItem>
            <SelectItem value="price_high">Price: high to low</SelectItem>
            <SelectItem value="name">Name</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>

    <div v-if="activeFilters.length" class="mt-4 flex flex-wrap gap-2" aria-label="Applied filters">
      <Button
        v-for="item in activeFilters"
        :key="item.key"
        variant="secondary"
        size="sm"
        @click="$emit('clear-filter', item.key)"
      >
        {{ item.label }}
        <X class="h-3.5 w-3.5" aria-hidden="true" />
      </Button>
      <Button variant="ghost" size="sm" @click="$emit('clear-all')">Clear all</Button>
    </div>

    <div class="mt-5 grid items-start gap-5 lg:grid-cols-[15rem_minmax(0,1fr)]">
      <aside class="hidden max-h-[calc(100dvh-13rem)] overflow-y-auto overscroll-contain border-r bg-background pr-5 lg:sticky lg:top-48 lg:block" aria-label="Product filters">
        <MarketplaceFilterControls
          v-model="draft"
          :catalog="catalog"
          :currency="identity.currency"
          @apply="apply"
          @clear="$emit('clear-all')"
        />
      </aside>

      <section aria-label="Products">
        <div v-if="catalog?.results?.length" class="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
          <MarketplaceProductCard
            v-for="product in catalog.results"
            :key="product.public_id"
            :product="product"
            :base="base"
            :slug="identity.slug"
            :currency="identity.currency"
          />
        </div>
        <StatePanel
          v-else
          class="border bg-background"
          title="No matching products"
          message="Change or clear a filter to see more of this catalog."
        >
          <Button variant="outline" @click="$emit('clear-all')">Clear filters</Button>
        </StatePanel>

        <div v-if="catalog?.next || catalog?.previous" class="mt-8 flex items-center justify-center gap-3">
          <Button variant="outline" :disabled="!catalog.previous" @click="$emit('change-page', -1)">
            <ChevronLeft class="h-4 w-4" aria-hidden="true" />
            Previous
          </Button>
          <Badge variant="outline" class="h-9 rounded-md px-4">Page {{ page }}</Badge>
          <Button variant="outline" :disabled="!catalog.next" @click="$emit('change-page', 1)">
            Next
            <ChevronRight class="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </section>
    </div>

    <Sheet v-model:open="filterOpen">
      <SheetContent side="right" class="w-[min(28rem,94vw)] overflow-y-auto">
        <SheetHeader class="text-left">
          <SheetTitle>Filter products</SheetTitle>
          <SheetDescription>Refine the catalog without leaving this page.</SheetDescription>
        </SheetHeader>
        <div class="mt-8">
          <MarketplaceFilterControls
            v-model="draft"
            :catalog="catalog"
            :currency="identity.currency"
            @apply="apply"
            @clear="$emit('clear-all')"
          />
        </div>
      </SheetContent>
    </Sheet>

    <Button
        class="fixed bottom-6 right-5 z-30 gap-2 rounded-full px-5 shadow-xl lg:hidden"
      type="button"
      @click="filterOpen = true"
    >
      <SlidersHorizontal class="h-4 w-4" aria-hidden="true" />
      Filters
      <Badge v-if="activeFilters.length" variant="secondary" class="ml-1 rounded-full">
        {{ activeFilters.length }}
      </Badge>
    </Button>
  </div>
</template>

<script setup>
import {
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
  X,
} from 'lucide-vue-next'
import MarketplaceFilterControls from './MarketplaceFilterControls.vue'
import MarketplaceProductCard from './MarketplaceProductCard.vue'

const props = defineProps({
  identity: { type: Object, required: true },
  catalog: { type: Object, default: null },
  filters: { type: Object, required: true },
  activeFilters: { type: Array, default: () => [] },
  page: { type: Number, default: 1 },
  base: { type: String, required: true },
})

const emit = defineEmits(['apply', 'clear-filter', 'clear-all', 'change-page'])
const filterOpen = ref(false)
const draft = ref({ ...props.filters })
const selectedCategory = computed(() => props.catalog?.facets?.categories?.find(
  (item) => item.slug === props.filters.category,
))

watch(
  () => props.filters,
  (value) => { draft.value = { ...value } },
  { deep: true },
)

function apply() {
  filterOpen.value = false
  emit('apply', { ...draft.value })
}
</script>
