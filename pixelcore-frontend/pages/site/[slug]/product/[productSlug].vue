<template>
  <StatePanel v-if="pending" kind="loading" title="Loading product" message="Checking current options and availability." />
  <StatePanel v-else-if="error || !identity || !product" kind="error" title="Product unavailable" message="This product is not published." />
  <MarketplaceStorefrontFrame
    v-else-if="isMarketplace"
    :identity="identity"
    :navigation="navigation"
    :base="base"
    full-bleed
  >
    <MarketplaceProductDetail
      :key="product.public_id"
      :product="product"
      :identity="identity"
      :base="base"
      :slug="String(route.params.slug)"
    />
  </MarketplaceStorefrontFrame>
  <StorefrontFrame v-else :identity="identity" :navigation="navigation" :base="base" :full-bleed="isLuxury">
    <nav class="text-sm text-muted-foreground" :class="isLuxury ? 'border-b px-5 py-4 sm:px-10 lg:px-[clamp(3rem,6vw,7rem)]' : 'mb-7'" aria-label="Breadcrumb"><a :href="`${base}/shop`" class="hover:text-foreground">Shop</a><span class="mx-2">/</span><span>{{ product.name }}</span></nav>
    <div class="grid" :class="isLuxury ? 'items-start gap-0 lg:grid-cols-2' : 'gap-10 lg:grid-cols-[minmax(0,1.15fr)_minmax(22rem,0.85fr)] xl:gap-16'">
      <div :class="isLuxury ? 'order-2 lg:order-1' : ''">
        <LuxuryProductMediaStack v-if="isLuxury" :product="product" :active-variant-id="activeVariant?.public_id" />
        <ProductViewer v-else :product="product" :active-variant-id="activeVariant?.public_id" />
      </div>
      <section :class="isLuxury ? 'order-1 px-5 py-10 sm:px-10 lg:order-2 lg:sticky lg:top-[4.5rem] lg:min-h-[calc(100dvh-4.5rem)] lg:self-start lg:px-[clamp(3rem,7vw,8rem)] lg:py-16' : 'lg:sticky lg:top-28 lg:self-start'">
        <p v-if="product.product_profile?.brand" class="text-sm font-extrabold uppercase tracking-[0.08em] text-muted-foreground">{{ product.product_profile.brand }}</p>
        <h1 class="display-face mt-2 text-5xl font-semibold tracking-[-0.03em] sm:text-6xl">{{ product.name }}</h1>
        <p class="mt-3 text-muted-foreground">{{ product.category }}</p>
        <div class="mt-6 flex items-baseline gap-3"><strong class="text-2xl">{{ money(configuredPrice) }}</strong><span v-if="configuredComparePrice" class="text-base text-muted-foreground line-through">{{ money(configuredComparePrice) }}</span><Badge v-if="configuredDiscount" variant="secondary">{{ configuredDiscount }}</Badge></div>
        <p v-if="product.reservation_activity" class="mt-4 flex items-center gap-2 text-sm font-semibold"><UsersRound class="h-4 w-4 text-primary" aria-hidden="true" />{{ product.reservation_activity.label }}</p>
        <p class="mt-6 max-w-xl text-base leading-7 text-muted-foreground">{{ product.description || product.summary }}</p>

        <fieldset v-for="dimension in product.variant_dimensions" :key="dimension.public_id" class="mt-7">
          <div class="flex items-center justify-between"><legend class="font-extrabold">{{ dimension.name }}</legend><Button v-if="dimension.name.toLowerCase() === 'size' && hasSizeGuide" variant="link" class="h-auto p-0" type="button" @click="sizeGuideOpen = true">Size guide</Button></div>
          <div class="mt-3 flex flex-wrap gap-2">
            <Button v-for="value in dimension.values" :key="value.public_id" type="button" :variant="selectedValue(dimension.name) === value.label ? 'default' : 'outline'" :disabled="!valueAvailable(dimension.name, value.label)" :aria-pressed="selectedValue(dimension.name) === value.label" @click="selectDimension(dimension.name, value.label)">
              <span v-if="dimension.display_type === 'color'" class="mr-2 h-4 w-4 rounded-full border border-current/20" :style="{ backgroundColor: value.swatch_color || '#d6d3d1' }" />{{ value.label }}
            </Button>
          </div>
        </fieldset>

        <div v-if="!product.variant_dimensions?.length && product.variants.length > 1" class="mt-7"><Label for="flat-variant">Product option</Label><Select v-model="flatVariantSelection"><SelectTrigger id="flat-variant" class="mt-2"><SelectValue placeholder="Choose option" /></SelectTrigger><SelectContent><SelectItem v-for="variant in product.variants" :key="variant.public_id" :value="variant.public_id">{{ variant.name }}</SelectItem></SelectContent></Select></div>
        <label class="field-label mt-7" for="product-quantity">Quantity</label><Input id="product-quantity" v-model.number="quantity" class="max-w-28" type="number" min="1" max="99" />
        <Alert v-if="product.availability === 'out_of_stock'" class="mt-5"><AlertTitle>Currently unavailable</AlertTitle><AlertDescription>This product cannot be added until stock is available.</AlertDescription></Alert>
        <div class="mt-6 grid grid-cols-[1fr_auto] gap-2"><Button size="lg" :disabled="adding || product.availability === 'out_of_stock' || (product.variants.length && !activeVariant)" @click="addToCart">{{ adding ? 'Adding…' : 'Add to bag' }}</Button><Button size="lg" variant="outline" :aria-label="wishlist.has(product.public_id) ? 'Remove from wishlist' : 'Save to wishlist'" @click="wishlist.toggle(route.params.slug, product.public_id)"><Heart class="h-5 w-5" :class="wishlist.has(product.public_id) ? 'fill-current' : ''" /></Button></div>
        <p v-if="message" class="mt-4 text-sm" :class="messageTone" role="status">{{ message }}</p>
        <ProductRequestPanel :product="product" :variant="activeVariant" :quantity="quantity" :slug="String(route.params.slug)" :timezone="identity.timezone" />

        <Accordion type="multiple" class="mt-8 border-y">
          <AccordionItem value="details"><AccordionTrigger>Product details</AccordionTrigger><AccordionContent class="space-y-4 leading-7 text-muted-foreground"><p v-if="product.product_profile?.materials"><strong class="text-foreground">Materials:</strong> {{ product.product_profile.materials }}</p><p v-if="product.product_profile?.care_instructions"><strong class="text-foreground">Care:</strong> {{ product.product_profile.care_instructions }}</p><p v-if="!product.product_profile?.materials && !product.product_profile?.care_instructions">No additional product details have been published.</p></AccordionContent></AccordionItem>
          <AccordionItem value="specifications"><AccordionTrigger>Specifications</AccordionTrigger><AccordionContent><dl class="divide-y"><div v-for="(value, key) in product.product_profile?.specifications || {}" :key="key" class="grid grid-cols-2 gap-4 py-3 text-sm"><dt class="text-muted-foreground">{{ key }}</dt><dd class="font-semibold">{{ value }}</dd></div></dl></AccordionContent></AccordionItem>
          <AccordionItem value="fulfillment"><AccordionTrigger>Fulfillment</AccordionTrigger><AccordionContent class="leading-7 text-muted-foreground">{{ fulfillmentCopy }}</AccordionContent></AccordionItem>
        </Accordion>
      </section>
    </div>
    <section v-if="product.related_products?.length" class="border-t" :class="isLuxury ? 'px-5 py-16 sm:px-10 lg:px-[clamp(3rem,6vw,7rem)] lg:py-24' : 'mt-24 pt-12'"><div class="flex items-end justify-between gap-6"><div><h2 class="display-face text-4xl font-semibold">More to explore</h2><p class="mt-2 text-muted-foreground">Related products from {{ identity.display_name }}.</p></div><ButtonAnchor :href="`${base}/shop`" variant="outline">Shop all</ButtonAnchor></div><div class="mt-8 grid gap-x-4 gap-y-10 sm:grid-cols-2 lg:grid-cols-4"><ProductCard v-for="item in product.related_products" :key="item.public_id" :product="item" :base="base" :slug="route.params.slug" :currency="identity.currency" /></div></section>
    <Dialog v-model:open="sizeGuideOpen"><DialogContent><DialogHeader><DialogTitle>Size guide</DialogTitle><DialogDescription>Measurements supplied by {{ identity.display_name }}.</DialogDescription></DialogHeader><Table><TableBody><TableRow v-for="(value, key) in product.product_profile?.size_guide || {}" :key="key"><TableHead>{{ key }}</TableHead><TableCell>{{ value }}</TableCell></TableRow></TableBody></Table></DialogContent></Dialog>
  </StorefrontFrame>
