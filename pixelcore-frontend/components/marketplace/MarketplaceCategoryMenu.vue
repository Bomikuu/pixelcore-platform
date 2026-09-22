<template>
  <Popover v-model:open="open">
    <PopoverAnchor as-child>
      <nav class="hidden border-t lg:block" aria-label="Product categories">
        <div class="mx-auto flex h-12 max-w-screen-2xl items-center gap-5 px-8">
            <Button
              ref="trigger"
              variant="ghost"
              class="h-12 gap-2 rounded-none border-b-2 px-0 hover:bg-transparent"
              :class="open ? 'border-primary text-primary' : 'border-transparent'"
              :aria-expanded="open"
              aria-haspopup="dialog"
              :aria-controls="panelId"
              @click="toggleMenu"
              @pointerenter="showOnHover"
              @pointerleave="scheduleClose"
              @keydown.down.prevent="open = true"
            >
              <ListFilter class="h-4 w-4" aria-hidden="true" />
              All categories
            </Button>
          <a :href="`${base}/shop`" class="text-sm hover:text-primary">All products</a>
          <a
            v-for="item in navigation.slice(0, 4)"
            :key="item.path"
            :href="`${base}${item.path === '/' ? '' : item.path}`"
            class="truncate text-sm hover:text-primary"
          >{{ item.label }}</a>
        </div>
      </nav>
    </PopoverAnchor>
    <PopoverContent
      :id="panelId"
      align="start"
      :side-offset="0"
      :collision-padding="0"
      :style="theme"
      data-business-theme
      class="w-[var(--radix-popover-trigger-width)] max-w-[100vw] rounded-none border-x-0 border-t-0 bg-background p-0 text-foreground shadow-xl"
      @pointerenter="cancelClose"
      @pointerleave="scheduleClose"
      @open-auto-focus="handleAutoFocus"
      @close-auto-focus="restoreFocus"
    >
      <div class="mx-auto grid max-w-screen-2xl grid-cols-[18rem_minmax(0,1fr)]">
        <nav class="max-h-[min(36rem,65dvh)] overflow-y-auto overscroll-contain border-r py-5 pl-6 pr-3" aria-label="Choose a category">
          <Button
            v-for="category in categories"
            :key="category.slug"
            variant="ghost"
            class="h-auto min-h-14 w-full justify-start gap-3 rounded-none px-3 text-left"
            :class="activeSlug === category.slug ? 'bg-secondary font-bold text-primary' : ''"
            :aria-pressed="activeSlug === category.slug"
            @pointerenter="activeSlug = category.slug"
            @focus="activeSlug = category.slug"
            @click="activeSlug = category.slug"
          >
            <img v-if="category.image" :src="category.image" alt="" class="h-8 w-8 shrink-0 rounded-full object-cover" />
            <Package v-else class="h-5 w-5 shrink-0" aria-hidden="true" />
            <span class="whitespace-normal">{{ category.name }}</span>
            <ChevronRight class="ml-auto h-4 w-4 shrink-0" aria-hidden="true" />
          </Button>
          <p v-if="!categories.length" class="px-3 py-6 text-sm text-muted-foreground">Categories will appear here when published.</p>
        </nav>
        <section class="max-h-[min(36rem,65dvh)] min-w-0 overflow-y-auto overscroll-contain p-7" aria-label="Category selection">
          <div class="mb-7 flex items-center justify-between gap-4">
            <h2 class="text-xl font-semibold">{{ activeCategory?.name || 'Explore the catalog' }}</h2>
            <a :href="categoryLink" class="shrink-0 text-sm underline underline-offset-4">View all products</a>
          </div>
          <div v-if="pending" class="grid grid-cols-4 gap-5" aria-label="Loading category products">
            <Skeleton v-for="index in 8" :key="index" class="aspect-square rounded-full" />
          </div>
          <div v-else-if="error" class="py-12">
            <p class="text-sm text-muted-foreground">Products could not be loaded.</p>
            <Button variant="outline" class="mt-4" @click="refresh">Try again</Button>
          </div>
          <div v-else class="grid grid-cols-3 gap-x-6 gap-y-8 xl:grid-cols-5">
            <a
              v-for="product in products"
              :key="product.public_id"
              :href="`${base}/product/${product.slug}`"
              class="group min-w-0 text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <div class="mx-auto aspect-square max-w-36 overflow-hidden rounded-full bg-secondary/50">
                <img v-if="cover(product)" :src="cover(product).url" :alt="cover(product).alt_text || ''" class="h-full w-full object-cover motion-safe:transition-transform motion-safe:duration-300 motion-safe:group-hover:scale-105" />
                <Package v-else class="mx-auto mt-[35%] h-8 w-8 text-muted-foreground" aria-hidden="true" />
              </div>
              <p class="mt-3 line-clamp-2 text-sm leading-5 group-hover:underline">{{ product.name }}</p>
            </a>
            <a :href="categoryLink" class="group text-center">
              <span class="mx-auto grid aspect-square max-w-36 place-items-center rounded-full bg-secondary/50">
                <LayoutGrid class="h-8 w-8 text-muted-foreground" aria-hidden="true" />
              </span>
              <span class="mt-3 block text-sm group-hover:underline">View all</span>
            </a>
          </div>
        </section>
      </div>
    </PopoverContent>
  </Popover>
