<template>
  <section class="min-h-screen">
    <header class="sticky top-0 z-30 flex flex-wrap items-center justify-between gap-3 border-b bg-background px-4 py-3 sm:px-6">
      <div class="flex min-w-0 items-center gap-3"><ButtonLink variant="outline"  to="/workspace/site" class="!px-3"><ArrowLeft class="h-4 w-4" aria-hidden="true" /><span class="sr-only">Back to pages</span></ButtonLink><div class="min-w-0"><p class="truncate font-bold">{{ page?.title || 'Page editor' }}</p><p class="text-xs text-muted-foreground">{{ saveState }}</p></div></div>
      <div class="flex items-center gap-2"><Button variant="outline" type="button" :disabled="!page" @click="openPreview"><Eye class="h-4 w-4" aria-hidden="true" /> Preview</Button><Button type="button" :disabled="saving || !page" @click="publish"><Upload class="h-4 w-4" aria-hidden="true" /> Publish</Button></div>
    </header>

    <StatePanel v-if="loading" kind="loading" title="Opening editor" message="Loading the latest draft revision and reusable assets." />
    <StatePanel v-else-if="error" kind="error" title="Editor unavailable" :message="error" />
    <div v-else class="grid min-h-[calc(100vh-69px)] lg:grid-cols-[16rem_minmax(0,1fr)_20rem]">
      <aside class="border-b bg-card p-4 lg:border-b-0 lg:border-r" aria-label="Block outline">
        <div class="flex items-center justify-between"><h2 class="font-bold">Outline</h2><span class="text-xs text-muted-foreground">{{ blocks.length }}/60</span></div>
        <div class="mt-4 space-y-1">
          <Button variant="ghost" v-for="(block, index) in blocks" :key="block.id" type="button" class="flex min-h-10 w-full items-center gap-2 rounded-[var(--radius)] px-3 text-left text-sm font-semibold hover:bg-muted" :class="selectedIndex === index ? 'bg-secondary text-foreground' : 'text-muted-foreground'" @click="selectedIndex = index"><GripVertical class="h-4 w-4" aria-hidden="true" /><span class="truncate capitalize">{{ block.type.replaceAll('_', ' ') }}</span></Button>
        </div>
        <label class="field-label mt-5" for="block-type">Add a block</label>
        <div class="flex gap-2"><NativeSelect id="block-type" v-model="newBlockType" class="!min-h-10"><option v-for="type in blockTypes" :key="type" :value="type">{{ type.replaceAll('_', ' ') }}</option></NativeSelect><Button variant="outline" class="!px-3" type="button" @click="addBlock"><Plus class="h-4 w-4" aria-hidden="true" /><span class="sr-only">Add block</span></Button></div>
      </aside>

      <main class="min-w-0 bg-muted/25 p-4 sm:p-6 lg:p-8" aria-label="Live page canvas">
        <div class="mx-auto max-w-6xl rounded-[var(--radius)] border bg-background px-5 shadow-[0_12px_32px_rgba(16,42,42,0.08)] sm:px-8">
          <StatePanel v-if="!blocks.length" title="This page is empty" message="Add a hero, text, catalog, booking, policy, or audited 3D block from the outline panel." />
          <SiteBlockRenderer v-for="block in blocks" :key="block.id" :block="block" :assets="assetMap" :offerings="offerings" :identity="business.activeBusiness" :currency="business.activeBusiness?.currency" />
        </div>
      </main>

      <aside class="border-t bg-card p-4 lg:border-l lg:border-t-0" aria-label="Selected block settings">
        <template v-if="selectedBlock">
          <div class="flex items-center justify-between gap-3"><h2 class="font-bold capitalize">{{ selectedBlock.type.replaceAll('_', ' ') }}</h2><Button variant="ghost" class="text-sm font-bold text-destructive" type="button" @click="removeBlock">Remove</Button></div>
          <div class="mt-5 space-y-4">
            <HeroSlidesEditor v-if="selectedBlock.type === 'commerce_hero'" v-model="selectedBlock.settings.slides" :assets="assets" @uploaded="assets.unshift($event)" />
            <div v-for="field in editableFields" :key="field.key">
              <label class="field-label" :for="`setting-${field.key}`">{{ field.label }}</label>
              <Textarea v-if="field.multiline" :id="`setting-${field.key}`" v-model="selectedBlock.settings[field.key]" class="min-h-24" />
              <Input v-else-if="field.type === 'number'" :id="`setting-${field.key}`" v-model.number="selectedBlock.settings[field.key]" type="number" :min="field.min" :max="field.max" />
              <NativeSelect v-else-if="field.options" :id="`setting-${field.key}`" v-model="selectedBlock.settings[field.key]"><option v-for="option in field.options" :key="option" :value="option">{{ option }}</option></NativeSelect>
              <Input v-else :id="`setting-${field.key}`" v-model="selectedBlock.settings[field.key]" :type="field.type || 'text'" />
            </div>
          </div>
          <Button variant="outline" class="mt-6 w-full" type="button" :disabled="saving" @click="saveDraft"><Save class="h-4 w-4" aria-hidden="true" /> {{ saving ? 'Saving…' : 'Save draft' }}</Button>
        </template>
        <p v-else class="text-sm leading-6 text-muted-foreground">Select a block from the outline to edit its bounded settings.</p>
        <p v-if="actionError" role="alert" class="mt-4 text-sm text-destructive">{{ actionError }}</p>
      </aside>
    </div>
  </section>
