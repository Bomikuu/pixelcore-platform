<template>
  <div class="space-y-8">
    <Alert>
      <Palette class="h-4 w-4" aria-hidden="true" />
      <AlertTitle>One style, your identity</AlertTitle>
      <AlertDescription>
        Keep the {{ styleLabel }} art direction, or override its palette and type
        without changing the card’s composition.
      </AlertDescription>
    </Alert>

    <section class="space-y-5" aria-labelledby="card-palette-heading">
      <div class="flex items-start gap-3">
        <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
          <Paintbrush class="h-4 w-4" aria-hidden="true" />
        </div>
        <div>
          <h3 id="card-palette-heading" class="font-semibold">Color palette</h3>
          <p class="mt-1 text-sm leading-5 text-muted-foreground">
            Apply the style’s authored colors or create a palette shared by both sides.
          </p>
        </div>
      </div>

      <div class="space-y-2">
        <Label for="card-color-mode">Palette source</Label>
        <Select v-model="card.color_mode">
          <SelectTrigger id="card-color-mode">
            <SelectValue placeholder="Choose a palette source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="style">{{ stylePaletteLabel }}</SelectItem>
            <SelectItem value="custom">Custom card palette</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div
        v-if="card.color_mode === 'style'"
        class="flex items-center justify-between gap-5 border-y py-4"
      >
        <div>
          <p class="text-sm font-medium">{{ stylePaletteLabel }}</p>
          <p class="mt-1 text-sm text-muted-foreground">
            Switch to Custom card palette to edit every material color.
          </p>
        </div>
        <div class="flex shrink-0 -space-x-2" aria-hidden="true">
          <span
            v-for="color in stylePalette"
            :key="color"
            class="h-9 w-9 rounded-full border-2 border-background shadow-sm"
            :style="{ backgroundColor: color }"
          />
        </div>
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2">
        <div
          v-for="color in colorFields"
          :key="color.key"
          class="space-y-2"
          :class="color.key === 'ornament_color' ? 'sm:col-span-2' : ''"
        >
          <Label :for="`card-${color.key}`">{{ color.label }}</Label>
          <div class="flex gap-2">
            <Input
              :id="`card-${color.key}`"
              v-model="card[color.key]"
              type="color"
              class="h-10 w-14 shrink-0 cursor-pointer p-1"
              :aria-label="`${color.label} color picker`"
            />
            <Input
              v-model="card[color.key]"
              class="font-mono uppercase"
              maxlength="7"
              pattern="#[0-9A-Fa-f]{6}"
              :aria-label="`${color.label} hex value`"
            />
          </div>
        </div>
      </div>
    </section>

    <Separator />

    <section class="space-y-5" aria-labelledby="card-type-heading">
      <div class="flex items-start gap-3">
        <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
          <Type class="h-4 w-4" aria-hidden="true" />
        </div>
        <div>
          <h3 id="card-type-heading" class="font-semibold">Typography</h3>
          <p class="mt-1 text-sm leading-5 text-muted-foreground">
            Use the style pairing or choose separate fonts for brand, contact, and accent text.
          </p>
        </div>
      </div>

      <div class="space-y-2">
        <Label for="card-typography-mode">Typography source</Label>
        <Select v-model="card.typography_mode">
          <SelectTrigger id="card-typography-mode">
            <SelectValue placeholder="Choose a typography source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="style">Style typography</SelectItem>
            <SelectItem value="custom">Custom font pairing</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div v-if="card.typography_mode === 'style'" class="space-y-2">
        <template v-if="card.style === 'luxury'">
          <div class="border-y py-4">
            <p class="font-['Cormorant_Garamond'] text-2xl font-semibold">
              Cormorant Garamond
            </p>
            <p class="mt-1 font-['Great_Vibes'] text-xl text-muted-foreground">
              Great Vibes with Manrope details
            </p>
          </div>
        </template>
        <template v-else>
          <Label for="card-font-style">Style font</Label>
          <Select v-model="card.font_style">
            <SelectTrigger id="card-font-style">
              <SelectValue placeholder="Choose a style font" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="modern">Modern · Manrope</SelectItem>
              <SelectItem value="editorial">Editorial · Newsreader</SelectItem>
              <SelectItem value="geometric">Geometric · Montserrat</SelectItem>
              <SelectItem value="warm">Warm · Plus Jakarta Sans</SelectItem>
            </SelectContent>
          </Select>
        </template>
      </div>

      <div v-else class="space-y-5">
        <div class="grid gap-4 sm:grid-cols-2">
          <div class="space-y-2">
            <Label for="card-heading-font">Business name</Label>
            <Select v-model="card.heading_font">
              <SelectTrigger id="card-heading-font">
                <SelectValue placeholder="Choose a heading font" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="font in headingFonts"
                  :key="font.value"
                  :value="font.value"
                >
                  {{ font.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2">
            <Label for="card-body-font">Contact details</Label>
            <Select v-model="card.body_font">
              <SelectTrigger id="card-body-font">
                <SelectValue placeholder="Choose a body font" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="font in bodyFonts"
                  :key="font.value"
                  :value="font.value"
                >
                  {{ font.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-2 sm:col-span-2">
            <Label for="card-accent-font">Name and accent</Label>
            <Select v-model="card.accent_font">
              <SelectTrigger id="card-accent-font">
                <SelectValue placeholder="Choose an accent font" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="font in accentFonts"
                  :key="font.value"
                  :value="font.value"
                >
                  {{ font.label }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div class="border-y py-5">
          <div class="flex items-start gap-3">
            <div class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-muted text-primary">
              <FileType2 class="h-4 w-4" aria-hidden="true" />
            </div>
            <div class="min-w-0 flex-1">
              <p class="font-medium">Custom font</p>
              <p class="mt-1 text-sm leading-5 text-muted-foreground">
                Upload one self-contained WOFF2 file, up to 2 MB. It remains private to this business.
              </p>
              <p
                v-if="card.custom_font_asset_public_id"
                class="mt-2 text-sm font-medium text-primary"
              >
                Custom font ready
              </p>
            </div>
          </div>

          <Input
            class="mt-4 cursor-pointer"
            type="file"
            accept=".woff2,font/woff2"
            :disabled="uploading"
            aria-label="Upload a custom WOFF2 font"
            @change="selectFont"
          />
          <p v-if="fileError" class="mt-2 text-sm text-destructive" role="alert">
            {{ fileError }}
          </p>
          <div
            v-if="uploading"
            class="mt-3 flex items-center gap-2 text-sm text-muted-foreground"
          >
            <LoaderCircle class="h-4 w-4 animate-spin" aria-hidden="true" />
            Validating and uploading font…
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import {
  FileType2,
  LoaderCircle,
  Paintbrush,
  Palette,
  Type,
} from 'lucide-vue-next'

defineProps({
  uploading: { type: Boolean, default: false },
})

const emit = defineEmits(['upload'])
const card = defineModel('card', {
  type: Object,
  required: true,
})
const fileError = ref('')

const styleLabel = computed(() => ({
  signature: 'Signature',
  editorial: 'Editorial',
  studio: 'Studio',
  luxury: 'Luxury',
}[card.value.style] || 'selected'))
const stylePaletteLabel = computed(() =>
  card.value.style === 'luxury'
    ? 'Luxury black and metallic palette'
    : 'Business identity palette',
)
const stylePalette = computed(() => {
  if (card.value.style === 'luxury') return ['#0B0B0D', '#F8F1E1', '#C8A96B']
  return [
    card.value.theme?.primary_color || '#165B4C',
    card.value.theme?.secondary_color || '#17362F',
    card.value.theme?.accent_color || '#D8922B',
  ]
})

const colorFields = [
  { key: 'background_color', label: 'Background' },
  { key: 'text_color', label: 'Text' },
  { key: 'accent_color', label: 'Accent' },
  { key: 'border_color', label: 'Border' },
  { key: 'ornament_color', label: 'Ornament' },
]

const customFont = { value: 'custom', label: 'Custom uploaded font' }
const headingFonts = [
  { value: 'cormorant', label: 'Cormorant Garamond' },
  { value: 'playfair', label: 'Playfair Display' },
  { value: 'newsreader', label: 'Newsreader' },
  { value: 'manrope', label: 'Manrope' },
  { value: 'montserrat', label: 'Montserrat' },
  customFont,
]
const bodyFonts = [
  { value: 'manrope', label: 'Manrope' },
  { value: 'jakarta', label: 'Plus Jakarta Sans' },
  { value: 'montserrat', label: 'Montserrat' },
  { value: 'newsreader', label: 'Newsreader' },
  customFont,
]
const accentFonts = [
  { value: 'great_vibes', label: 'Great Vibes' },
  { value: 'allura', label: 'Allura' },
  { value: 'parisienne', label: 'Parisienne' },
  { value: 'alex_brush', label: 'Alex Brush' },
  { value: 'playball', label: 'Playball' },
  { value: 'lobster', label: 'Lobster' },
  { value: 'cormorant', label: 'Cormorant Garamond' },
  customFont,
]

function selectFont(event) {
  fileError.value = ''
  const file = event.target.files?.[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.woff2')) {
    fileError.value = 'Choose a .woff2 font file.'
    event.target.value = ''
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    fileError.value = 'Custom fonts must be 2 MB or smaller.'
    event.target.value = ''
    return
  }
  emit('upload', file)
  event.target.value = ''
}
</script>
