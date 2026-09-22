<template>
  <section class="min-w-0 overflow-hidden rounded-xl border bg-card" aria-labelledby="product-gallery-heading">
    <div class="flex flex-wrap items-start justify-between gap-4 border-b p-5 sm:p-6">
      <div class="max-w-2xl">
        <div class="flex items-center gap-2">
          <Images class="h-5 w-5 text-primary" aria-hidden="true" />
          <h2 id="product-gallery-heading" class="text-base font-extrabold">Product gallery</h2>
          <Badge variant="secondary">{{ items.length + (cover ? 1 : 0) }}</Badge>
        </div>
        <p class="mt-2 text-sm leading-6 text-muted-foreground">Add alternate angles, details, and lifestyle images for the product page. Choose one saved image for the product card’s hover view.</p>
      </div>
      <Button variant="outline" type="button" :disabled="disabled" @click="openPicker">
        <Plus class="h-4 w-4" aria-hidden="true" /> Add images
      </Button>
      <Input :id="inputId" class="sr-only" type="file" multiple tabindex="-1" aria-label="Choose gallery images"
        accept="image/jpeg,image/png,image/webp,image/avif" :disabled="disabled" @change="$emit('select', $event)" />
    </div>

    <div class="p-5 sm:p-6">
      <ul v-if="cover || items.length" class="grid min-w-0 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" aria-label="Primary image and gallery">
        <li v-if="cover" class="min-w-0 overflow-hidden rounded-lg border border-primary">
          <div class="relative aspect-square bg-muted/40">
            <img :src="cover.url" :alt="cover.alt_text || 'Primary product image'" class="h-full w-full object-contain p-3" />
            <Badge class="absolute left-3 top-3">Primary image</Badge>
          </div>
          <div class="space-y-3 border-t p-3">
            <p class="text-sm font-semibold">{{ coverPending ? 'New cover · not saved' : 'Product cover' }}</p>
            <Button variant="outline" size="sm" type="button" :disabled="disabled" @click="$emit('edit-cover')">Edit in Details</Button>
          </div>
        </li>
        <li v-for="(item, index) in items" :key="item.public_id" class="min-w-0 overflow-hidden rounded-lg border"
          :class="isHover(item) ? 'border-primary' : 'border-border'">
          <div class="relative aspect-square bg-muted/40">
            <img :src="item.url" :alt="item.alt_text || `Product view ${index + 1}`" class="h-full w-full object-contain p-3" loading="lazy" />
            <Badge v-if="isHover(item)" class="absolute left-3 top-3">Hover image</Badge>
          </div>
          <div class="space-y-3 border-t p-3">
            <p class="truncate text-sm font-semibold">{{ item.alt_text || `View ${index + 1}` }}</p>
            <div class="flex items-center justify-between gap-2">
              <Button variant="outline" size="sm" type="button" :disabled="disabled" :aria-pressed="isHover(item)"
                @click="isHover(item) ? $emit('clear-hover') : $emit('set-hover', item)">
                <MousePointer2 class="h-4 w-4" aria-hidden="true" />{{ isHover(item) ? 'Clear hover' : 'Use on hover' }}
              </Button>
              <Button variant="ghost" size="icon" type="button" class="shrink-0 text-destructive" :disabled="disabled"
                :aria-label="`Remove gallery view ${index + 1}`" @click="$emit('remove', item)">
                <Trash2 class="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
        </li>
      </ul>
      <div v-else-if="!pending.length" class="flex min-h-52 flex-col items-center justify-center rounded-lg border border-dashed px-5 py-8 text-center">
        <Images class="h-7 w-7 text-muted-foreground" aria-hidden="true" />
        <p class="mt-3 font-semibold">Show every angle</p>
        <p class="mt-2 max-w-md text-sm leading-6 text-muted-foreground">Set your primary image in Details, then add other views here for the product’s thumbnails, zoom view, and luxury image stack.</p>
        <Button variant="outline" type="button" class="mt-4" :disabled="disabled" @click="openPicker">Choose gallery images</Button>
      </div>

      <div v-if="pending.length" :class="cover || items.length ? 'mt-6 border-t pt-5' : ''">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <h3 class="text-sm font-bold">Ready to upload · {{ pending.length }}</h3>
          <span class="text-xs text-muted-foreground" role="status">Select Save changes to upload these images.</span>
        </div>
        <ul class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" aria-label="Images awaiting upload">
          <li v-for="(item, index) in pending" :key="item.url" class="min-w-0 overflow-hidden rounded-lg border border-dashed">
            <img :src="item.url" :alt="item.name" class="aspect-square w-full bg-muted/40 object-contain p-3" />
            <div class="flex items-center justify-between gap-2 border-t px-3 py-2">
              <span class="truncate text-xs" :title="item.name">{{ item.name }}</span>
              <Button variant="ghost" size="icon" type="button" class="shrink-0" :disabled="disabled"
                :aria-label="`Remove pending image ${item.name}`" @click="$emit('remove-pending', index)">
                <X class="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </li>
        </ul>
      </div>
      <p class="mt-4 text-xs leading-5 text-muted-foreground">JPG, PNG, WebP, or AVIF · Up to 8 MB per image · Up to 12 new images per save. Hover assignments and removal of saved images apply immediately.</p>
      <Button v-if="hover && !items.some(isHover)" variant="ghost" size="sm" type="button" class="mt-2" :disabled="disabled" @click="$emit('clear-hover')">Clear existing hover assignment</Button>
    </div>
  </section>
</template>

<script setup>
import { Images, MousePointer2, Plus, Trash2, X } from 'lucide-vue-next'

const props = defineProps({
  items: { type: Array, default: () => [] },
  cover: { type: Object, default: null },
  coverPending: Boolean,
  pending: { type: Array, default: () => [] },
  hover: { type: Object, default: null },
  disabled: Boolean,
})
defineEmits(['select', 'set-hover', 'clear-hover', 'remove', 'remove-pending', 'edit-cover'])
const inputId = useId()
const isHover = (item) => props.hover?.asset_public_id === item.asset_public_id
function openPicker() { document.getElementById(inputId)?.click() }
</script>
