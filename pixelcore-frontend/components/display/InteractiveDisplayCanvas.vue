<template>
  <div
    ref="canvas"
    class="display-canvas"
    :style="{ backgroundColor: settings.background || '#102a2a', color: settings.foreground || '#f7f3ea' }"
    @pointerdown.self="emit('select', '')"
  >
    <img v-if="backgroundUrl" :src="backgroundUrl" alt="" class="display-canvas__background" />
    <div
      v-for="element in visibleElements"
      :key="element.id"
      class="display-element"
      :class="{ 'display-element--editable': editable, 'display-element--selected': selectedId === element.id }"
      :style="elementStyle(element)"
      :role="editable ? 'button' : undefined"
      :tabindex="editable ? 0 : undefined"
      :aria-label="editable ? `Move ${elementLabel(element.type)}` : undefined"
      @pointerdown="editable && startInteraction($event, element, 'move')"
      @keydown="editable && moveWithKeyboard($event, element)"
    >
      <p v-if="element.type === 'business'" class="display-element__business">{{ element.content || businessName }}</p>
      <p v-else-if="element.type === 'heading'" class="display-element__heading">{{ element.content || settings.heading || 'Your display' }}</p>
      <p v-else-if="['subtitle', 'text'].includes(element.type)" class="display-element__text">{{ element.content || settings.message }}</p>
      <article v-else-if="element.type === 'offering'" class="display-element__offering">
        <template v-if="offeringFor(element.offering_id)">
          <strong>{{ offeringFor(element.offering_id).name }}</strong>
          <span>{{ money(offeringFor(element.offering_id).base_price) }}</span>
          <small>{{ offeringFor(element.offering_id).summary }}</small>
        </template>
        <span v-else class="display-element__placeholder">Choose an offering</span>
      </article>
      <div v-else-if="element.type === 'offering_group'" class="display-element__group">
        <article v-for="offering in offeringsFor(element)" :key="offering.public_id">
          <div><strong>{{ offering.name }}</strong><span>{{ money(offering.base_price) }}</span></div>
          <small>{{ offering.summary }}</small>
        </article>
        <span v-if="!offeringsFor(element).length" class="display-element__placeholder">Choose offerings</span>
      </div>
      <img v-else-if="element.type === 'image' && assetFor(element.asset_id)" :src="assetFor(element.asset_id).file_url" :alt="assetFor(element.asset_id).alt_text || ''" class="display-element__image" />
      <div v-else-if="element.type === 'image'" class="display-element__placeholder">Choose an image</div>
      <p v-else-if="element.type === 'social_footer'" class="display-element__social">{{ element.content || 'Connect with us' }}</p>

      <Button variant="ghost"
        v-if="editable && selectedId === element.id"
        type="button"
        class="display-element__resize"
        :aria-label="`Resize ${elementLabel(element.type)}`"
        @pointerdown.stop="startInteraction($event, element, 'resize')"
      />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  settings: { type: Object, required: true },
  offerings: { type: Array, default: () => [] },
  assets: { type: Array, default: () => [] },
  businessName: { type: String, default: '' },
  backgroundUrl: { type: String, default: '' },
  editable: { type: Boolean, default: false },
  selectedId: { type: String, default: '' },
  selectedSlideId: { type: String, default: '' },
  currency: { type: String, default: 'PHP' },
})

const emit = defineEmits(['select', 'change'])
const canvas = ref(null)
const activeSlideIndex = ref(0)
let interaction = null
let slideTimer = null

const builder = computed(() => props.settings.builder || { slides: [] })
const activeSlide = computed(() => builder.value.slides?.find((slide) => slide.id === props.selectedSlideId) || builder.value.slides?.[activeSlideIndex.value] || builder.value.slides?.[0])
const visibleElements = computed(() => [...(activeSlide.value?.elements || [])].filter((element) => element.visible !== false).sort((a, b) => Number(a.z_index || 0) - Number(b.z_index || 0)))
const offeringMap = computed(() => new Map(props.offerings.map((offering) => [String(offering.public_id), offering])))
const assetMap = computed(() => new Map(props.assets.map((asset) => [String(asset.public_id), asset])))
const fontFamilies = { manrope: 'Manrope, ui-sans-serif, sans-serif', newsreader: 'Newsreader, Georgia, serif', poppins: 'Poppins, ui-sans-serif, sans-serif', montserrat: 'Montserrat, ui-sans-serif, sans-serif', playfair: '"Playfair Display", Georgia, serif', system: 'ui-sans-serif, sans-serif' }

watch(() => [builder.value.slideshow_enabled, builder.value.slides?.length, builder.value.slides?.map((slide) => slide.duration_seconds).join(',')], restartSlideshow)
onMounted(restartSlideshow)
onBeforeUnmount(() => { stopInteraction(); if (slideTimer) window.clearTimeout(slideTimer) })