</template>

<script setup>
import { ChevronRight, LayoutGrid, ListFilter, Package } from 'lucide-vue-next'
import { Popover, PopoverAnchor, PopoverContent } from '@/components/ui/popover'
import { businessThemeStyle } from '@/utils/businessTheme'
import { productImages } from '@/utils/productImages'

const props = defineProps({
  identity: { type: Object, required: true },
  categories: { type: Array, default: () => [] },
  navigation: { type: Array, default: () => [] },
  base: { type: String, required: true },
})
const open = ref(false)
const trigger = ref(null)
const panelId = useId()
const hoveredOpen = ref(false)
const activeSlug = ref('')
let closeTimer
const theme = computed(() => businessThemeStyle(props.identity))
const activeCategory = computed(() => props.categories.find((item) => item.slug === activeSlug.value))
const categoryLink = computed(() => `${props.base}/shop${activeSlug.value ? '?category=' + encodeURIComponent(activeSlug.value) : ''}`)
const config = useRuntimeConfig()
const baseURL = import.meta.server ? config.apiInternalBaseUrl : config.public.apiBaseUrl
watch(() => props.categories, (items) => {
  if (!items.some((item) => item.slug === activeSlug.value)) activeSlug.value = items[0]?.slug || ''
}, { immediate: true })
const { data, pending, error, refresh } = useAsyncData(
  `marketplace-menu:${props.identity.slug}`,
  () => open.value
    ? $fetch(`public/${props.identity.slug}/storefront/products/`, {
        baseURL,
        query: { category: activeSlug.value || undefined, page_size: 12 },
      })
    : Promise.resolve(null),
  { watch: [open, activeSlug] },
)
const products = computed(() => data.value?.results || [])
const cover = (product) => productImages(product)[0]
function cancelClose() { clearTimeout(closeTimer) }
function scheduleClose() {
  cancelClose()
  closeTimer = setTimeout(() => {
    if (hoveredOpen.value) open.value = false
  }, 220)
}
function showOnHover(event) {
  if (event.pointerType !== 'mouse') return
  cancelClose()
  hoveredOpen.value = true
  open.value = true
}
function handleAutoFocus(event) {
  if (hoveredOpen.value) event.preventDefault()
}
function toggleMenu(event) {
  if (event.detail === 0) {
    hoveredOpen.value = false
    open.value = !open.value
  } else {
    open.value = hoveredOpen.value || !open.value
  }
}
function restoreFocus(event) {
  event.preventDefault()
  const active = document.activeElement
  if (!active || active === document.body || document.getElementById(panelId)?.contains(active)) {
    trigger.value?.$el?.focus()
  }
}
watch(open, (value) => { if (!value) hoveredOpen.value = false })
onBeforeUnmount(cancelClose)
</script>
