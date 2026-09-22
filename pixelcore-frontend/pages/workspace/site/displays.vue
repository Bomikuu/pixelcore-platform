<template>
  <section class="workspace-page space-y-8">
    <PageHeader title="Poster & display setup" description="Design posters and catalog screens in admin, then pair and run each display in its own dedicated tab.">
      <template #actions>
        <ButtonAnchor variant="outline" href="/poster-menu" target="_blank" rel="noopener"><ExternalLink class="h-4 w-4" aria-hidden="true" /> Open display screen</ButtonAnchor>
        <Button as-child variant="outline"><label class="cursor-pointer"><Upload class="h-4 w-4" aria-hidden="true" /> Import JSON<Input class="sr-only" type="file" accept="application/json" @change="importJson" /></label></Button>
        <Button type="button" @click="newDisplay"><Plus class="h-4 w-4" aria-hidden="true" /> New display</Button>
      </template>
    </PageHeader>

    <StatePanel v-if="loading" kind="loading" title="Loading displays" message="Retrieving layouts, offerings, media, and paired screens." />
    <StatePanel v-else-if="loadError" kind="error" title="Display Studio unavailable" :message="loadError"><Button variant="outline" @click="load">Try again</Button></StatePanel>
    <div v-else class="grid gap-8 xl:grid-cols-[17rem_minmax(0,1fr)_21rem]">
      <aside class="border-y bg-card">
        <div class="flex items-center justify-between border-b px-4 py-3"><h2 class="text-sm font-extrabold">Displays</h2><span class="text-xs text-muted-foreground">{{ displays.length }}</span></div>
        <Button v-for="display in displays" :key="display.public_id" variant="ghost" type="button" class="block w-full border-b px-4 py-4 text-left hover:bg-muted/50" :class="active?.public_id === display.public_id ? 'bg-secondary/70 text-foreground' : ''" :aria-current="active?.public_id === display.public_id ? 'true' : undefined" @click="selectDisplay(display)"><span class="block font-bold">{{ display.name }}</span><span class="mt-1 flex items-center justify-between text-xs text-muted-foreground"><span>{{ labelFor(display.kind) }}</span><StatusPill :value="display.is_published ? 'published' : 'draft'" /></span></Button>
        <p v-if="!displays.length" class="p-5 text-sm leading-6 text-muted-foreground">Create a reusable screen. Restaurant businesses can start from Poster Menu; every business can use generic display templates.</p>
      </aside>

      <section class="min-w-0">
        <div class="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div class="flex flex-wrap gap-2" aria-label="Display slides">
            <Button variant="outline" v-for="(slide, index) in editor.settings.builder.slides" :key="slide.id" type="button" :aria-current="selectedSlideId === slide.id ? 'true' : undefined" :class="selectedSlideId === slide.id ? 'border-primary text-primary' : ''" @click="selectSlide(slide)">{{ index + 1 }}</Button>
            <Button variant="outline" type="button" :disabled="editor.settings.builder.slides.length >= 12" @click="addSlide"><Plus class="h-4 w-4" aria-hidden="true" /> Slide</Button>
          </div>
          <Button v-if="editor.settings.builder.slides.length > 1" variant="outline" type="button" @click="removeSlide"><Trash2 class="h-4 w-4" aria-hidden="true" /> Remove slide</Button>
        </div>
        <div class="display-preview">
          <InteractiveDisplayCanvas
            :settings="editor.settings"
            :offerings="selectedOfferings"
            :assets="assets"
            :business-name="business.activeBusiness?.display_name"
            :background-url="selectedBackground?.file_url || ''"
            :currency="business.activeBusiness?.currency || 'PHP'"
            :selected-id="selectedElementId"
            :selected-slide-id="selectedSlideId"
            editable
            @select="selectedElementId = $event"
            @change="updateElement"
          />
        </div>
        <p class="mt-3 text-center text-xs text-muted-foreground">Drag elements to move them. Use the corner handle to resize, or arrow keys for precise movement.</p>
      </section>

      <aside class="space-y-6 border-t pt-6 xl:max-h-[calc(100vh-8rem)] xl:overflow-y-auto xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
        <form class="space-y-4" @submit.prevent="save">
          <section class="space-y-4">
            <h2 class="text-sm font-extrabold">Display</h2>
            <div><label class="field-label" for="display-name">Display name</label><Input id="display-name" v-model.trim="editor.name" required /></div>
            <div><label class="field-label" for="display-kind">Purpose</label><NativeSelect id="display-kind" v-model="editor.kind"><option value="catalog_board">Catalog board</option><option value="promotion">Promotional poster</option><option value="information">Information screen</option><option value="qr_catalog">QR catalog</option></NativeSelect></div>
            <div><label class="field-label" for="display-template">Template</label><NativeSelect id="display-template" v-model="editor.template"><option v-if="isRestaurant" value="poster_menu">Poster Menu</option><option value="feature_rows">Feature rows</option><option value="triple_grid">Triple grid</option><option value="hero_list">Hero and list</option><option value="freeform">Freeform canvas</option><option value="mobile_catalog">Mobile catalog</option></NativeSelect><p v-if="!isRestaurant" class="mt-1 text-xs text-muted-foreground">Poster Menu appears with the restaurant preset.</p></div>
            <div><label class="field-label" for="display-background-asset">Media background</label><NativeSelect id="display-background-asset" v-model="editor.background_asset_public_id"><option value="">No image</option><option v-for="asset in assets" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</option></NativeSelect></div>
            <div class="grid grid-cols-2 gap-3"><label class="text-xs font-bold">Background<Input v-model="editor.settings.background" type="color" class="mt-2 h-10 w-full border bg-transparent p-1" /></label><label class="text-xs font-bold">Text<Input v-model="editor.settings.foreground" type="color" class="mt-2 h-10 w-full border bg-transparent p-1" /></label></div>
          </section>

          <section class="border-t pt-5">
            <div class="flex items-center justify-between"><h2 class="text-sm font-extrabold">Canvas elements</h2><span class="text-xs text-muted-foreground">{{ activeSlide?.elements.length || 0 }}/60</span></div>
            <div class="mt-3 grid grid-cols-3 gap-2">
              <Button variant="ghost" v-for="option in addOptions" :key="option.type" class="element-button" type="button" :disabled="(activeSlide?.elements.length || 0) >= 60" @click="addElement(option.type)"><component :is="option.icon" class="h-4 w-4" aria-hidden="true" />{{ option.label }}</Button>
            </div>
            <div v-if="selectedElement" class="mt-5 space-y-4 border-t pt-5">
              <div class="flex items-center justify-between"><strong class="text-sm">Selected {{ elementLabel(selectedElement.type) }}</strong><Button variant="outline" type="button" aria-label="Delete selected element" @click="removeElement"><Trash2 class="h-4 w-4" /></Button></div>
              <div v-if="['business', 'heading', 'subtitle', 'text', 'social_footer'].includes(selectedElement.type)"><label class="field-label" for="element-content">Text</label><Textarea id="element-content" v-model.trim="selectedElement.content" class="min-h-20" maxlength="300" /></div>
              <div v-if="selectedElement.type === 'offering'"><label class="field-label" for="element-offering">Offering</label><NativeSelect id="element-offering" v-model="selectedElement.offering_id"><option value="">Choose an offering</option><option v-for="offering in selectedOfferings" :key="offering.public_id" :value="offering.public_id">{{ offering.name }}</option></NativeSelect></div>
              <div v-if="selectedElement.type === 'image'"><label class="field-label" for="element-image">Image</label><NativeSelect id="element-image" v-model="selectedElement.asset_id"><option value="">Choose an image</option><option v-for="asset in assets" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</option></NativeSelect></div>
              <div class="grid grid-cols-2 gap-3"><label class="text-xs font-bold">X position<Input v-model.number="selectedElement.x" class="mt-1" type="number" min="0" max="96" /></label><label class="text-xs font-bold">Y position<Input v-model.number="selectedElement.y" class="mt-1" type="number" min="0" max="96" /></label><label class="text-xs font-bold">Width<Input v-model.number="selectedElement.width" class="mt-1" type="number" min="4" max="100" /></label><label class="text-xs font-bold">Height<Input v-model.number="selectedElement.height" class="mt-1" type="number" min="4" max="100" /></label></div>
              <div v-if="selectedElement.style" class="grid grid-cols-2 gap-3"><label class="text-xs font-bold">Type size<Input v-model.number="selectedElement.style.font_size" class="mt-1" type="number" min="10" max="120" /></label><label class="text-xs font-bold">Color<Input v-model="selectedElement.style.color" type="color" class="mt-1 h-10 w-full border bg-transparent p-1" /></label></div>
              <div class="grid grid-cols-2 gap-2"><Button variant="outline" type="button" @click="moveLayer(-1)">Send back</Button><Button variant="outline" type="button" @click="moveLayer(1)">Bring forward</Button></div>
            </div>
          </section>

          <fieldset class="border-t pt-5"><legend class="field-label">Available offerings</legend><div class="max-h-48 space-y-2 overflow-y-auto border-y py-2"><label v-for="offering in offerings" :key="offering.public_id" class="flex items-start gap-2 px-1 text-sm"><NativeCheckbox v-model="editor.offering_ids" :value="offering.public_id" class="mt-1" /><span>{{ offering.name }}<span class="block text-xs text-muted-foreground">{{ money(offering.base_price) }}</span></span></label><p v-if="!offerings.length" class="py-3 text-xs text-muted-foreground">Publish catalog offerings to select them here.</p></div></fieldset>
          <p v-if="saveMessage" class="text-sm" :class="saveError ? 'text-destructive' : 'text-primary'" role="status">{{ saveMessage }}</p>
          <div class="grid grid-cols-2 gap-2"><Button variant="outline" type="button" @click="exportJson"><Download class="h-4 w-4" aria-hidden="true" /> Export</Button><Button :disabled="saving">{{ saving ? 'Saving…' : 'Save draft' }}</Button></div>
        </form>
        <div v-if="active" class="border-t pt-5">
          <template v-if="!active.is_published">
            <Button variant="outline" v-if="!confirmingPublish" class="w-full" type="button" @click="confirmingPublish = true">Publish display</Button>
            <div v-else role="group" aria-label="Confirm display publication" class="space-y-3 border-y bg-secondary/35 p-4">
              <p class="text-sm leading-6">Publish this display to its public link and assigned screens?</p>
              <div class="grid grid-cols-2 gap-2">
                <Button variant="outline" type="button" @click="confirmingPublish = false">Keep draft</Button>
                <Button type="button" @click="publish">Confirm publish</Button>
              </div>
            </div>
          </template>
          <ButtonAnchor variant="outline"  v-else :href="active.public_url" target="_blank" rel="noopener" class="w-full">Open live display <ExternalLink class="h-4 w-4" aria-hidden="true" /></ButtonAnchor>
        </div>
      </aside>
    </div>

    <section class="border-t pt-8">
      <div class="flex flex-wrap items-end justify-between gap-5">
        <div><h2 class="text-xl font-extrabold">Screen setup</h2><p class="mt-2 text-sm text-muted-foreground">Create a signage device, generate its single-use setup code, then open the dedicated screen in a new tab.</p></div>
        <div class="flex flex-wrap gap-2"><ButtonAnchor variant="outline" href="/poster-menu" target="_blank" rel="noopener"><ExternalLink class="h-4 w-4" aria-hidden="true" /> Open screen</ButtonAnchor><Button v-if="!showDeviceForm" type="button" @click="showDeviceForm = true"><MonitorUp class="h-4 w-4" aria-hidden="true" /> Add screen</Button></div>
      </div>
      <form v-if="showDeviceForm" class="mt-5 flex flex-col gap-3 border-y bg-secondary/35 p-4 sm:flex-row sm:items-end" @submit.prevent="createDevice">
        <label class="field-label flex-1">Screen name<Input v-model.trim="deviceName" class="mt-1" maxlength="120" required /></label>
        <Button variant="outline" type="button" @click="showDeviceForm = false; deviceName = ''">Cancel</Button>
        <Button :disabled="savingDevice">{{ savingDevice ? 'Adding screen…' : 'Create screen' }}</Button>
      </form>
      <div v-if="devices.length" class="mt-5 border-y bg-card"><div v-for="device in devices" :key="device.public_id" class="resource-row sm:grid-cols-[1fr_auto_auto_auto]"><div><p class="font-bold">{{ device.name }}</p><p class="mt-1 text-xs text-muted-foreground">{{ device.last_seen_at ? `Last seen ${formatDate(device.last_seen_at)}` : 'Not paired yet' }}</p></div><code v-if="pairingCodes[device.public_id]" class="border bg-muted px-3 py-2 font-mono text-lg font-bold tracking-[.18em]">{{ pairingCodes[device.public_id] }}</code><Button variant="outline" type="button" :disabled="!active?.is_published" @click="assignDevice(device)">Assign current</Button><Button variant="outline" type="button" @click="showPairingCode(device)">New setup code</Button></div></div>
    </section>
  </section>
