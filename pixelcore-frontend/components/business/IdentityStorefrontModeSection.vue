<template>
  <div class="space-y-8">
    <header>
      <h2 class="text-xl font-extrabold">Storefront mode</h2>
      <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Choose the shopping composition that fits the brand. The mode controls layout; colors, type, and media remain editable.</p>
    </header>

    <div class="grid gap-4 sm:grid-cols-2">
      <Button
        v-for="mode in modes"
        :key="mode.id"
        type="button"
        variant="outline"
        class="h-auto min-h-56 items-stretch justify-start whitespace-normal p-0 text-left"
        :class="activeMode === mode.id ? 'border-primary ring-2 ring-primary/20' : ''"
        :aria-pressed="activeMode === mode.id"
        @click="storefront.mode = mode.id"
      >
        <span class="flex w-full flex-col p-5">
          <span class="flex items-start justify-between gap-4">
            <span class="grid h-10 w-10 place-items-center rounded-[var(--button-radius)] bg-secondary text-foreground"><component :is="mode.icon" class="h-5 w-5" /></span>
            <Badge v-if="activeMode === mode.id">Selected</Badge>
          </span>
          <strong class="mt-5 text-lg">{{ mode.name }}</strong>
          <span class="mt-2 text-sm font-normal leading-6 text-muted-foreground">{{ mode.description }}</span>
          <span class="mt-auto pt-5 text-xs font-bold text-primary">{{ mode.layout }}</span>
        </span>
      </Button>
    </div>

    <Alert>
      <Palette class="h-4 w-4" />
      <AlertTitle>Layout and brand styling stay separate</AlertTitle>
      <AlertDescription>Changing mode preserves your current identity. Apply the recommended styling only when you want a considered starting palette and type system.</AlertDescription>
    </Alert>

    <section class="border-t pt-7" aria-labelledby="mode-preset-heading">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 id="mode-preset-heading" class="font-extrabold">{{ activeModeName }} styling preset</h3>
          <p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">Updates colors, typography, component shape, storefront canvas, and footer. Every value remains editable in the other settings sections.</p>
        </div>
        <Button type="button" variant="outline" class="shrink-0" @click="applyPreset"><WandSparkles class="h-4 w-4" />Apply recommended styling</Button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { Gem, Palette, ShoppingBag, WandSparkles } from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toast'

const props = defineProps({ form: { type: Object, required: true } })
const storefront = computed(() => props.form.branding.storefront)
const activeMode = computed(() => storefront.value.mode || 'default')
const activeModeName = computed(() => modes.find((mode) => mode.id === activeMode.value)?.name || 'Default')
const modes = [
  { id: 'default', name: 'Default', icon: ShoppingBag, description: 'The current PixelCore shopping experience with focused product cards, filters, thumbnail galleries, and balanced content density.', layout: 'Flexible grids and focused product detail' },
  { id: 'luxury', name: 'Luxury', icon: Gem, description: 'An image-led editorial storefront with edge-to-edge collection tiles, collection heroes, and a scroll gallery beside sticky purchasing details.', layout: 'Full-width editorial collection and sticky detail' },
]

const presets = {
  default: {
    colors: { primary_color: '#165B4C', secondary_color: '#17362F', accent_color: '#D8922B', background_color: '#FAF9F5', text_color: '#17312B', muted_text_color: '#5D6D68', link_color: '#165B4C' },
    typography: { primary_font: 'Manrope', heading_font: 'Newsreader', body_weight: 400, heading_weight: 700, base_font_size: '16px' },
    style: { button_radius: 'medium', card_radius: 'large', input_radius: 'medium', modal_radius: 'large', border_width: 'thin', shadow_intensity: 'subtle', content_width: 'wide' },
    background: { type: 'color', color: '#FAF9F5', gradient_from: '#FAF9F5', gradient_to: '#E7F0EC', gradient_angle: 135, asset_id: '' },
    footer: { background_color: '#17362F', text_color: '#FFFFFF', link_color: '#D9F85D' },
  },
  luxury: {
    colors: { primary_color: '#202321', secondary_color: '#D8DAD7', accent_color: '#3D5748', background_color: '#F4F5F3', text_color: '#202321', muted_text_color: '#626762', link_color: '#202321' },
    typography: { primary_font: 'Manrope', heading_font: 'Playfair Display', body_weight: 400, heading_weight: 600, base_font_size: '16px' },
    style: { button_radius: 'none', card_radius: 'none', input_radius: 'none', modal_radius: 'none', border_width: 'thin', shadow_intensity: 'none', content_width: 'full' },
    background: { type: 'color', color: '#F4F5F3', gradient_from: '#F4F5F3', gradient_to: '#D8DAD7', gradient_angle: 135, asset_id: '' },
    footer: { background_color: '#202321', text_color: '#F4F5F3', link_color: '#F4F5F3' },
  },
}

function applyPreset() {
  const preset = presets[activeMode.value]
  Object.assign(props.form.branding, preset.colors)
  Object.assign(props.form.branding.typography, preset.typography)
  Object.assign(props.form.branding.style, preset.style)
  Object.assign(props.form.branding.storefront.background, preset.background)
  Object.assign(props.form.branding.storefront.footer, preset.footer)
  toast({ title: `${activeModeName.value} styling applied`, description: 'Review the live preview, then save identity to publish these changes.' })
}
</script>