function clamp(value, minimum, maximum) { return Math.min(maximum, Math.max(minimum, Number(value) || 0)) }
function offeringFor(id) { return offeringMap.value.get(String(id)) }
function assetFor(id) { return assetMap.value.get(String(id)) }
function offeringsFor(element) {
  const ids = element.offering_ids?.length ? element.offering_ids : props.offerings.map((offering) => offering.public_id)
  return ids.slice(0, 8).map(offeringFor).filter(Boolean)
}
function elementLabel(type) { return ({ business: 'business name', heading: 'heading', subtitle: 'subtitle', text: 'text', offering: 'offering', offering_group: 'offering group', image: 'image', social_footer: 'social footer' }[type] || 'element') }
function money(value) { return new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency }).format(Number(value || 0)) }
function elementStyle(element) {
  const style = element.style || {}
  return {
    left: `${clamp(element.x, 0, 98)}%`,
    top: `${clamp(element.y, 0, 98)}%`,
    width: `${clamp(element.width, 4, 100)}%`,
    height: `${clamp(element.height, 4, 100)}%`,
    zIndex: Number(element.z_index || 1),
    transform: `rotate(${clamp(element.rotation, -180, 180)}deg)`,
    color: style.color || props.settings.foreground || '#f7f3ea',
    fontFamily: fontFamilies[style.font_family] || 'inherit',
    fontWeight: Number(style.font_weight || 700),
    textAlign: style.text_align || 'left',
    fontSize: `${clamp(style.font_size || 26, 10, 120) / 16}cqw`,
  }
}
function restartSlideshow() {
  if (slideTimer) window.clearTimeout(slideTimer)
  slideTimer = null
  activeSlideIndex.value = Math.min(activeSlideIndex.value, Math.max(0, (builder.value.slides?.length || 1) - 1))
  scheduleNextSlide()
}
function scheduleNextSlide() {
  if (props.editable || props.selectedSlideId || !builder.value.slideshow_enabled || (builder.value.slides?.length || 0) <= 1) return
  const seconds = clamp(activeSlide.value?.duration_seconds || 8, 3, 60)
  slideTimer = window.setTimeout(() => { activeSlideIndex.value = (activeSlideIndex.value + 1) % builder.value.slides.length; scheduleNextSlide() }, seconds * 1000)
}
function startInteraction(event, element, mode) {
  if (!canvas.value || event.button !== 0) return
  event.preventDefault()
  emit('select', element.id)
  const bounds = canvas.value.getBoundingClientRect()
  interaction = {
    pointerId: event.pointerId,
    element: structuredClone(element),
    mode,
    startX: event.clientX,
    startY: event.clientY,
    width: bounds.width,
    height: bounds.height,
  }
  event.currentTarget.setPointerCapture?.(event.pointerId)
  window.addEventListener('pointermove', continueInteraction)
  window.addEventListener('pointerup', stopInteraction, { once: true })
}
function continueInteraction(event) {
  if (!interaction || event.pointerId !== interaction.pointerId) return
  const dx = ((event.clientX - interaction.startX) / interaction.width) * 100
  const dy = ((event.clientY - interaction.startY) / interaction.height) * 100
  const next = { ...interaction.element }
  if (interaction.mode === 'resize') {
    next.width = clamp(interaction.element.width + dx, 4, 100 - interaction.element.x)
    next.height = clamp(interaction.element.height + dy, 4, 100 - interaction.element.y)
  } else {
    next.x = clamp(interaction.element.x + dx, 0, 100 - interaction.element.width)
    next.y = clamp(interaction.element.y + dy, 0, 100 - interaction.element.height)
  }
  emit('change', next)
}
function stopInteraction() {
  interaction = null
  window.removeEventListener('pointermove', continueInteraction)
  window.removeEventListener('pointerup', stopInteraction)
}
function moveWithKeyboard(event, element) {
  const direction = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[event.key]
  if (!direction) return
  event.preventDefault()
  const step = event.shiftKey ? 5 : 1
  emit('select', element.id)
  emit('change', { ...element, x: clamp(element.x + direction[0] * step, 0, 100 - element.width), y: clamp(element.y + direction[1] * step, 0, 100 - element.height) })
}
</script>

<style scoped>
.display-canvas { container-type: inline-size; position: relative; width: 100%; height: 100%; overflow: hidden; user-select: none; }
.display-canvas__background { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: .3; pointer-events: none; }
.display-element { position: absolute; min-width: 0; overflow: hidden; touch-action: none; }
.display-element--editable { cursor: move; outline: 1px dashed transparent; }
.display-element--editable:hover { outline-color: currentColor; }
.display-element--selected { outline: 2px solid hsl(var(--primary)); outline-offset: 2px; }
.display-element__business { font-size: .42em; letter-spacing: .14em; text-transform: uppercase; opacity: .72; }
.display-element__heading { font-family: var(--font-display); font-size: 1em; line-height: .96; }
.display-element__text { font-size: .44em; line-height: 1.5; opacity: .8; }
.display-element__offering { height: 100%; display: grid; grid-template-columns: 1fr auto; align-content: start; gap: .3em 1em; border-top: 1px solid currentColor; padding-top: .5em; }
.display-element__offering small { grid-column: 1 / -1; font-size: .34em; line-height: 1.4; opacity: .68; }
.display-element__group { display: grid; height: 100%; grid-template-columns: repeat(2, minmax(0, 1fr)); align-content: start; gap: .6em 1em; }
.display-element__group article { border-top: 1px solid currentColor; padding-top: .35em; }
.display-element__group article div { display: flex; justify-content: space-between; gap: .75em; }
.display-element__group small { display: block; margin-top: .25em; font-size: .32em; line-height: 1.35; opacity: .65; }
.display-element__image { width: 100%; height: 100%; object-fit: cover; }
.display-element__social { font-size: .36em; letter-spacing: .08em; text-transform: uppercase; }
.display-element__placeholder { display: grid; height: 100%; place-items: center; border: 1px dashed currentColor; font-size: .34em; opacity: .55; }
.display-element__resize { position: absolute; right: 2px; bottom: 2px; width: 16px; height: 16px; border: 2px solid currentColor; background: hsl(var(--background)); cursor: nwse-resize; }
</style>
