<template>
  <article class="group relative flex min-w-0 flex-col border bg-background transition duration-200 hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-lg">
    <a :href="`${base}/product/${product.slug}`" class="relative block aspect-square overflow-hidden bg-secondary/45">
      <img
        v-if="cover"
        :src="cover.url"
        :alt="cover.alt_text || product.name"
        class="h-full w-full object-cover transition duration-300 group-hover:scale-[1.025]"
        :class="hoverImage ? 'group-hover:opacity-0' : ''"
      />
      <img
        v-if="hoverImage"
        :src="hoverImage.url"
        :alt="hoverImage.alt_text || ''"
        class="absolute inset-0 h-full w-full object-cover opacity-0 transition duration-300 group-hover:scale-[1.025] group-hover:opacity-100"
      />
      <div v-if="!cover" class="grid h-full place-items-center px-5 text-center text-sm font-semibold text-muted-foreground">
        Product image coming soon
      </div>
      <div class="absolute left-2 top-2 flex flex-wrap gap-1.5">
        <Badge v-if="discount" variant="destructive">{{ discount }}</Badge>
        <Badge v-else-if="product.availability === 'out_of_stock'" variant="secondary">Sold out</Badge>
      </div>
    </a>

    <Button
      variant="secondary"
      size="icon"
      class="absolute right-2 top-2 h-9 w-9 rounded-full shadow-sm"
      :aria-label="saved ? `Remove ${product.name} from saved products` : `Save ${product.name}`"
      @click="toggleWishlist"
    >
      <Heart class="h-4 w-4" :class="saved ? 'fill-current' : ''" aria-hidden="true" />
    </Button>

    <div class="flex flex-1 flex-col p-3 sm:p-4">
      <p v-if="product.product_profile?.brand" class="truncate text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">
        {{ product.product_profile.brand }}
      </p>
      <h2 class="mt-1 line-clamp-2 min-h-10 text-sm font-extrabold leading-5">
        <a :href="`${base}/product/${product.slug}`" class="hover:text-primary">
          {{ product.name }}
        </a>
      </h2>
      <p class="mt-1 truncate text-xs text-muted-foreground">
        {{ product.category || productType }}
      </p>

      <div class="mt-auto pt-3">
        <div class="flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <strong class="text-base text-primary">{{ money(product.base_price) }}</strong>
          <span v-if="product.compare_at_price" class="text-xs text-muted-foreground line-through">
            {{ money(product.compare_at_price) }}
          </span>
        </div>
        <p v-if="product.reservation_activity" class="mt-2 flex items-center gap-1.5 text-xs font-semibold">
          <UsersRound class="h-3.5 w-3.5 text-primary" aria-hidden="true" />
          {{ product.reservation_activity.label }}
        </p>
        <div v-if="colors.length" class="mt-3 flex items-center gap-1.5" :aria-label="`${colors.length} colors available`">
          <span
            v-for="color in colors.slice(0, 5)"
            :key="color.public_id"
            class="h-3.5 w-3.5 rounded-full border"
            :style="{ backgroundColor: color.swatch_color || '#d6d3d1' }"
          />
          <span v-if="colors.length > 5" class="text-[11px] text-muted-foreground">+{{ colors.length - 5 }}</span>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup>
import { Heart, UsersRound } from 'lucide-vue-next'
import { productImages } from '@/utils/productImages'
import { discountLabel } from '@/utils/pricing'

const props = defineProps({
  product: { type: Object, required: true },
  base: { type: String, required: true },
  slug: { type: String, required: true },
  currency: { type: String, default: 'PHP' },
})

const wishlist = useWishlistStore()
const images = computed(() => productImages(props.product))
const cover = computed(() => images.value[0] || null)
const hoverImage = computed(() => {
  if (props.product.product_profile?.card_hover_enabled === false) return null
  return props.product.ordered_media?.find((item) => item.role === 'hover') || images.value[1] || null
})
const saved = computed(() => wishlist.has(props.product.public_id))
const discount = computed(() => discountLabel(props.product.base_price, props.product.compare_at_price))
const colors = computed(() =>
  props.product.variant_dimensions?.find((dimension) => dimension.display_type === 'color')?.values || [],
)
const productType = computed(() =>
  props.product.offering_type === 'digital' ? 'Digital product' : 'Product',
)

function money(value) {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: props.currency,
  }).format(Number(value || 0))
}

function toggleWishlist() {
  wishlist.toggle(props.slug, props.product.public_id)
}
</script>
