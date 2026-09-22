<template>
  <div class="mx-auto w-full max-w-[1920px] px-4 py-5 sm:px-6 xl:px-10">
    <nav class="mb-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground" aria-label="Breadcrumb">
      <a :href="base || '/'" class="hover:text-primary">Home</a>
      <ChevronRight class="h-3.5 w-3.5" aria-hidden="true" />
      <a :href="`${base}/shop`" class="hover:text-primary">Shop</a>
      <ChevronRight class="h-3.5 w-3.5" aria-hidden="true" />
      <span class="truncate">{{ product.name }}</span>
    </nav>

    <div class="grid min-w-0 gap-7 lg:grid-cols-2 lg:items-start xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)_minmax(17rem,0.68fr)] xl:gap-6 2xl:gap-8">
      <section class="min-w-0" aria-label="Product gallery">
        <ProductViewer :product="product" :active-variant-id="activeVariant?.public_id || ''" />
        <div class="mt-5 flex items-center gap-4 rounded-xl bg-secondary/40 p-4">
          <img v-if="identity.logo" :src="identity.logo" :alt="identity.display_name" class="h-12 w-12 shrink-0 rounded-lg bg-background object-contain p-1" />
          <Store v-else class="h-7 w-7 shrink-0 text-primary" aria-hidden="true" />
          <div class="min-w-0 flex-1">
            <p class="font-semibold">{{ identity.display_name }}</p>
            <p class="mt-1 text-xs text-muted-foreground">{{ identity.tagline || 'Explore more from this store.' }}</p>
          </div>
          <NuxtLink :to="`${base}/shop`" class="shrink-0 text-xs font-semibold underline underline-offset-4">Visit store</NuxtLink>
        </div>
      </section>

      <section class="min-w-0">
        <div v-if="configuredDiscount" class="mb-5 flex flex-wrap items-center gap-3 rounded-lg bg-primary/10 px-4 py-3 text-primary">
          <Tag class="h-5 w-5 shrink-0" aria-hidden="true" />
          <strong>{{ configuredDiscount }}</strong>
          <span class="text-sm">on your selected option</span>
        </div>
        <h1 class="text-2xl font-semibold leading-snug tracking-tight 2xl:text-3xl">{{ product.name }}</h1>
        <p class="mt-3 text-sm text-muted-foreground">
          {{ [product.product_profile?.brand, product.category].filter(Boolean).join(' · ') }}
        </p>
        <a href="#product-reviews" class="mt-4 inline-flex flex-wrap items-center gap-2 text-sm underline-offset-4 hover:underline">
          <span v-if="reviewSummary.count" class="flex items-center gap-0.5 text-primary" :aria-label="`${reviewSummary.average} out of 5 stars`">
            <Star v-for="star in 5" :key="star" class="h-4 w-4" :class="star <= Math.round(reviewSummary.average) ? 'fill-current' : ''" aria-hidden="true" />
          </span>
          <MessageSquare v-else class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <strong v-if="reviewSummary.count">{{ Number(reviewSummary.average).toFixed(1) }}</strong>
          <span>{{ reviewSummary.count ? `${reviewSummary.count} customer review${reviewSummary.count === 1 ? '' : 's'}` : 'No reviews yet' }}</span>
        </a>
        <div class="mt-5 border-y py-5">
          <div class="flex flex-wrap items-baseline gap-3">
            <strong class="text-3xl tracking-tight tabular-nums 2xl:text-4xl">{{ money(configuredPrice) }}</strong>
            <span v-if="configuredDiscount" class="text-sm text-muted-foreground line-through">{{ money(configuredComparePrice) }}</span>
          </div>
          <p class="mt-2 text-xs text-muted-foreground">Per item<span v-if="activeVariant?.sku"> · SKU {{ activeVariant.sku }}</span></p>
        </div>
        <p v-if="product.reservation_activity" class="mt-4 flex items-center gap-2 text-sm font-semibold">
          <UsersRound class="h-4 w-4 text-primary" aria-hidden="true" />
          {{ product.reservation_activity.label }}
        </p>
        <p v-if="product.summary" class="mt-5 text-sm leading-7 text-muted-foreground">{{ product.summary }}</p>

        <fieldset v-for="dimension in product.variant_dimensions" :key="dimension.public_id" class="mt-6">
          <legend class="text-sm font-semibold">{{ dimension.name }} <span class="ml-2 font-normal text-muted-foreground">{{ selectedValue(dimension.name) }}</span></legend>
          <div class="mt-3 flex flex-wrap gap-2">
            <Button
              v-for="value in dimension.values"
              :key="value.public_id"
              type="button"
              variant="outline"
              class="min-h-11 gap-2 px-3"
              :class="selectedValue(dimension.name) === value.label ? 'border-foreground bg-secondary ring-1 ring-foreground' : ''"
              :disabled="!valueAvailable(dimension.name, value.label)"
              :aria-pressed="selectedValue(dimension.name) === value.label"
              @click="selectDimension(dimension.name, value.label)"
            >
              <img v-if="dimension.display_type === 'color' && optionImage(dimension.name, value.label)" :src="optionImage(dimension.name, value.label)" alt="" class="h-10 w-10 rounded object-cover" />
              <span v-else-if="dimension.display_type === 'color'" class="h-4 w-4 rounded-full border" :style="{ backgroundColor: value.swatch_color || '#d6d3d1' }" />
              {{ value.label }}
            </Button>
          </div>
        </fieldset>

        <div v-if="!product.variant_dimensions?.length && activeVariants.length > 1" class="mt-6">
          <Label for="marketplace-flat-variant">Product option</Label>
          <Select v-model="flatVariantSelection">
            <SelectTrigger id="marketplace-flat-variant" class="mt-2"><SelectValue placeholder="Choose an option" /></SelectTrigger>
            <SelectContent>
              <SelectItem v-for="variant in activeVariants" :key="variant.public_id" :value="variant.public_id">{{ variant.name }}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div v-if="specifications.length" class="mt-7 border-t pt-5">
          <h2 class="font-semibold">Key attributes</h2>
          <dl class="mt-3 grid grid-cols-2 gap-x-6 gap-y-5 rounded-xl bg-secondary/40 p-4">
            <div v-for="entry in specifications.slice(0, 6)" :key="entry.key" class="min-w-0">
              <dt class="text-xs text-muted-foreground">{{ entry.key }}</dt>
              <dd class="mt-1 break-words text-sm font-medium">{{ entry.value }}</dd>
            </div>
          </dl>
          <a v-if="specifications.length > 6" href="#product-details" class="mt-3 inline-block text-xs underline underline-offset-4">See all specifications</a>
        </div>
      </section>

      <aside class="min-w-0 rounded-xl border bg-background p-5 lg:col-span-2 xl:sticky xl:top-40 xl:col-span-1 2xl:p-6" aria-label="Purchase options">
        <div class="flex items-center gap-3">
          <Truck class="h-5 w-5 text-primary" aria-hidden="true" />
          <h2 class="font-semibold">{{ fulfillmentTitle }}</h2>
        </div>
        <p class="mt-3 text-sm leading-6 text-muted-foreground">{{ fulfillmentCopy }}</p>
        <Separator class="my-5" />
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-sm font-medium">Your order</p>
            <strong class="mt-1 block text-2xl tabular-nums">{{ money(Number(configuredPrice) * validQuantity) }}</strong>
            <p v-if="activeVariant?.name" class="mt-1 text-xs text-muted-foreground">{{ activeVariant.name }}</p>
          </div>
          <Button variant="ghost" size="icon" :aria-label="wishlist.has(product.public_id) ? 'Remove from saved products' : 'Save product'" :aria-pressed="wishlist.has(product.public_id)" @click="wishlist.toggle(slug, product.public_id)">
            <Heart class="h-5 w-5" :class="wishlist.has(product.public_id) ? 'fill-current' : ''" aria-hidden="true" />
          </Button>
        </div>
        <Alert v-if="unavailable" class="mt-4">
          <AlertTitle>Currently unavailable</AlertTitle>
          <AlertDescription>Choose another option or check back for availability.</AlertDescription>
        </Alert>
        <p v-else class="mt-4 flex items-center gap-2 text-sm text-primary"><CircleCheck class="h-4 w-4" aria-hidden="true" />Available to order</p>
        <div class="mt-5 flex items-center justify-between gap-3">
          <Label for="marketplace-product-quantity">Quantity</Label>
          <div class="flex items-center rounded-lg border">
            <Button variant="ghost" size="icon" aria-label="Decrease quantity" :disabled="validQuantity <= 1" @click="quantity = validQuantity - 1"><Minus class="h-4 w-4" aria-hidden="true" /></Button>
            <Input id="marketplace-product-quantity" v-model.number="quantity" class="w-16 border-0 px-1 text-center shadow-none" type="number" min="1" max="99" step="1" />
            <Button variant="ghost" size="icon" aria-label="Increase quantity" :disabled="validQuantity >= 99" @click="quantity = validQuantity + 1"><Plus class="h-4 w-4" aria-hidden="true" /></Button>
          </div>
        </div>
        <Button class="mt-5 w-full gap-2" size="lg" :disabled="adding || unavailable || !quantityIsValid" @click="addToCart(true)">
          <LoaderCircle v-if="adding" class="h-4 w-4 animate-spin" aria-hidden="true" />
          {{ adding ? 'Preparing your order…' : 'Buy now' }}
          <ArrowRight v-if="!adding" class="h-4 w-4" aria-hidden="true" />
        </Button>
        <Button class="mt-2 w-full gap-2" variant="outline" size="lg" :disabled="adding || unavailable || !quantityIsValid" @click="addToCart(false)">
          <ShoppingBag class="h-4 w-4" aria-hidden="true" />Add to bag
        </Button>
        <p v-if="!quantityIsValid" class="mt-3 text-sm text-destructive" role="status">Choose a whole quantity between 1 and 99.</p>
        <p v-if="message" class="mt-3 text-sm text-destructive" role="alert">{{ message }}</p>
        <p class="mt-4 text-xs leading-5 text-muted-foreground">Final delivery charges, discounts, and payment options are shown at checkout.</p>
        <ProductRequestPanel :product="product" :variant="activeVariant" :quantity="validQuantity" :slug="slug" :timezone="identity.timezone" />
      </aside>
    </div>

    <section id="product-details" class="mt-10 scroll-mt-40 border-t py-8">
      <h2 class="text-xl font-semibold">About this product</h2>
      <div class="mt-5 grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div class="max-w-prose space-y-5 text-sm leading-7">
          <p class="whitespace-pre-line text-muted-foreground">{{ product.description || product.summary || 'The store has not added a description yet.' }}</p>
          <p v-if="product.product_profile?.materials"><strong>Materials</strong><br />{{ product.product_profile.materials }}</p>
          <p v-if="product.product_profile?.care_instructions"><strong>Care instructions</strong><br />{{ product.product_profile.care_instructions }}</p>
        </div>
        <dl v-if="specifications.length" class="divide-y border-y text-sm">
          <div v-for="entry in specifications" :key="entry.key" class="grid grid-cols-2 gap-4 py-3">
            <dt class="text-muted-foreground">{{ entry.key }}</dt><dd class="break-words">{{ entry.value }}</dd>
          </div>
        </dl>
      </div>
    </section>
    <ProductReviews :slug="slug" :product-slug="product.slug" :product-name="product.name" :initial-summary="product.review_summary" @summary="reviewSummary = $event" />

    <MarketplaceProductShelf v-if="product.related_products?.length" class="mt-10" title="More from this store" :products="product.related_products" :identity="identity" :base="base" />
  </div>
