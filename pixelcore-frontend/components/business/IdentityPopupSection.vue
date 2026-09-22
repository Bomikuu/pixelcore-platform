<template>
  <div class="space-y-7">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 class="text-xl font-semibold">Storefront popup</h2>
        <p class="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
          Launch a campaign with a poster or a focused message. These settings apply to both shop layouts.
        </p>
      </div>
      <Button type="button" variant="outline" class="gap-2" @click="previewOpen = true">
        <Eye class="h-4 w-4" aria-hidden="true" />Preview popup
      </Button>
    </header>
    <label class="flex items-center justify-between gap-4 rounded-xl border p-4">
      <span>
        <span class="block font-semibold">Show on the storefront</span>
        <span class="mt-1 block text-xs text-muted-foreground">Save identity to publish your changes.</span>
      </span>
      <Switch v-model:checked="popup.enabled" />
    </label>

    <fieldset class="space-y-4">
      <legend class="mb-3 font-semibold">Presentation</legend>
      <div class="grid gap-3 sm:grid-cols-3">
        <Button
          v-for="layout in layouts"
          :key="layout.value"
          type="button"
          variant="outline"
          class="h-auto flex-col items-start gap-3 whitespace-normal p-4 text-left"
          :class="popup.layout === layout.value ? 'border-primary bg-secondary' : ''"
          :aria-pressed="popup.layout === layout.value"
          @click="popup.layout = layout.value"
        >
          <component :is="layout.icon" class="h-5 w-5 text-primary" aria-hidden="true" />
          <span class="font-semibold">{{ layout.label }}</span>
          <span class="text-xs font-normal leading-5 text-muted-foreground">{{ layout.description }}</span>
        </Button>
      </div>
      <div class="grid gap-4 sm:grid-cols-2">
        <label>
          <span class="field-label">Size</span>
          <Select v-model="popup.size">
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="small">Small</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="large">Large</SelectItem>
            </SelectContent>
          </Select>
        </label>
        <label>
          <span class="field-label">Content mode</span>
          <Select v-model="popup.mode">
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="standard">Visual editor</SelectItem>
              <SelectItem value="custom">Existing custom HTML & CSS</SelectItem>
            </SelectContent>
          </Select>
        </label>
      </div>
    </fieldset>

    <fieldset class="grid gap-4 border-t pt-6 sm:grid-cols-2">
      <legend class="pr-3 font-semibold">Campaign content</legend>
      <label class="sm:col-span-2">
        <span class="field-label">Title / accessible poster description</span>
        <Input v-model="popup.title" maxlength="120" placeholder="Describe this promotion" />
      </label>
      <template v-if="popup.mode === 'standard'">
        <label v-if="popup.layout !== 'poster'" class="sm:col-span-2">
          <span class="field-label">Description</span>
          <Textarea v-model="popup.description" maxlength="800" rows="4" />
        </label>
        <label class="sm:col-span-2">
          <span class="field-label">Campaign image</span>
          <Select :model-value="popup.asset_id || 'none'" @update:model-value="popup.asset_id = $event === 'none' ? '' : $event">
            <SelectTrigger><SelectValue placeholder="Choose an image" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No image</SelectItem>
              <SelectItem v-for="asset in imageAssets" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</SelectItem>
            </SelectContent>
          </Select>
          <span class="mt-2 block text-xs leading-5 text-muted-foreground">
            Upload artwork in Site → Media. Image-only posters preserve the full image without cropping; transparent PNG artwork is supported.
          </span>
        </label>
        <img v-if="selectedAsset" :src="selectedAsset.file_url" alt="Selected campaign artwork" class="max-h-64 w-full rounded-lg bg-secondary object-contain sm:col-span-2" />
        <p v-if="popup.layout === 'poster' && !selectedAsset" class="text-sm text-muted-foreground sm:col-span-2">Choose a campaign image to use the poster layout. Until then, the popup shows your text.</p>
        <label>
          <span class="field-label">{{ popup.layout === 'poster' ? 'Poster link description' : 'Button label' }}</span>
          <Input v-model="popup.cta_text" maxlength="80" placeholder="Shop the collection" />
        </label>
        <label>
          <span class="field-label">Destination</span>
          <Input v-model="popup.cta_url" placeholder="/shop" />
        </label>
      </template>
      <template v-else>
        <label class="sm:col-span-2">
          <span class="field-label">Custom HTML</span>
          <Textarea v-model="popup.custom_html" rows="8" class="font-mono text-xs" />
        </label>
        <label class="sm:col-span-2">
          <span class="field-label">Scoped CSS</span>
          <Textarea v-model="popup.custom_css" rows="8" class="font-mono text-xs" />
        </label>
        <p class="text-xs leading-5 text-muted-foreground sm:col-span-2">Existing sanitization and isolated-frame rules apply. Scripts, forms, imports, external CSS URLs, and executable content are not allowed.</p>
      </template>
      <label><span class="field-label">Background</span><Input v-model="popup.background_color" type="color" class="h-11 p-1" /></label>
      <label><span class="field-label">Text color</span><Input v-model="popup.text_color" type="color" class="h-11 p-1" /></label>
      <label>
        <span class="field-label">Corners</span>
        <Select v-model="popup.border_radius">
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Sharp</SelectItem>
            <SelectItem value="small">Slightly rounded</SelectItem>
            <SelectItem value="medium">Rounded</SelectItem>
            <SelectItem value="large">Soft</SelectItem>
            <SelectItem value="pill">Extra rounded</SelectItem>
          </SelectContent>
        </Select>
      </label>
    </fieldset>

    <fieldset class="grid gap-4 border-t pt-6 sm:grid-cols-2">
      <legend class="pr-3 font-semibold">When it appears</legend>
      <label>
        <span class="field-label">Display frequency</span>
        <Select v-model="popup.frequency">
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="session">Once per browser session</SelectItem>
            <SelectItem value="daily">Once every 24 hours</SelectItem>
            <SelectItem value="always">Every eligible page visit</SelectItem>
          </SelectContent>
        </Select>
      </label>
      <label>
        <span class="field-label">Delay in seconds</span>
        <Input v-model.number="popup.display_delay" type="number" min="0" max="120" />
      </label>
      <label class="flex items-center justify-between gap-3 rounded-lg border p-4">
        <span class="text-sm font-medium">Home page only</span>
        <Switch v-model:checked="popup.home_only" />
      </label>
      <label class="flex items-center justify-between gap-3 rounded-lg border p-4">
        <span class="text-sm font-medium">Allow dismissal</span>
        <Switch v-model:checked="popup.dismissible" />
      </label>
      <p class="text-xs leading-5 text-muted-foreground sm:col-span-2">
        Preview works even when the popup is disabled and never marks it as seen. Saving changed campaign settings allows visitors to see the new version.
      </p>
    </fieldset>
    <StorefrontPopup v-if="previewOpen" :identity="previewIdentity" base="" preview @closed="previewOpen = false" />
  </div>
</template>

<script setup>
import { Eye, Image, PanelTop, PanelsLeftBottom } from 'lucide-vue-next'
import StorefrontPopup from '@/components/site/StorefrontPopup.vue'

const props = defineProps({
  form: { type: Object, required: true },
  assets: { type: Array, default: () => [] },
})
const popup = computed(() => props.form.branding.storefront.popup)
const previewOpen = ref(false)
const imageAssets = computed(() => props.assets.filter((asset) => asset.asset_type === 'image' && asset.processing_status === 'ready'))
const selectedAsset = computed(() => imageAssets.value.find((asset) => asset.public_id === popup.value.asset_id))
const previewIdentity = computed(() => ({
  ...props.form,
  branding_assets: {
    ...props.form.branding_assets,
    ...Object.fromEntries(props.assets.map((asset) => [asset.public_id, { ...asset, url: asset.file_url }])),
  },
}))
const layouts = [
  { value: 'image_top', label: 'Image + message', icon: PanelTop, description: 'Artwork above a headline and action.' },
  { value: 'split', label: 'Split layout', icon: PanelsLeftBottom, description: 'Image and message side by side.' },
  { value: 'poster', label: 'Image-only poster', icon: Image, description: 'Let your campaign artwork fill the popup.' },
]
</script>
