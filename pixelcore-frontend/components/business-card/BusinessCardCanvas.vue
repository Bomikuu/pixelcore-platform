<template>
  <div class="w-full">
    <div
      class="business-card-stage mx-auto"
      :class="card.orientation === 'portrait' ? 'max-w-[25rem]' : 'max-w-[46rem]'"
    >
      <Button
        v-if="controls"
        type="button"
        variant="ghost"
        class="business-card-shell block h-auto w-full whitespace-normal rounded-none bg-transparent p-0 text-left hover:bg-transparent"
        :class="cardShellClasses"
        :aria-label="flipped ? 'Show the brand side' : 'Show the contact side'"
        :aria-pressed="flipped"
        @click="flipped = !flipped"
      >
        <BusinessCardFace
          :card="visibleCard"
          side="front"
          :qr-data-url="qrDataUrl"
          :qr-label="qrLabel"
        />
        <BusinessCardFace
          :card="visibleCard"
          side="back"
          :qr-data-url="qrDataUrl"
          :qr-label="qrLabel"
        />
      </Button>
      <div v-else class="business-card-shell" :class="cardShellClasses">
        <BusinessCardFace
          :card="visibleCard"
          side="front"
          :qr-data-url="qrDataUrl"
          :qr-label="qrLabel"
        />
        <BusinessCardFace
          :card="visibleCard"
          side="back"
          :qr-data-url="qrDataUrl"
          :qr-label="qrLabel"
        />
      </div>
    </div>

    <p v-if="controls" class="sr-only" aria-live="polite">
      {{ flipped ? 'Contact side shown.' : 'Brand side shown.' }}
    </p>

    <div v-if="printable" class="business-card-print hidden print:grid">
      <div
        class="business-card-print-face"
        :class="card.orientation === 'portrait' ? 'business-card-print-face--portrait' : ''"
      >
        <BusinessCardFace
          :card="visibleCard"
          side="front"
          :qr-data-url="qrDataUrl"
          :qr-label="qrLabel"
        />
      </div>
      <div
        class="business-card-print-face"
        :class="card.orientation === 'portrait' ? 'business-card-print-face--portrait' : ''"
      >
        <BusinessCardFace
          :card="visibleCard"
          side="back"
          :qr-data-url="qrDataUrl"
          :qr-label="qrLabel"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  card: { type: Object, required: true },
  controls: { type: Boolean, default: true },
  printable: { type: Boolean, default: false },
  qrFallbackUrl: { type: String, default: '' },
})

const flipped = ref(false)
const qrDataUrl = ref('')
const customFontFamily = ref('')
let qrGeneration = 0
let fontGeneration = 0
let activeFontFace = null

const visibleCard = computed(() => ({
  ...props.card,
  email: props.card.show_email === false ? '' : props.card.email,
  phone: props.card.show_phone === false ? '' : props.card.phone,
  business_address: props.card.show_business_address === false
    ? ''
    : props.card.business_address,
  _custom_font_family: customFontFamily.value,
}))
const cardShellClasses = computed(() => [
  props.card.orientation === 'portrait' ? 'aspect-[2/3.5]' : 'aspect-[3.5/2]',
  flipped.value ? 'business-card-shell--flipped' : '',
])
const qrTargetUrl = computed(() =>
  props.card.business_website_url || props.qrFallbackUrl,
)
const qrLabel = computed(() =>
  props.card.business_website_url ? 'Visit website' : 'Open this card',
)

watch(
  qrTargetUrl,
  generateQr,
  { immediate: true },
)

watch(
  () => props.card.custom_font_url,
  loadCustomFont,
  { immediate: true },
)

onBeforeUnmount(() => {
  fontGeneration += 1
  releaseCustomFont()
})

async function generateQr(url) {
  const generation = ++qrGeneration
  qrDataUrl.value = ''
  if (!url || !import.meta.client) return

  try {
    const module = await import('qrcode')
    const qrCode = module.default || module
    const value = await qrCode.toDataURL(url, {
      width: 256,
      margin: 1,
      errorCorrectionLevel: 'M',
      color: { dark: '#102A2A', light: '#FFFFFF' },
    })
    if (generation === qrGeneration) qrDataUrl.value = value
  } catch {
    if (generation === qrGeneration) qrDataUrl.value = ''
  }
}

function releaseCustomFont() {
  if (activeFontFace && import.meta.client && document.fonts) {
    document.fonts.delete(activeFontFace)
  }
  activeFontFace = null
  customFontFamily.value = ''
}

async function loadCustomFont(url) {
  const generation = ++fontGeneration
  releaseCustomFont()
  if (!url || !import.meta.client || !window.FontFace || !document.fonts) return

  try {
    const absoluteUrl = new URL(url, window.location.origin).href
    const identifier = String(props.card.public_id || 'draft').replace(/[^a-zA-Z0-9-]/g, '')
    const family = `PixelCoreCard-${identifier}`
    const fontFace = new window.FontFace(
      family,
      `url(${JSON.stringify(absoluteUrl)}) format("woff2")`,
      { display: 'swap' },
    )
    await fontFace.load()
    if (generation !== fontGeneration) return
    document.fonts.add(fontFace)
    activeFontFace = fontFace
    customFontFamily.value = family
  } catch {
    if (generation === fontGeneration) releaseCustomFont()
  }
}
</script>

<style scoped>
.business-card-stage {
  container-type: inline-size;
  perspective: 1400px;
}

.business-card-shell {
  position: relative;
  width: 100%;
  transform-style: preserve-3d;
  transition:
    transform 520ms cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 180ms ease-out;
  box-shadow: 0 1.75rem 4rem -2rem rgb(16 42 42 / 45%);
}

button.business-card-shell {
  cursor: pointer;
  outline-offset: 0.35rem;
}

button.business-card-shell:hover {
  box-shadow: 0 2rem 4.5rem -2rem rgb(16 42 42 / 55%);
}

button.business-card-shell:focus-visible {
  box-shadow:
    0 0 0 0.2rem hsl(var(--background)),
    0 0 0 0.35rem hsl(var(--ring)),
    0 1.75rem 4rem -2rem rgb(16 42 42 / 45%);
}

.business-card-shell--flipped {
  transform: rotateY(180deg);
}

@media (prefers-reduced-motion: reduce) {
  .business-card-shell {
    transition: none;
  }
}

@media print {
  .business-card-stage {
    display: none;
  }

  .business-card-print {
    grid-template-columns: 1fr;
    place-items: center;
    gap: 12mm;
  }

  .business-card-print-face {
    position: relative;
    width: 3.5in;
    height: 2in;
    overflow: hidden;
    break-after: page;
    container-type: inline-size;
    print-color-adjust: exact;
  }

  .business-card-print-face--portrait {
    width: 2in;
    height: 3.5in;
  }
}
</style>