</template>

<script setup>
import ProductRequestPanel from '~/components/storefront/ProductRequestPanel.vue'
import LuxuryProductMediaStack from '~/components/storefront/LuxuryProductMediaStack.vue'
import { discountLabel } from '~/utils/pricing'
import { Heart, UsersRound } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'
import MarketplaceProductDetail from '@/components/marketplace/MarketplaceProductDetail.vue'
import MarketplaceStorefrontFrame from '@/components/marketplace/MarketplaceStorefrontFrame.vue'
definePageMeta({ layout: 'storefront' })
const route = useRoute()
const { identity, navigation, pending: identityPending, error: identityError, baseURL, siteBase: base } = useStorefrontContext(route.params.slug)
const { data: product, pending: productPending, error: productError } = useAsyncData(`commerce-product:${route.params.slug}:${route.params.productSlug}`, () => $fetch(`public/${route.params.slug}/storefront/products/${route.params.productSlug}/`, { baseURL }))
const pending = computed(() => identityPending.value || productPending.value)
const error = computed(() => identityError.value || productError.value)
const isLuxury = computed(() => identity.value?.branding?.storefront?.mode === 'luxury')
const isMarketplace = computed(() => identity.value?.branding?.storefront?.layout === 'marketplace')
const cart = useCartStore()
const wishlist = useWishlistStore()
const selected = reactive({})
const flatVariantId = ref('')
const quantity = ref(1)
const adding = ref(false)
const sizeGuideOpen = ref(false)
const message = ref('')
const messageTone = ref('text-muted-foreground')
onMounted(() => wishlist.hydrate(route.params.slug))
const activeVariants = computed(() => (product.value?.variants || []).filter((variant) => variant.is_active))
const defaultVariant = computed(() => activeVariants.value[0] || null)
const selectedValue = (dimensionName) => selected[dimensionName] ?? defaultVariant.value?.attributes?.[dimensionName] ?? ''
const flatVariantSelection = computed({
  get: () => flatVariantId.value || defaultVariant.value?.public_id || '',
  set: (value) => { flatVariantId.value = value },
})
const activeVariant = computed(() => {
  if (!product.value?.variant_dimensions?.length) {
    return activeVariants.value.find((variant) => variant.public_id === flatVariantSelection.value) || defaultVariant.value
  }
  return activeVariants.value.find((variant) => product.value.variant_dimensions.every((dimension) => variant.attributes?.[dimension.name] === selectedValue(dimension.name))) || null
})
const configuredPrice = computed(() => activeVariant.value?.price ?? product.value?.base_price)
const configuredComparePrice = computed(() => activeVariant.value?.compare_at_price || product.value?.compare_at_price)
const configuredDiscount = computed(() => discountLabel(configuredPrice.value, configuredComparePrice.value))
useHead(() => product.value ? { title: product.value.product_profile?.seo_title || `${product.value.name} | ${identity.value?.display_name || ''}`, meta: [{ name: 'description', content: product.value.product_profile?.seo_description || product.value.summary }], script: [{ type: 'application/ld+json', innerHTML: JSON.stringify({ '@context': 'https://schema.org', '@type': 'Product', name: product.value.name, description: product.value.summary, image: (product.value.ordered_media || []).filter((item) => ['cover', 'gallery'].includes(item.role)).map((item) => item.url), sku: activeVariant.value?.sku || '', offers: { '@type': 'Offer', price: String(configuredPrice.value), priceCurrency: identity.value?.currency || 'PHP', availability: product.value.availability === 'out_of_stock' ? 'https://schema.org/OutOfStock' : 'https://schema.org/InStock' } }).replaceAll('<', '\\u003c') }] } : {})
const hasSizeGuide = computed(() => Object.keys(product.value?.product_profile?.size_guide || {}).length > 0)
const fulfillmentCopy = computed(() => ({ delivery: 'This product can be delivered using the shipping zones available at checkout.', pickup: 'This product can be collected from the business after confirmation.', digital: 'Access is provided after server-confirmed payment.' }[product.value?.fulfillment_type] || 'Fulfillment details are confirmed during checkout.'))
function valueAvailable(dimensionName, label) {
  return activeVariants.value.some((variant) => (product.value?.variant_dimensions || []).every((dimension) => {
    const value = dimension.name === dimensionName ? label : selectedValue(dimension.name)
    return !value || variant.attributes?.[dimension.name] === value
  }))
}
function selectDimension(dimensionName, label) {
  selected[dimensionName] = label
  if (activeVariant.value) return
  const compatibleVariant = activeVariants.value.find((variant) => variant.attributes?.[dimensionName] === label)
  if (!compatibleVariant) return
  for (const dimension of product.value?.variant_dimensions || []) selected[dimension.name] = compatibleVariant.attributes?.[dimension.name] || ''
}
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: identity.value?.currency || 'PHP' }).format(Number(value || 0))
async function addToCart() { adding.value = true; message.value = ''; try { await cart.add(route.params.slug, product.value.public_id, activeVariant.value?.public_id || null, quantity.value); cart.drawerOpen = true; toast({ title: 'Added to bag', description: `${product.value.name} is ready for review.` }) } catch (requestError) { message.value = requestError?.data?.error?.message || 'This product could not be added. Refresh its availability and try again.'; messageTone.value = 'text-destructive' } finally { adding.value = false } }
</script>
