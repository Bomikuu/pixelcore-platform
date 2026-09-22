<template>
  <article class="group relative min-w-0 border-b border-r border-border/70 bg-background">
    <a :href="`${base}/product/${product.slug}`" class="flex h-full flex-col focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
      <div class="relative flex-1 overflow-hidden bg-secondary/55" :class="featured ? 'min-h-[60dvh] lg:min-h-[70dvh]' : 'aspect-[4/5]'">
        <img
          v-if="primaryImage"
          :src="primaryImage.url"
          :alt="primaryImage.alt_text || product.name"
          class="absolute inset-0 h-full w-full object-cover transition-opacity duration-500 motion-reduce:transition-none"
          :class="secondaryImage ? 'group-hover:opacity-0 group-focus-within:opacity-0' : ''"
        />
        <img
          v-if="secondaryImage"
          :src="secondaryImage.url"
          :alt="secondaryImage.alt_text || `${product.name} alternate view`"
          class="absolute inset-0 h-full w-full object-cover opacity-0 transition-opacity duration-500 group-hover:opacity-100 group-focus-within:opacity-100 motion-reduce:transition-none"
        />
        <div v-if="!primaryImage" class="absolute inset-0 grid place-items-center p-8 text-center text-sm font-semibold text-muted-foreground">Photography coming soon</div>
      </div>
      <div class="grid min-h-32 gap-4 px-5 py-5 sm:grid-cols-[1fr_auto] sm:px-7">
        <div class="min-w-0">
          <p v-if="product.product_profile?.brand" class="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">{{ product.product_profile.brand }}</p>
          <h2 class="mt-1 text-base font-semibold tracking-[-0.015em]">{{ product.name }}</h2>
          <p class="mt-1 text-sm text-muted-foreground">{{ product.category }}</p>
          <p v-if="product.reservation_activity" class="mt-2 flex items-center gap-1.5 text-xs font-semibold"><UsersRound class="h-3.5 w-3.5" aria-hidden="true" />{{ product.reservation_activity.label }}</p>
        </div>
        <div class="text-left sm:text-right">
          <p class="font-semibold tabular-nums">{{ money(product.display_price || product.base_price) }}</p>
          <p v-if="product.compare_at_price" class="mt-1 text-sm tabular-nums text-muted-foreground"><span class="line-through">{{ money(product.compare_at_price) }}</span><span v-if="saleLabel" class="ml-2 font-semibold text-foreground">{{ saleLabel }}</span></p>
        </div>
      </div>
    </a>
    <Button
      type="button"
      variant="ghost"
      size="icon"
      class="absolute right-4 top-4 z-10 bg-background/80 text-foreground backdrop-blur hover:bg-background"
      :aria-label="wishlist.has(product.public_id) ? `Remove ${product.name} from wishlist` : `Save ${product.name} to wishlist`"
      @click="wishlist.toggle(slug, product.public_id)"
    >
      <Heart class="h-4 w-4" :class="wishlist.has(product.public_id) ? 'fill-current' : ''" />
    </Button>
  </article>
</template>

<script setup>
import { productImages } from '~/utils/productImages'
import { discountLabel } from '~/utils/pricing'
import { Heart, UsersRound } from 'lucide-vue-next'

const props = defineProps({
  product: { type: Object, required: true },
  base: { type: String, required: true },
  slug: { type: String, required: true },
  currency: { type: String, default: 'PHP' },
  featured: { type: Boolean, default: false },
})

const wishlist = useWishlistStore()
const images = computed(() => productImages(props.product))
const primaryImage = computed(() => images.value[0] || null)
const secondaryImage = computed(() => {
  if (props.product.product_profile?.card_hover_enabled === false) return null
  return props.product.ordered_media?.find((item) => item.role === 'hover') || images.value[1] || null
})
const saleLabel = computed(() => discountLabel(props.product.display_price || props.product.base_price, props.product.compare_at_price))
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency }).format(Number(value || 0))
</script>