</template>

<!-- The marketplace has its own composition; Brand / Luxury remains unchanged. -->
<script setup>
import { ArrowRight, ChevronRight, CircleCheck, Heart, LoaderCircle, MessageSquare, Minus, Plus, ShoppingBag, Star, Store, Tag, Truck, UsersRound } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'
import { discountLabel } from '@/utils/pricing'
import ProductRequestPanel from '@/components/storefront/ProductRequestPanel.vue'
import ProductViewer from '@/components/storefront/ProductViewer.vue'
import ProductReviews from '@/components/storefront/ProductReviews.vue'
import MarketplaceProductShelf from './MarketplaceProductShelf.vue'

const props = defineProps({
  product: { type: Object, required: true },
  identity: { type: Object, required: true },
  base: { type: String, required: true },
  slug: { type: String, required: true },
})

const cart = useCartStore()
const wishlist = useWishlistStore()
const selected = reactive({})
const flatVariantId = ref('')
const quantity = ref(1)
const adding = ref(false)
const message = ref('')
const reviewSummary = ref(props.product.review_summary || { count: 0, average: null })
const specifications = computed(() => Object.entries(props.product.product_profile?.specifications || {}).map(([key, value]) => ({ key, value })))
const validQuantity = computed(() => Math.max(1, Math.min(99, Math.trunc(Number(quantity.value) || 1))))
const quantityIsValid = computed(() => Number.isInteger(Number(quantity.value)) && Number(quantity.value) >= 1 && Number(quantity.value) <= 99)

