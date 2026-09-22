<template>
  <article class="group relative min-w-0">
    <a :href="`${base}/product/${product.slug}`" class="block overflow-hidden bg-secondary/55">
      <div class="relative aspect-[4/5] overflow-hidden">
        <img v-if="activeImage" :src="activeImage.url" :alt="activeImage.alt_text || product.name" class="h-full w-full object-cover transition duration-500 ease-out group-hover:scale-[1.025]" :class="hoverImage && mediaIndex === 0 ? 'group-hover:opacity-0' : ''" />
        <img v-if="hoverImage && mediaIndex === 0" :src="hoverImage.url" :alt="hoverImage.alt_text || ''" class="absolute inset-0 h-full w-full object-cover opacity-0 transition duration-500 ease-out group-hover:scale-[1.025] group-hover:opacity-100" />
        <div v-if="!activeImage" class="flex h-full items-center justify-center text-sm font-semibold text-muted-foreground">Image coming soon</div>
        <Badge v-if="badge" class="absolute left-3 top-3" variant="secondary">{{ badge }}</Badge>
      </div>
    </a>
    <template v-if="galleryEnabled && images.length > 1">
      <Button variant="secondary" size="icon" class="absolute left-3 top-[42%] h-9 w-9 rounded-full opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-focus-within:opacity-100" aria-label="Previous product image" @click="moveImage(-1)"><ChevronLeft class="h-4 w-4" /></Button>
      <Button variant="secondary" size="icon" class="absolute right-3 top-[42%] h-9 w-9 rounded-full opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-focus-within:opacity-100" aria-label="Next product image" @click="moveImage(1)"><ChevronRight class="h-4 w-4" /></Button>
    </template>
    <Button variant="secondary" size="icon" class="absolute right-3 top-3 rounded-full" :aria-label="saved ? `Remove ${product.name} from wishlist` : `Save ${product.name} to wishlist`" @click="toggle">
      <Heart class="h-4 w-4" :class="saved ? 'fill-current' : ''" aria-hidden="true" />
    </Button>
    <div class="pt-4">
      <div class="flex items-start justify-between gap-4">
        <div class="min-w-0"><p v-if="product.product_profile?.brand" class="text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">{{ product.product_profile.brand }}</p><h2 class="mt-1 truncate font-extrabold"><a :href="`${base}/product/${product.slug}`">{{ product.name }}</a></h2></div>
        <div class="shrink-0 text-right"><strong>{{ money(product.base_price) }}</strong><span v-if="product.compare_at_price" class="ml-2 text-sm text-muted-foreground line-through">{{ money(product.compare_at_price) }}</span></div>
      </div>
      <p class="mt-1 text-sm text-muted-foreground">{{ product.category || productType }}</p>
      <p v-if="product.reservation_activity" class="mt-2 flex items-center gap-1.5 text-xs font-semibold text-foreground"><UsersRound class="h-3.5 w-3.5 text-primary" aria-hidden="true" />{{ product.reservation_activity.label }}</p>
      <div v-if="colors.length" class="mt-3 flex items-center gap-1.5" :aria-label="`${colors.length} colors available`"><span v-for="color in colors.slice(0, 6)" :key="color.public_id" class="h-4 w-4 rounded-full border" :style="{ backgroundColor: color.swatch_color || '#d6d3d1' }" /><span v-if="colors.length > 6" class="ml-1 text-xs text-muted-foreground">+{{ colors.length - 6 }}</span></div>
    </div>
  </article>
</template>

<script setup>
import { productImages } from '~/utils/productImages'
import { discountLabel } from '~/utils/pricing'
import { ChevronLeft, ChevronRight, Heart, UsersRound } from 'lucide-vue-next'
const props = defineProps({ product: { type: Object, required: true }, base: { type: String, required: true }, currency: { type: String, default: 'PHP' }, slug: { type: String, required: true } })
const wishlist = useWishlistStore()
const mediaIndex = ref(0)
const images = computed(() => productImages(props.product))
const activeImage = computed(() => images.value[mediaIndex.value] || images.value[0])
const hoverImage = computed(() => props.product.product_profile?.card_hover_enabled === false ? null : props.product.ordered_media?.find((item) => item.role === 'hover'))
const galleryEnabled = computed(() => Boolean(props.product.product_profile?.card_gallery_enabled))
const colors = computed(() => props.product.variant_dimensions?.find((item) => item.display_type === 'color')?.values || [])
const saved = computed(() => wishlist.has(props.product.public_id))
const badge = computed(() => props.product.availability === 'out_of_stock' ? 'Sold out' : discountLabel(props.product.base_price, props.product.compare_at_price))
const productType = computed(() => props.product.offering_type === 'digital' ? 'Digital product' : 'Product')
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency }).format(Number(value || 0))
function toggle() { wishlist.toggle(props.slug, props.product.public_id) }
function moveImage(step) { mediaIndex.value = (mediaIndex.value + step + images.value.length) % images.value.length }
</script>
