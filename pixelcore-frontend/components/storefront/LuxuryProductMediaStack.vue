<template>
  <section aria-label="Product media" class="border-r border-border/70">
    <div v-if="images.length" class="divide-y divide-border/70">
      <Button
        v-for="(item, index) in images"
        :key="item.public_id || item.url"
        type="button"
        variant="ghost"
        class="group relative block min-h-[68dvh] w-full overflow-hidden rounded-none bg-secondary/55 p-0 hover:bg-secondary/55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring lg:min-h-[88dvh]"
        :aria-label="`Zoom image ${index + 1} of ${images.length}`"
        @click="openZoom(index)"
      >
        <img
          :src="item.url"
          :alt="item.alt_text || product.name"
          class="absolute inset-0 h-full w-full object-contain p-5 transition-transform duration-500 group-hover:scale-[1.012] motion-reduce:transition-none sm:p-10"
        />
        <span class="absolute bottom-5 right-5 grid h-10 w-10 place-items-center bg-background/90 text-foreground opacity-0 backdrop-blur transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100 motion-reduce:transition-none" aria-hidden="true">
          <Maximize2 class="h-4 w-4" />
        </span>
      </Button>
    </div>

    <div v-else class="grid min-h-[72dvh] place-items-center bg-secondary/55 px-8 text-center text-muted-foreground">No product photography yet</div>

    <div v-if="model" class="min-h-[70dvh] border-t border-border/70 bg-secondary/55 lg:min-h-[88dvh]">
      <ClientOnly>
        <ThreeScene class="h-[70dvh] rounded-none lg:h-[88dvh]" kind="product_model" :settings="sceneSettings" :asset-url="model.url" :poster-url="poster?.url || images[0]?.url" />
        <template #fallback><img v-if="poster || images[0]" :src="(poster || images[0]).url" :alt="(poster || images[0]).alt_text || product.name" class="h-[70dvh] w-full object-contain p-8 lg:h-[88dvh]" /></template>
      </ClientOnly>
    </div>

    <Dialog v-model:open="zoomOpen">
      <DialogContent class="!flex !h-[94dvh] !w-[calc(100vw-1rem)] !max-w-[100rem] flex-col gap-0 overflow-hidden bg-background p-0">
        <DialogHeader class="flex-row items-center justify-between gap-4 border-b px-5 py-4 pr-14 text-left">
          <div>
            <DialogTitle>{{ product.name }}</DialogTitle>
            <DialogDescription>Image {{ activeIndex + 1 }} of {{ images.length }}</DialogDescription>
          </div>
          <div class="flex items-center gap-1">
            <Button type="button" variant="ghost" size="icon" aria-label="Zoom out" :disabled="zoomScale <= 1" @click="zoomScale = Math.max(1, zoomScale - 0.5)"><Minus class="h-4 w-4" /></Button>
            <span class="w-12 text-center text-xs font-bold tabular-nums">{{ Math.round(zoomScale * 100) }}%</span>
            <Button type="button" variant="ghost" size="icon" aria-label="Zoom in" :disabled="zoomScale >= 2.5" @click="zoomScale = Math.min(2.5, zoomScale + 0.5)"><Plus class="h-4 w-4" /></Button>
          </div>
        </DialogHeader>
        <div class="relative flex min-h-0 flex-1 items-center justify-center overflow-auto bg-secondary/55 p-5 sm:p-10">
          <img v-if="activeImage" :src="activeImage.url" :alt="activeImage.alt_text || product.name" class="max-h-full max-w-full object-contain transition-transform duration-200 motion-reduce:transition-none" :style="{ transform: `scale(${zoomScale})` }" />
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
import { ChevronLeft, ChevronRight, Maximize2, Minus, Plus } from 'lucide-vue-next'

const props = defineProps({ product: { type: Object, required: true }, activeVariantId: { type: String, default: '' } })
const zoomOpen = ref(false)
const activeIndex = ref(0)
const zoomScale = ref(1)
const media = computed(() => props.product.ordered_media || [])
const images = computed(() => productImages(props.product, props.activeVariantId))
const activeImage = computed(() => images.value[activeIndex.value] || null)
const model = computed(() => media.value.find((item) => item.role === 'model'))
const poster = computed(() => media.value.find((item) => item.role === 'poster'))
const sceneSettings = { motion: 'interactive', speed: 0.35, background_color: '#f4f5f3', camera: { x: 0, y: 0.25, z: 4.2 }, lighting: { ambient: 1.2, key: 1.8 } }

function openZoom(index) { activeIndex.value = index; zoomScale.value = 1; zoomOpen.value = true }
function showPrevious() { activeIndex.value = (activeIndex.value - 1 + images.value.length) % images.value.length; zoomScale.value = 1 }
function showNext() { activeIndex.value = (activeIndex.value + 1) % images.value.length; zoomScale.value = 1 }

watch(() => props.activeVariantId, () => { activeIndex.value = 0 })
watch(images, () => { if (activeIndex.value >= images.value.length) activeIndex.value = 0 })
watch(zoomOpen, (open) => { if (!open) zoomScale.value = 1 })
</script>