const activeVariants = computed(() => (props.product.variants || []).filter((variant) => variant.is_active))
const defaultVariant = computed(() => activeVariants.value[0] || null)
const flatVariantSelection = computed({
  get: () => flatVariantId.value || defaultVariant.value?.public_id || '',
  set: (value) => { flatVariantId.value = value },
})
const activeVariant = computed(() => {
  if (!props.product.variant_dimensions?.length) {
    return activeVariants.value.find((variant) => variant.public_id === flatVariantSelection.value) || defaultVariant.value
  }
  return activeVariants.value.find((variant) =>
    props.product.variant_dimensions.every((dimension) => variant.attributes?.[dimension.name] === selectedValue(dimension.name)),
  ) || null
})
const unavailable = computed(() => props.product.availability === 'out_of_stock' || Boolean(props.product.variants?.length && !activeVariant.value))
const configuredPrice = computed(() => activeVariant.value?.price ?? props.product.base_price)
const configuredComparePrice = computed(() => activeVariant.value?.compare_at_price || props.product.compare_at_price)
const configuredDiscount = computed(() => discountLabel(configuredPrice.value, configuredComparePrice.value))
const fulfillmentTitle = computed(() => ({ delivery: 'Delivery', pickup: 'Store pickup', digital: 'Digital delivery', booking: 'Booking' }[props.product.fulfillment_type] || 'Fulfillment'))
const fulfillmentCopy = computed(() => ({
  delivery: 'Choose your delivery address at checkout to see available shipping options and charges.',
  pickup: 'Collect from the store after your order is confirmed. Pickup details are provided with your order.',
  digital: 'Your digital product will be available after payment is confirmed.',
}[props.product.fulfillment_type] || 'Available fulfillment options are shown at checkout.'))