</template>

<script setup>
import { ArrowLeft, Eye, GripVertical, Plus, Save, Upload } from 'lucide-vue-next'
import HeroSlidesEditor from '~/components/site/HeroSlidesEditor.vue'

const route = useRoute()
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const page = ref(null)
const blocks = ref([])
const assets = ref([])
const offerings = ref([])
const selectedIndex = ref(0)
const newBlockType = ref('hero')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const actionError = ref('')
const saveState = ref('Draft not saved in this session')
const blockTypes = ['hero', 'commerce_hero', 'promo_strip', 'text', 'image', 'gallery', 'columns', 'cta', 'faq', 'contact', 'product_grid', 'featured_products', 'product_rail', 'service_grid', 'booking_cta', 'policy', 'three_hero', 'product_model', 'particle_scene']
const selectedBlock = computed(() => blocks.value[selectedIndex.value] || null)
const assetMap = computed(() => Object.fromEntries(assets.value.map((asset) => [asset.public_id, { ...asset, url: asset.file_url }])))
const editableFields = computed(() => {
  if (!selectedBlock.value) return []
  const common = {
    hero: [['heading', 'Heading'], ['body', 'Body', true], ['primary_label', 'Primary action'], ['primary_path', 'Primary path']],
    commerce_hero: [['heading', 'Opening heading'], ['body', 'Opening description', true], ['offering_ids_text', 'Featured product IDs (one per line)', true], ['primary_label', 'Opening action'], ['primary_path', 'Opening action path'], ['secondary_label', 'Secondary action'], ['secondary_path', 'Secondary action path']],
    promo_strip: [['message', 'Announcement'], ['label', 'Action label'], ['path', 'Action path']],
    text: [['document_text', 'Text', true]],
    image: [['asset_id', 'Image asset ID'], ['caption', 'Caption'], ['fit', 'Image fit', false, '', 0, 0, ['cover', 'contain']], ['aspect_ratio', 'Aspect ratio']],
    gallery: [['asset_ids_text', 'Image asset IDs (one per line)', true], ['columns', 'Columns', false, 'number', 1, 4]],
    columns: [['columns_json', 'Columns (JSON)', true], ['gap', 'Gap', false, '', 0, 0, ['compact', 'normal', 'wide']]],
    cta: [['heading', 'Heading'], ['body', 'Body', true], ['label', 'Action label'], ['path', 'Internal path']],
    faq: [['heading', 'Heading'], ['items_json', 'Questions and answers (JSON)', true]],
    contact: [['heading', 'Heading'], ['body', 'Body', true]],
    booking_cta: [['heading', 'Heading'], ['body', 'Body', true], ['label', 'Action label']],
    product_grid: [['heading', 'Heading'], ['limit', 'Item limit', false, 'number', 1, 12]],
    featured_products: [['heading', 'Heading'], ['offering_ids_text', 'Offering IDs (one per line)', true]],
    product_rail: [['heading', 'Heading'], ['offering_ids_text', 'Offering IDs (one per line)', true], ['limit', 'Item limit', false, 'number', 1, 12]],
    service_grid: [['heading', 'Heading'], ['limit', 'Item limit', false, 'number', 1, 12]],
    policy: [['heading', 'Heading'], ['document_text', 'Policy text', true], ['updated_label', 'Updated label']],
    three_hero: [['heading', 'Heading'], ['body', 'Body', true], ['asset_id', 'GLB/GLTF asset ID'], ['poster_asset_id', 'Poster asset ID'], ['background_color', 'Background color', false, 'color'], ['motion', 'Motion', false, '', 0, 0, ['none', 'subtle', 'interactive']]],
    product_model: [['asset_id', 'GLB/GLTF asset ID'], ['poster_asset_id', 'Poster asset ID'], ['motion', 'Motion', false, '', 0, 0, ['none', 'subtle', 'interactive']]],
    particle_scene: [['heading', 'Heading'], ['body', 'Body', true], ['particle_count', 'Particle count', false, 'number', 1, 1500], ['speed', 'Motion speed', false, 'number', 0, 1.5], ['motion', 'Motion', false, '', 0, 0, ['none', 'subtle', 'interactive']]],
  }
  const fields = common[selectedBlock.value.type] || []
  return fields.map(([key, label, multiline = false, type = '', min, max, options]) => ({ key, label, multiline, type, min, max, options }))
})

