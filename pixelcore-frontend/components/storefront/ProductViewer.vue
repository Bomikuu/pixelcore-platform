<template>
  <section aria-label="Product media">
    <div class="mb-4 flex items-center justify-between gap-3">
      <Tabs v-if="model" v-model="mode">
        <TabsList>
          <TabsTrigger value="photo"><Images class="mr-2 h-4 w-4" />Photos</TabsTrigger>
          <TabsTrigger value="model"><Box class="mr-2 h-4 w-4" />3D view</TabsTrigger>
        </TabsList>
      </Tabs>
      <p v-if="mode === 'photo' && images.length" class="ml-auto text-xs font-semibold text-muted-foreground">{{ activeIndex + 1 }} of {{ images.length }}</p>
    </div>

    <div v-if="mode === 'model' && model" class="aspect-square overflow-hidden bg-secondary">
      <ClientOnly>
        <ThreeScene class="h-full rounded-none" kind="product_model" :settings="sceneSettings" :asset-url="model.url" :poster-url="poster?.url || images[0]?.url" />
        <template #fallback><img v-if="poster || images[0]" :src="(poster || images[0]).url" :alt="(poster || images[0]).alt_text || product.name" class="h-full w-full object-contain" /></template>
      </ClientOnly>
    </div>

    <div v-else-if="images.length" class="grid gap-3 md:grid-cols-[5.75rem_minmax(0,1fr)]">
      <div class="order-2 flex gap-2 overflow-x-auto pb-1 md:order-1 md:max-h-[44rem] md:flex-col md:overflow-y-auto md:pr-1" aria-label="Product image thumbnails">
        <Button
          v-for="(item, index) in images"
          :key="item.public_id || item.url"
          type="button"
          variant="ghost"
          class="h-20 w-20 shrink-0 overflow-hidden rounded-md border bg-secondary p-0 hover:border-foreground/40 md:h-[5.25rem] md:w-full"
          :class="index === activeIndex ? 'border-foreground ring-1 ring-foreground' : 'border-transparent'"
          :aria-label="`View image ${index + 1} of ${images.length}`"
          :aria-current="index === activeIndex ? 'true' : undefined"
          @click="activeIndex = index"
        >
          <img :src="item.url" :alt="item.alt_text || ''" class="h-full w-full object-cover" />
        </Button>
      </div>

      <div class="group relative order-1 aspect-square min-w-0 overflow-hidden bg-secondary md:order-2">
        <Button type="button" variant="ghost" class="h-full w-full rounded-none p-0 hover:bg-transparent" :aria-label="`Zoom ${activeImage?.alt_text || product.name}`" @click="openZoom">
          <img :src="activeImage.url" :alt="activeImage.alt_text || product.name" class="h-full w-full object-contain p-4 transition-transform duration-500 group-hover:scale-[1.015] sm:p-8" />
        </Button>
        <Button class="absolute right-3 top-3 bg-background/90 shadow-sm backdrop-blur" size="icon" variant="outline" type="button" aria-label="Open image zoom" @click="openZoom"><Maximize2 class="h-4 w-4" /></Button>
        <template v-if="images.length > 1">
          <Button class="absolute left-3 top-1/2 -translate-y-1/2 bg-background/90 opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-focus-within:opacity-100" size="icon" variant="outline" type="button" aria-label="Previous image" @click="showPrevious"><ChevronLeft class="h-4 w-4" /></Button>
          <Button class="absolute right-3 top-1/2 -translate-y-1/2 bg-background/90 opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-focus-within:opacity-100" size="icon" variant="outline" type="button" aria-label="Next image" @click="showNext"><ChevronRight class="h-4 w-4" /></Button>
        </template>
      </div>
    </div>

    <div v-else class="flex aspect-square items-center justify-center bg-secondary px-8 text-center text-muted-foreground">No product photography yet</div>

    <Dialog v-model:open="zoomOpen">
      <DialogContent class="!flex !h-[92dvh] !w-[calc(100vw-2rem)] !max-w-[92rem] flex-col gap-0 overflow-hidden bg-background p-0">
        <DialogHeader class="flex-row items-center justify-between gap-4 border-b px-5 py-4 pr-14 text-left">
          <div><DialogTitle>{{ product.name }}</DialogTitle><DialogDescription>Image {{ activeIndex + 1 }} of {{ images.length }}</DialogDescription></div>
          <div class="flex items-center gap-1">
            <Button type="button" variant="ghost" size="icon" aria-label="Zoom out" :disabled="zoomScale <= 1" @click="zoomScale = Math.max(1, zoomScale - 0.5)"><Minus class="h-4 w-4" /></Button>
            <span class="w-12 text-center text-xs font-bold tabular-nums">{{ Math.round(zoomScale * 100) }}%</span>
            <Button type="button" variant="ghost" size="icon" aria-label="Zoom in" :disabled="zoomScale >= 2.5" @click="zoomScale = Math.min(2.5, zoomScale + 0.5)"><Plus class="h-4 w-4" /></Button>
          </div>
        </DialogHeader>
        <div class="relative flex min-h-0 flex-1 items-center justify-center overflow-auto bg-secondary/60 p-5 sm:p-10">
          <img v-if="activeImage" :src="activeImage.url" :alt="activeImage.alt_text || product.name" class="max-h-full max-w-full object-contain transition-transform duration-200" :style="{ transform: `scale(${zoomScale})` }" />
          <template v-if="images.length > 1">
            <Button class="fixed left-6 top-1/2 -translate-y-1/2 bg-background/95 shadow" size="icon" variant="outline" type="button" aria-label="Previous image" @click="showPrevious"><ChevronLeft class="h-4 w-4" /></Button>
            <Button class="fixed right-6 top-1/2 -translate-y-1/2 bg-background/95 shadow" size="icon" variant="outline" type="button" aria-label="Next image" @click="showNext"><ChevronRight class="h-4 w-4" /></Button>
          </template>
        </div>
      </DialogContent>
    </Dialog>
  </section>
</template>

<script setup>
import { productImages } from '~/utils/productImages'
import { Box, ChevronLeft, ChevronRight, Images, Maximize2, Minus, Plus } from 'lucide-vue-next'

const props = defineProps({ product: { type: Object, required: true }, activeVariantId: { type: String, default: '' } })
const mode = ref('photo')
const activeIndex = ref(0)
const zoomOpen = ref(false)
const zoomScale = ref(1)
const media = computed(() => props.product.ordered_media || [])
const images = computed(() => productImages(props.product, props.activeVariantId))
const activeImage = computed(() => images.value[activeIndex.value] || images.value[0])
const model = computed(() => media.value.find((item) => item.role === 'model'))
const poster = computed(() => media.value.find((item) => item.role === 'poster'))
const sceneSettings = { motion: 'interactive', speed: 0.4, background_color: '#f1efe8', camera: { x: 0, y: 0.25, z: 4.2 }, lighting: { ambient: 1.2, key: 1.8 } }

watch(() => props.activeVariantId, () => { activeIndex.value = 0 })
watch(images, () => { if (activeIndex.value >= images.value.length) activeIndex.value = 0 })
watch(zoomOpen, (open) => { if (!open) zoomScale.value = 1 })

function openZoom() { zoomScale.value = 1; zoomOpen.value = true }
function showPrevious() { activeIndex.value = (activeIndex.value - 1 + images.value.length) % images.value.length; zoomScale.value = 1 }
function showNext() { activeIndex.value = (activeIndex.value + 1) % images.value.length; zoomScale.value = 1 }
</script>