</template>

<script setup>
import { Download, ExternalLink, Image, LayoutGrid, MonitorUp, Plus, Tag, Trash2, Type, Upload } from 'lucide-vue-next'
import InteractiveDisplayCanvas from '@/components/display/InteractiveDisplayCanvas.vue'
import { toast } from '@/components/ui/toast'

const business = useBusinessStore()
const { apiFetch } = useApiClient()
const displays = ref([]); const offerings = ref([]); const assets = ref([]); const devices = ref([]); const active = ref(null)
const loading = ref(true); const loadError = ref(''); const saving = ref(false); const saveMessage = ref(''); const saveError = ref(false); const confirmingPublish = ref(false); const showDeviceForm = ref(false); const savingDevice = ref(false); const deviceName = ref(''); const pairingCodes = reactive({})
const selectedElementId = ref(''); const selectedSlideId = ref('')
const addOptions = [
  { type: 'business', label: 'Brand', icon: Tag }, { type: 'heading', label: 'Heading', icon: Type }, { type: 'text', label: 'Text', icon: Type },
  { type: 'offering', label: 'Offering', icon: LayoutGrid }, { type: 'offering_group', label: 'Catalog', icon: LayoutGrid }, { type: 'image', label: 'Image', icon: Image },
]
const editor = reactive({ name: '', kind: 'catalog_board', template: 'feature_rows', offering_ids: [], background_asset_public_id: '', settings: defaultSettings() })
const isRestaurant = computed(() => business.activeBusiness?.industry_preset === 'restaurant')
const selectedOfferings = computed(() => offerings.value.filter((item) => editor.offering_ids.includes(item.public_id)))
const selectedBackground = computed(() => assets.value.find((item) => item.public_id === editor.background_asset_public_id))
const activeSlide = computed(() => editor.settings.builder.slides.find((slide) => slide.id === selectedSlideId.value) || editor.settings.builder.slides[0])
const selectedElement = computed(() => activeSlide.value?.elements.find((element) => element.id === selectedElementId.value) || null)