onMounted(load)
async function load() {
  try {
    if (!business.activeBusiness) await business.loadBusinesses()
    const id = business.activeBusiness.public_id
    const [pageResponse, assetResponse, offeringResponse] = await Promise.all([
      apiFetch(`businesses/${id}/site/pages/${route.params.pageId}/`),
      apiFetch(`businesses/${id}/assets/`),
      apiFetch(`businesses/${id}/offerings/`),
    ])
    page.value = pageResponse
    blocks.value = hydrateBlocks(pageResponse.draft_revision?.content?.blocks || [])
    assets.value = assetResponse.results || []
    offerings.value = offeringResponse.results || []
    saveState.value = `Draft revision ${pageResponse.draft_revision?.number || 0}`
  } catch (requestError) { error.value = requestError?.data?.error?.message || 'The page editor could not be loaded.' } finally { loading.value = false }
}

function defaults(type) {
  const byType = {
    hero: { eyebrow: '', heading: '', body: '', primary_label: 'Explore', primary_path: '/shop', secondary_label: '', secondary_path: '', asset_id: '', alignment: 'left' },
    commerce_hero: { heading: '', body: '', offering_id: '', offering_ids: [], primary_label: 'Shop now', primary_path: '/shop', secondary_label: '', secondary_path: '', autoplay: true },
    promo_strip: { message: '', label: '', path: '/shop' },
    text: { document: [], width: 'normal', alignment: 'left' },
    image: { asset_id: '', caption: '', fit: 'cover', aspect_ratio: '4/3' },
    gallery: { asset_ids: [], columns: 3, captions: [] },
    columns: { columns: [], gap: 'normal' },
    cta: { heading: '', body: '', label: 'Continue', path: '/', tone: 'primary' },
    faq: { heading: '', items: [] },
    contact: { heading: '', body: '', show_phone: true, show_email: true, show_address: true },
    product_grid: { heading: '', category_id: '', limit: 6, layout: 'grid' },
    featured_products: { heading: '', offering_ids: [], layout: 'grid' },
    product_rail: { heading: '', offering_ids: [], limit: 4 },
    service_grid: { heading: '', category_id: '', limit: 6, layout: 'grid' },
    booking_cta: { heading: '', body: '', service_id: '', label: 'Book now' },
    policy: { heading: '', document: [], updated_label: '' },
    three_hero: { heading: '', body: '', asset_id: '', poster_asset_id: '', background_color: '#17362F', camera: {}, lighting: {}, rotation: true, motion: 'subtle' },
    product_model: { offering_id: '', asset_id: '', poster_asset_id: '', camera: {}, lighting: {}, rotation: true, motion: 'interactive' },
    particle_scene: { heading: '', body: '', poster_asset_id: '', particle_count: 300, colors: ['#D8922B'], speed: 0.5, motion: 'subtle' },
  }
  return structuredClone(byType[type])
}
function editableSettings(settings) {
  const value = structuredClone(settings || {})
  if (Array.isArray(value.document)) value.document_text = value.document.map((item) => typeof item === 'string' ? item : item?.text || '').filter(Boolean).join('\n\n')
  if (Array.isArray(value.asset_ids)) value.asset_ids_text = value.asset_ids.join('\n')
  if (Array.isArray(value.offering_ids)) value.offering_ids_text = value.offering_ids.join('\n')
  if (Array.isArray(value.columns)) value.columns_json = JSON.stringify(value.columns, null, 2)
  if (Array.isArray(value.items)) value.items_json = JSON.stringify(value.items, null, 2)
  return value
}
function hydrateBlocks(source) { return structuredClone(source).map((block) => ({ ...block, settings: editableSettings(block.settings) })) }
function addBlock() { blocks.value.push({ id: crypto.randomUUID(), type: newBlockType.value, version: 1, settings: editableSettings(defaults(newBlockType.value)) }); selectedIndex.value = blocks.value.length - 1 }
function removeBlock() { blocks.value.splice(selectedIndex.value, 1); selectedIndex.value = Math.max(0, selectedIndex.value - 1) }
function normalizedContent() {
  const copy = JSON.parse(JSON.stringify(blocks.value))
  for (const block of copy) {
    if (block.settings.document_text !== undefined) { block.settings.document = String(block.settings.document_text).split(/\n\s*\n/).filter(Boolean); delete block.settings.document_text }
    if (block.settings.asset_ids_text !== undefined) { block.settings.asset_ids = String(block.settings.asset_ids_text).split(/\s+/).filter(Boolean); delete block.settings.asset_ids_text }
    if (block.settings.offering_ids_text !== undefined) { block.settings.offering_ids = String(block.settings.offering_ids_text).split(/\s+/).filter(Boolean); delete block.settings.offering_ids_text }
    if (block.settings.columns_json !== undefined) { block.settings.columns = JSON.parse(block.settings.columns_json || '[]'); delete block.settings.columns_json }
    if (block.settings.items_json !== undefined) { block.settings.items = JSON.parse(block.settings.items_json || '[]'); delete block.settings.items_json }
  }
  return { schema_version: 1, blocks: copy }
}
async function saveDraft() { saving.value = true; actionError.value = ''; saveState.value = 'Saving draft…'; try { page.value = await apiFetch(`businesses/${business.activeBusiness.public_id}/site/pages/${page.value.public_id}/`, { method: 'PATCH', body: { content: normalizedContent() } }); saveState.value = `Saved as revision ${page.value.draft_revision.number}` } catch (requestError) { actionError.value = requestError?.data?.error?.message || 'The draft could not be saved.'; saveState.value = 'Save failed' } finally { saving.value = false } }
async function publish() { await saveDraft(); if (actionError.value) return; saving.value = true; try { page.value = await apiFetch(`businesses/${business.activeBusiness.public_id}/site/pages/${page.value.public_id}/publish/`, { method: 'POST', body: { revision_public_id: page.value.draft_revision.public_id } }); saveState.value = `Published revision ${page.value.published_revision.number}` } catch (requestError) { actionError.value = requestError?.data?.error?.message || 'The page could not be published.' } finally { saving.value = false } }
async function openPreview() { actionError.value = ''; try { const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/site/pages/${page.value.public_id}/preview/`, { method: 'POST' }); window.open(`/site-preview?token=${encodeURIComponent(response.token)}`, '_blank', 'noopener,noreferrer') } catch (requestError) { actionError.value = requestError?.data?.error?.message || 'A preview link could not be created.' } }
</script>
