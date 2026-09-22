<template>
  <section :data-block-type="block.type" class="py-8 sm:py-12" :class="['hero', 'commerce_hero'].includes(block.type) ? 'relative left-1/2 w-screen -translate-x-1/2 !py-0' : block.type === 'promo_strip' ? '!h-0 !py-0' : ''">
    <CommerceHeroCarousel v-if="block.type === 'commerce_hero'" :settings="settings" :offerings="offerings" :assets="assets" :site-base="siteBase" :mode="identity.branding?.storefront?.mode || 'default'" />
    <div v-else-if="block.type === 'hero'" class="grid min-h-[calc(100dvh-4.5rem)] gap-8 px-5 py-12 sm:px-10 lg:grid-cols-[1.15fr_0.85fr] lg:items-center lg:px-16">
      <div><h1 class="display-face max-w-3xl text-5xl font-semibold tracking-[-0.03em] sm:text-6xl">{{ settings.heading || 'Give this page a clear promise.' }}</h1><p class="mt-5 max-w-2xl text-base leading-7 text-muted-foreground">{{ settings.body }}</p><div class="mt-7 flex flex-wrap gap-3"><ButtonAnchor  v-if="settings.primary_label" :href="basePath(settings.primary_path)">{{ settings.primary_label }}</ButtonAnchor><ButtonAnchor variant="outline"  v-if="settings.secondary_label" :href="basePath(settings.secondary_path)">{{ settings.secondary_label }}</ButtonAnchor></div></div>
      <img v-if="asset(settings.asset_id)" :src="asset(settings.asset_id).url" :alt="asset(settings.asset_id).alt_text || ''" class="aspect-[4/3] w-full rounded-[var(--radius)] object-cover" />
    </div>
    <div v-else-if="block.type === 'text' || block.type === 'policy'" class="mx-auto max-w-3xl"><h2 v-if="settings.heading" class="display-face text-3xl font-semibold">{{ settings.heading }}</h2><p v-for="(paragraph, index) in documentParagraphs" :key="index" class="mt-4 leading-7 text-muted-foreground">{{ paragraph }}</p></div>
    <figure v-else-if="block.type === 'image' && asset(settings.asset_id)" class="mx-auto max-w-5xl"><img :src="asset(settings.asset_id).url" :alt="asset(settings.asset_id).alt_text || ''" class="w-full rounded-[var(--radius)] object-cover" /><figcaption v-if="settings.caption" class="mt-3 text-sm text-muted-foreground">{{ settings.caption }}</figcaption></figure>
    <div v-else-if="block.type === 'gallery'" class="grid gap-3" :class="galleryColumns"><figure v-for="(assetId, index) in settings.asset_ids || []" :key="assetId" class="min-w-0"><img v-if="asset(assetId)" :src="asset(assetId).url" :alt="asset(assetId).alt_text || ''" class="aspect-square w-full rounded-[var(--radius)] object-cover" /><figcaption v-if="settings.captions?.[index]" class="mt-2 text-sm text-muted-foreground">{{ settings.captions[index] }}</figcaption></figure></div>
    <div v-else-if="block.type === 'columns'" class="grid md:grid-cols-2" :class="columnGap"><article v-for="(column, index) in settings.columns || []" :key="index" class="border-t pt-5"><h2 class="display-face text-2xl font-semibold">{{ column.heading }}</h2><p class="mt-3 leading-7 text-muted-foreground">{{ column.body }}</p></article></div>
    <div v-else-if="block.type === 'cta' || block.type === 'booking_cta'" class="border-y py-10 text-center"><h2 class="display-face text-4xl font-semibold">{{ settings.heading }}</h2><p class="mx-auto mt-4 max-w-2xl text-muted-foreground">{{ settings.body }}</p><ButtonAnchor  :href="block.type === 'booking_cta' ? `${siteBase}/booking` : basePath(settings.path)" class="mt-6">{{ settings.label || 'Continue' }}</ButtonAnchor></div>
    <div v-else-if="block.type === 'product_rail'"><div class="flex items-end justify-between gap-5"><h2 class="display-face text-4xl font-semibold">{{ settings.heading || 'Featured products' }}</h2><ButtonAnchor :href="`${siteBase}/shop`" variant="outline">Shop all</ButtonAnchor></div><div class="mt-7 grid gap-x-4 gap-y-10 sm:grid-cols-2 lg:grid-cols-4"><ProductCard v-for="item in visibleOfferings" :key="item.public_id" :product="item" :base="siteBase" :slug="identity.slug" :currency="currency" /></div></div>
    <div v-else-if="['product_grid', 'featured_products', 'service_grid'].includes(block.type)"><h2 class="display-face text-3xl font-semibold">{{ settings.heading || (block.type === 'service_grid' ? 'Services' : 'Products') }}</h2><div class="mt-6 grid gap-px overflow-hidden border bg-border sm:grid-cols-2 lg:grid-cols-3"><article v-for="item in visibleOfferings" :key="item.public_id" class="bg-card p-5"><p class="font-bold">{{ item.name }}</p><p class="mt-2 text-sm leading-6 text-muted-foreground">{{ item.summary }}</p><div class="mt-5 flex items-center justify-between"><span class="font-bold">{{ formatMoney(item.base_price) }}</span><a :href="item.offering_type === 'service' ? `${siteBase}/services/${item.slug}` : `${siteBase}/product/${item.slug}`" class="text-sm font-bold text-primary">View</a></div></article></div></div>
    <div v-else-if="block.type === 'policy_highlights'" class="grid gap-8 border-y py-8 lg:grid-cols-[0.8fr_1.2fr] lg:gap-16 lg:py-12">
      <h2 class="display-face text-3xl font-semibold tracking-tight sm:text-4xl">Shopping with us.</h2>
      <div class="divide-y">
        <article v-for="(item, index) in settings.items || []" :key="index" class="grid gap-2 py-5 first:pt-0 last:pb-0 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)] sm:gap-6">
          <h3 class="text-sm font-bold sm:text-base">{{ item.heading }}</h3>
          <p class="max-w-lg text-sm leading-6 text-muted-foreground">{{ item.body }}</p>
        </article>
      </div>
    </div>
    <StorefrontPromoStrip v-else-if="block.type === 'promo_strip'" :settings="settings" :href="basePath(settings.path)" :storage-key="`pixelcore:promo:${identity.slug || 'site'}:${block.id}`" />
    <div v-else-if="block.type === 'editorial_split' || block.type === 'collection_feature'" class="grid overflow-hidden bg-secondary lg:grid-cols-2"><img v-if="asset(settings.asset_id)" :src="asset(settings.asset_id).url" :alt="asset(settings.asset_id).alt_text || ''" class="min-h-80 h-full w-full object-cover" :class="settings.media_side === 'right' ? 'lg:order-2' : ''" /><div class="flex flex-col justify-center p-8 sm:p-12"><h2 class="display-face text-4xl font-semibold">{{ settings.heading }}</h2><p class="mt-4 max-w-xl leading-7 text-muted-foreground">{{ settings.body }}</p><ButtonAnchor v-if="settings.label" :href="basePath(settings.path || `/collection/${settings.collection_slug}`)" class="mt-7 self-start">{{ settings.label }}</ButtonAnchor></div></div>
    <div v-else-if="block.type === 'category_tiles'"><h2 class="display-face text-4xl font-semibold">{{ settings.heading || 'Shop by category' }}</h2><div class="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><a v-for="(item, index) in settings.items || []" :key="index" :href="`${siteBase}/shop?category=${encodeURIComponent(item.slug)}`" class="group relative min-h-64 overflow-hidden bg-secondary p-7"><img v-if="asset(item.asset_id)" :src="asset(item.asset_id).url" :alt="asset(item.asset_id).alt_text || ''" class="absolute inset-0 h-full w-full object-cover transition duration-500 group-hover:scale-[1.025]" /><span class="absolute inset-x-5 bottom-5 bg-background px-4 py-3 text-lg font-extrabold">{{ item.label }}</span></a></div></div>
    <div v-else-if="block.type === 'faq'"><h2 class="display-face text-3xl font-semibold">{{ settings.heading || 'Frequently asked questions' }}</h2><details v-for="(item, index) in settings.items || []" :key="index" class="border-b py-4"><summary class="cursor-pointer font-bold">{{ item.question }}</summary><p class="mt-3 max-w-3xl text-sm leading-6 text-muted-foreground">{{ item.answer }}</p></details></div>
    <div v-else-if="block.type === 'contact'" class="grid gap-8 border-y py-10 lg:grid-cols-[1fr_0.8fr]"><div><h2 class="display-face text-3xl font-semibold">{{ settings.heading || 'Contact us' }}</h2><p class="mt-4 max-w-2xl leading-7 text-muted-foreground">{{ settings.body }}</p></div><address class="space-y-3 text-sm not-italic"><a v-if="settings.show_email && identity.contact_email" class="block font-bold text-primary" :href="`mailto:${identity.contact_email}`">{{ identity.contact_email }}</a><a v-if="settings.show_phone && identity.contact_phone" class="block font-bold text-primary" :href="`tel:${identity.contact_phone}`">{{ identity.contact_phone }}</a><p v-if="settings.show_address && (identity.city || identity.region)" class="leading-6 text-muted-foreground">{{ [identity.city, identity.region].filter(Boolean).join(', ') }}</p></address></div>
    <div v-else-if="['three_hero', 'product_model', 'particle_scene'].includes(block.type)" class="grid gap-7 lg:grid-cols-[0.8fr_1.2fr] lg:items-center"><div><h2 class="display-face text-4xl font-semibold">{{ settings.heading || 'Interactive view' }}</h2><p class="mt-4 leading-7 text-muted-foreground">{{ settings.body }}</p></div><ClientOnly><ThreeScene :kind="block.type" :settings="settings" :asset-url="asset(settings.asset_id)?.url" :poster-url="asset(settings.poster_asset_id)?.url" /><template #fallback><div class="min-h-[20rem] rounded-[var(--radius)] bg-secondary" /></template></ClientOnly></div>
    <div v-else class="border-y py-8 text-sm text-muted-foreground">{{ block.type.replaceAll('_', ' ') }} block</div>
  </section>