watch(() => business.activeBusiness?.public_id, (value) => { if (value) load() })
onMounted(async () => { if (!business.activeBusiness) await business.loadBusinesses(); await load() })

function uid(prefix) { return `${prefix}-${globalThis.crypto?.randomUUID?.() || Date.now().toString(36)}` }
function defaultSettings() { return { heading: 'Make this screen yours', message: 'Add a focused message for customers or your team.', background: '#102a2a', foreground: '#f7f3ea', builder: { version: 1, slides_enabled: false, slideshow_enabled: false, slides: [{ id: uid('slide'), name: 'Slide 1', duration_seconds: 8, elements: [] }] } } }
function baseElement(type) {
  const defaults = {
    business: { x: 7, y: 7, width: 40, height: 6, content: '', size: 22 }, heading: { x: 7, y: 15, width: 52, height: 18, content: 'Make this screen yours', size: 72 },
    text: { x: 7, y: 36, width: 42, height: 12, content: 'Add a focused message for customers or your team.', size: 28 }, offering: { x: 57, y: 10, width: 36, height: 32, offering_id: '', size: 30 },
    offering_group: { x: 7, y: 55, width: 86, height: 36, offering_ids: [], size: 28 }, image: { x: 58, y: 12, width: 34, height: 38, asset_id: '', size: 24 },
  }[type] || { x: 7, y: 45, width: 40, height: 10, content: '', size: 28 }
  return { id: uid(type), type, x: defaults.x, y: defaults.y, width: defaults.width, height: defaults.height, rotation: 0, z_index: 10, visible: true, content: defaults.content || '', offering_id: defaults.offering_id || '', offering_ids: defaults.offering_ids || [], asset_id: defaults.asset_id || '', style: { font_size: defaults.size, font_weight: 700, color: editor?.settings?.foreground || '#f7f3ea', text_align: 'left' } }
}
function seedDefaultElements(settings) { const slide = settings.builder.slides[0]; slide.elements = [baseElement('business'), baseElement('heading'), baseElement('text'), baseElement('offering_group')]; slide.elements[1].content = settings.heading; slide.elements[2].content = settings.message; return settings }
function normaliseSettings(source = {}) {
  const rawSource = toRaw(source)
  const settings = { ...defaultSettings(), ...structuredClone(rawSource) }
  const rawBuilder = rawSource.builder && typeof rawSource.builder === 'object' ? structuredClone(rawSource.builder) : null
  settings.builder = { version: 1, slides_enabled: false, slideshow_enabled: false, ...(rawBuilder || {}) }
  if (!Array.isArray(settings.builder.slides) || !settings.builder.slides.length) settings.builder.slides = defaultSettings().builder.slides
  settings.builder.slides = settings.builder.slides.slice(0, 12).map((slide, index) => ({ id: String(slide.id || uid('slide')), name: String(slide.name || `Slide ${index + 1}`), duration_seconds: Math.min(60, Math.max(3, Number(slide.duration_seconds || 8))), elements: Array.isArray(slide.elements) ? slide.elements.slice(0, 60) : [] }))
  if (!settings.builder.slides[0].elements.length) seedDefaultElements(settings)
  return settings
}
async function load() {
  if (!business.activeBusiness) return
  loading.value = true; loadError.value = ''
  try {
    const id = business.activeBusiness.public_id
    const [displayResponse, offeringResponse, assetResponse, deviceResponse] = await Promise.all([apiFetch(`businesses/${id}/displays/`), apiFetch(`businesses/${id}/offerings/?status=published`), apiFetch(`businesses/${id}/assets/`), apiFetch(`businesses/${id}/devices/`)])
    displays.value = displayResponse.results || []; offerings.value = offeringResponse.results || []; assets.value = (assetResponse.results || []).filter((item) => item.asset_type === 'image'); devices.value = (deviceResponse.results || []).filter((item) => item.device_type === 'signage')
    if (!active.value && displays.value.length) selectDisplay(displays.value[0]); else if (!displays.value.length) newDisplay()
  } catch (error) { loadError.value = error?.data?.error?.message || 'Could not load Display Studio.' } finally { loading.value = false }
}
function selectDisplay(display) { active.value = display; confirmingPublish.value = false; Object.assign(editor, { name: display.name, kind: display.kind, template: display.template, offering_ids: [...(display.offering_ids || [])], background_asset_public_id: display.background_asset_public_id || '', settings: normaliseSettings(display.settings) }); selectedSlideId.value = editor.settings.builder.slides[0].id; selectedElementId.value = editor.settings.builder.slides[0].elements[0]?.id || '' }
function newDisplay() { active.value = null; confirmingPublish.value = false; const settings = defaultSettings(); seedDefaultElements(settings); Object.assign(editor, { name: '', kind: 'catalog_board', template: isRestaurant.value ? 'poster_menu' : 'feature_rows', offering_ids: [], background_asset_public_id: '', settings }); selectedSlideId.value = settings.builder.slides[0].id; selectedElementId.value = settings.builder.slides[0].elements[0]?.id || ''; saveMessage.value = '' }
function selectSlide(slide) { selectedSlideId.value = slide.id; selectedElementId.value = slide.elements[0]?.id || '' }
function addSlide() { const slide = { id: uid('slide'), name: `Slide ${editor.settings.builder.slides.length + 1}`, duration_seconds: 8, elements: [] }; editor.settings.builder.slides.push(slide); editor.settings.builder.slides_enabled = true; selectSlide(slide) }
function removeSlide() { const index = editor.settings.builder.slides.findIndex((slide) => slide.id === selectedSlideId.value); editor.settings.builder.slides.splice(index, 1); selectSlide(editor.settings.builder.slides[Math.max(0, index - 1)]) }
function addElement(type) { const element = baseElement(type); if (type === 'offering_group') element.offering_ids = [...editor.offering_ids]; activeSlide.value.elements.push(element); selectedElementId.value = element.id }
function updateElement(next) { const index = activeSlide.value.elements.findIndex((element) => element.id === next.id); if (index >= 0) activeSlide.value.elements[index] = next }
function removeElement() { const index = activeSlide.value.elements.findIndex((element) => element.id === selectedElementId.value); activeSlide.value.elements.splice(index, 1); selectedElementId.value = activeSlide.value.elements[Math.max(0, index - 1)]?.id || '' }
function moveLayer(delta) { if (!selectedElement.value) return; selectedElement.value.z_index = Math.max(1, Number(selectedElement.value.z_index || 1) + delta) }
function payload() { return { name: editor.name, kind: editor.kind, template: editor.template, offering_ids: editor.offering_ids, background_asset_public_id: editor.background_asset_public_id || null, settings: structuredClone(toRaw(editor.settings)) } }
async function save() { saving.value = true; saveMessage.value = ''; saveError.value = false; try { const id = business.activeBusiness.public_id; const path = active.value ? `businesses/${id}/displays/${active.value.public_id}/` : `businesses/${id}/displays/`; const saved = await apiFetch(path, { method: active.value ? 'PATCH' : 'POST', body: payload() }); const index = displays.value.findIndex((item) => item.public_id === saved.public_id); if (index >= 0) displays.value[index] = saved; else displays.value.unshift(saved); selectDisplay(saved); saveMessage.value = 'Draft saved.'; toast({ title: 'Display saved', description: `${saved.name} is ready for review.` }) } catch (error) { saveError.value = true; saveMessage.value = error?.data?.error?.message || 'The display could not be saved.'; toast({ title: 'Display not saved', description: saveMessage.value, variant: 'destructive' }) } finally { saving.value = false } }
async function publish() { if (!active.value) return; active.value = await apiFetch(`businesses/${business.activeBusiness.public_id}/displays/${active.value.public_id}/publish/`, { method: 'POST' }); displays.value[displays.value.findIndex((item) => item.public_id === active.value.public_id)] = active.value; confirmingPublish.value = false; saveMessage.value = 'Display published.'; toast({ title: 'Display published', description: `${active.value.name} is now available to paired screens.` }) }
function exportJson() { const blob = new Blob([JSON.stringify({ schema_version: 1, ...payload() }, null, 2)], { type: 'application/json' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `${editor.name || 'pixelcore-display'}.json`; link.click(); URL.revokeObjectURL(link.href) }
async function importJson(event) { const file = event.target.files?.[0]; if (!file) return; try { if (file.size > 200_000) throw new Error('large'); const data = JSON.parse(await file.text()); Object.assign(editor, { name: data.name || file.name.replace(/\.json$/i, ''), kind: data.kind || 'catalog_board', template: data.template || 'freeform', offering_ids: Array.isArray(data.offering_ids) ? data.offering_ids : [], background_asset_public_id: '', settings: normaliseSettings(data.settings) }); active.value = null; selectedSlideId.value = editor.settings.builder.slides[0].id; selectedElementId.value = editor.settings.builder.slides[0].elements[0]?.id || ''; saveMessage.value = 'Imported locally. Review and save to publish.'; saveError.value = false } catch { saveMessage.value = 'That file is not valid Display Studio JSON.'; saveError.value = true } event.target.value = '' }
async function createDevice() { savingDevice.value = true; saveMessage.value = ''; try { const device = await apiFetch(`businesses/${business.activeBusiness.public_id}/devices/`, { method: 'POST', body: { name: deviceName.value, device_type: 'signage', is_active: true, configuration: {} } }); devices.value.push(device); deviceName.value = ''; showDeviceForm.value = false; await showPairingCode(device); saveMessage.value = 'Screen created. Enter its single-use setup code on the signage device.'; saveError.value = false; toast({ title: 'Screen created', description: `${device.name} is ready to pair.` }) } catch (error) { saveMessage.value = error?.data?.error?.message || 'The screen could not be created.'; saveError.value = true; toast({ title: 'Screen not created', description: saveMessage.value, variant: 'destructive' }) } finally { savingDevice.value = false } }
async function showPairingCode(device) { const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/devices/${device.public_id}/pairing-code/`, { method: 'POST' }); pairingCodes[device.public_id] = response.pairing_code; toast({ title: 'Setup code ready', description: `Enter ${response.pairing_code} on ${device.name}.` }) }
async function assignDevice(device) { if (!active.value?.is_published) return; await apiFetch(`businesses/${business.activeBusiness.public_id}/displays/${active.value.public_id}/assign-device/`, { method: 'POST', body: { device_public_id: device.public_id } }); saveMessage.value = `${active.value.name} assigned to ${device.name}.`; saveError.value = false; toast({ title: 'Display assigned', description: saveMessage.value }) }
const elementLabel = (value) => ({ business: 'brand', heading: 'heading', subtitle: 'subtitle', text: 'text', offering: 'offering', offering_group: 'catalog', image: 'image', social_footer: 'social footer' }[value] || 'element')
const labelFor = (value) => ({ catalog_board: 'Catalog board', promotion: 'Promotion', information: 'Information screen', qr_catalog: 'QR catalog' }[value] || value)
const money = (value) => new Intl.NumberFormat('en-PH', { style: 'currency', currency: business.activeBusiness?.currency || 'PHP' }).format(Number(value || 0))
const formatDate = (value) => new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
</script>

<style scoped>
.display-preview { aspect-ratio: 16 / 9; min-height: 24rem; overflow: hidden; border: 1px solid hsl(var(--border)); border-radius: .75rem; box-shadow: 0 14px 30px -20px hsl(var(--foreground) / .28); }
.element-button { display: flex; min-height: 3.75rem; flex-direction: column; justify-content: space-between; gap: .5rem; border: 1px solid hsl(var(--border)); padding: .6rem; text-align: left; font-size: .7rem; font-weight: 800; }
.element-button:hover { border-color: hsl(var(--primary)); color: hsl(var(--primary)); }
.element-button:disabled { cursor: not-allowed; opacity: .45; }
@media (max-width: 640px) { .display-preview { aspect-ratio: 4 / 5; min-height: 30rem; } }
</style>