onMounted(() => wishlist.hydrate(props.slug))

function selectedValue(dimensionName) {
  return selected[dimensionName] ?? defaultVariant.value?.attributes?.[dimensionName] ?? ''
}

function optionImage(dimensionName, label) {
  const variant = activeVariants.value.find((item) => item.attributes?.[dimensionName] === label)
  return props.product.ordered_media?.find((item) => item.variant_public_id === variant?.public_id && ['cover', 'gallery'].includes(item.role))?.url || ''
}

function valueAvailable(dimensionName, label) {
  return activeVariants.value.some((variant) =>
    (props.product.variant_dimensions || []).every((dimension) => {
      const value = dimension.name === dimensionName ? label : selectedValue(dimension.name)
      return !value || variant.attributes?.[dimension.name] === value
    }),
  )
}

function selectDimension(dimensionName, label) {
  selected[dimensionName] = label
  if (activeVariant.value) return
  const compatibleVariant = activeVariants.value.find((variant) => variant.attributes?.[dimensionName] === label)
  if (!compatibleVariant) return
  for (const dimension of props.product.variant_dimensions || []) {
    selected[dimension.name] = compatibleVariant.attributes?.[dimension.name] || ''
  }
}

function money(value) {
  return new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.identity.currency || 'PHP' }).format(Number(value || 0))
}

async function addToCart(checkout = false) {
  if (adding.value || unavailable.value || !quantityIsValid.value) return
  adding.value = true
  message.value = ''
  try {
    await cart.add(props.slug, props.product.public_id, activeVariant.value?.public_id || null, validQuantity.value)
    if (checkout) {
      cart.drawerOpen = false
      await navigateTo(`${props.base}/checkout`)
    } else {
      cart.drawerOpen = true
      toast({ title: 'Added to bag', description: `${props.product.name} is ready for review.` })
    }
  } catch (error) {
    message.value = error?.data?.error?.message || 'This product could not be added. Refresh and try again.'
  } finally {
    adding.value = false
  }
}
</script>
