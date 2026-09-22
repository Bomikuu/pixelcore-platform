<template>
  <section class="space-y-6 border-b pb-8" aria-labelledby="marketplace-hero-settings">
    <header>
      <h2 id="marketplace-hero-settings" class="text-xl font-semibold">Marketplace home hero</h2>
      <p class="mt-2 text-sm leading-6 text-muted-foreground">
        Lead with a campaign, product search, or both. Your header search remains available in every layout.
      </p>
    </header>
    <div class="grid gap-3 sm:grid-cols-3">
      <Button
        v-for="option in layouts"
        :key="option.value"
        type="button"
        variant="outline"
        class="h-auto flex-col items-start gap-3 whitespace-normal p-4 text-left"
        :class="settings.hero_layout === option.value ? 'border-primary bg-secondary' : ''"
        :aria-pressed="settings.hero_layout === option.value"
        @click="settings.hero_layout = option.value"
      >
        <component :is="option.icon" class="h-5 w-5 text-primary" aria-hidden="true" />
        <span class="font-semibold">{{ option.label }}</span>
        <span class="text-xs font-normal leading-5 text-muted-foreground">{{ option.description }}</span>
      </Button>
    </div>
    <div v-if="settings.hero_layout !== 'carousel'" class="grid gap-4">
      <label>
        <span class="field-label">Search heading</span>
        <Input v-model="settings.search_heading" maxlength="180" />
      </label>
      <label>
        <span class="field-label">Search supporting text</span>
        <Textarea v-model="settings.search_description" maxlength="600" placeholder="Leave empty to use the store introduction." />
      </label>
    </div>
    <template v-if="settings.hero_layout !== 'search'">
      <div class="grid gap-4 sm:grid-cols-2">
        <label>
          <span class="field-label">Carousel width</span>
          <Select v-model="settings.carousel_width">
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="full">Edge to edge</SelectItem>
              <SelectItem value="contained">Contained with margins</SelectItem>
            </SelectContent>
          </Select>
        </label>
        <label>
          <span class="field-label">Carousel height</span>
          <Select v-model="settings.carousel_height">
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="compact">Compact</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="tall">Tall</SelectItem>
              <SelectItem value="screen">Full screen</SelectItem>
            </SelectContent>
          </Select>
        </label>
        <label class="flex items-center justify-between gap-3 rounded-lg border p-3">
          <span class="text-sm font-medium">Autoplay slides</span>
          <Switch v-model:checked="settings.autoplay" />
        </label>
        <label>
          <span class="field-label">Seconds per slide</span>
          <Input v-model.number="settings.interval" type="number" min="4" max="30" :disabled="!settings.autoplay" />
        </label>
      </div>
      <HeroSlidesEditor v-model="settings.slides" :assets="assets" @uploaded="$emit('uploaded', $event)" />
      <p class="text-sm leading-6 text-muted-foreground">
        Without custom slides, the carousel uses the existing home-page hero or published product images.
        Add at least two slides for carousel navigation. Existing CMS content is not overwritten.
      </p>
      <div v-if="settings.slides.length" class="overflow-hidden rounded-xl border">
        <div class="flex items-center gap-2 border-b px-4 py-3 text-sm font-semibold">
          <Eye class="h-4 w-4" aria-hidden="true" />Carousel preview
        </div>
        <CustomHeroCarousel
          :key="`${settings.interval}:${settings.carousel_height}`"
          :slides="settings.slides"
          :assets="previewAssets"
          :autoplay="settings.autoplay"
          :interval="settings.interval"
          height="compact"
          preview
        />
      </div>
    </template>
  </section>
</template>

<script setup>
import { Eye, GalleryHorizontal, PanelsTopLeft, Search } from 'lucide-vue-next'
import HeroSlidesEditor from '@/components/site/HeroSlidesEditor.vue'
import CustomHeroCarousel from '@/components/site/CustomHeroCarousel.vue'

const props = defineProps({
  form: { type: Object, required: true },
  assets: { type: Array, default: () => [] },
})
defineEmits(['uploaded'])
const settings = computed(() => props.form.branding.storefront.marketplace)
const previewAssets = computed(() => Object.fromEntries(props.assets.map((asset) => [
  asset.public_id,
  { ...asset, url: asset.file_url },
])))
const layouts = [
  { value: 'carousel', label: 'Campaign carousel', icon: GalleryHorizontal, description: 'Large visuals directly below the header.' },
  { value: 'both', label: 'Integrated carousel', icon: PanelsTopLeft, description: 'Place product search directly inside the campaign.' },
  { value: 'search', label: 'Search-led', icon: Search, description: 'Keep search as the main introduction.' },
]
</script>