</template>

<script setup>
import CommerceHeroCarousel from './CommerceHeroCarousel.vue'
import StorefrontPromoStrip from './StorefrontPromoStrip.vue'

const props = defineProps({ block: { type: Object, required: true }, assets: { type: Object, default: () => ({}) }, offerings: { type: Array, default: () => [] }, identity: { type: Object, default: () => ({}) }, siteBase: { type: String, default: '' }, currency: { type: String, default: 'PHP' } })
const settings = computed(() => props.block.settings || {})
const asset = (id) => id ? props.assets[id] : null
const documentParagraphs = computed(() => {
  const document = settings.value.document
  if (Array.isArray(document)) return document.map((item) => typeof item === 'string' ? item : item?.text || '').filter(Boolean)
  if (document?.content) return document.content.map((item) => item?.text || item?.content?.map((node) => node.text).join('') || '').filter(Boolean)
  return settings.value.body ? [settings.value.body] : []
})
const visibleOfferings = computed(() => {
  let items = props.offerings
  if (props.block.type === 'service_grid') items = items.filter((item) => item.offering_type === 'service')
  if (props.block.type === 'product_grid') items = items.filter((item) => item.offering_type !== 'service')
  if (settings.value.offering_ids?.length) items = items.filter((item) => settings.value.offering_ids.includes(item.public_id))
  return items.slice(0, Number(settings.value.limit || 6))
})
const galleryColumns = computed(() => ({ 1: 'sm:grid-cols-1', 2: 'sm:grid-cols-2', 3: 'sm:grid-cols-2 lg:grid-cols-3', 4: 'sm:grid-cols-2 lg:grid-cols-4' }[Number(settings.value.columns || 3)]))
const columnGap = computed(() => ({ compact: 'gap-4', normal: 'gap-8', wide: 'gap-12' }[settings.value.gap] || 'gap-8'))
const basePath = (path) => path ? `${props.siteBase}${path === '/' ? '' : path}` : props.siteBase
const formatMoney = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency }).format(Number(value || 0))
</script>
