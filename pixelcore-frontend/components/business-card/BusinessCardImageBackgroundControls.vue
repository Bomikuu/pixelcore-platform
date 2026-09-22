<template>
  <div class="space-y-6">
    <div
      class="relative aspect-[16/9] overflow-hidden rounded-xl border bg-muted"
      :style="previewStyle"
    >
      <img
        v-if="selectedAsset"
        :src="selectedAsset.file_url"
        :alt="selectedAsset.alt_text || selectedAsset.title"
        class="h-full w-full"
        :class="card.background_image_fit === 'contain' ? 'object-contain' : 'object-cover'"
        :style="{ objectPosition: card.background_image_position || 'center' }"
      />
      <div
        v-else
        class="flex h-full flex-col items-center justify-center gap-3 px-6 text-center text-muted-foreground"
      >
        <ImageIcon class="h-8 w-8" aria-hidden="true" />
        <p class="text-sm font-medium">Choose an image or upload brand artwork</p>
        <p class="max-w-sm text-xs leading-5">
          Until an image is selected, the generated pattern remains active.
        </p>
      </div>
    </div>

    <div class="grid gap-5 sm:grid-cols-2">
      <div class="space-y-2">
        <Label for="card-background-library">Media library</Label>
        <Select
          :model-value="card.background_asset_public_id || 'none'"
          @update:model-value="selectAsset"
        >
          <SelectTrigger id="card-background-library">
            <SelectValue placeholder="Choose an image" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">No image selected</SelectItem>
            <SelectItem
              v-for="asset in imageAssets"
              :key="asset.public_id"
              :value="asset.public_id"
            >
              {{ asset.title }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="space-y-2">
        <Label for="card-background-upload">Upload or replace</Label>
        <Input
          id="card-background-upload"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/avif"
          :disabled="uploading"
          @change="handleUpload"
        />
        <p class="text-xs leading-5 text-muted-foreground">
          JPG, PNG, WebP or AVIF up to 8 MB.
        </p>
      </div>
    </div>

    <p v-if="uploading" role="status" class="flex items-center gap-2 text-sm">
      <LoaderCircle class="h-4 w-4 animate-spin" aria-hidden="true" />
      Uploading background image…
    </p>
    <p v-if="uploadError" role="alert" class="text-sm text-destructive">
      {{ uploadError }}
    </p>

    <div class="grid gap-5 border-t pt-6 sm:grid-cols-2">
      <BackgroundSelect
        v-model="card.background_apply_to"
        label="Apply to"
        :options="applyOptions"
      />
      <BackgroundSelect
        v-model="card.background_image_fit"
        label="Image fit"
        :options="fitOptions"
      />
      <BackgroundSelect
        v-model="card.background_image_position"
        label="Image position"
        :options="positionOptions"
      />
      <BackgroundSelect
        v-model="card.background_overlay"
        label="Readability overlay"
        :options="overlayOptions"
      />
    </div>

    <div v-if="card.background_overlay !== 'none'">
      <Label class="mb-3 block">Overlay strength</Label>
      <div class="grid grid-cols-3 gap-2">
        <Button
          v-for="strength in strengthOptions"
          :key="strength"
          type="button"
          variant="outline"
          :aria-pressed="card.background_overlay_strength === strength"
          :class="card.background_overlay_strength === strength ? selectedClass : ''"
          @click="card.background_overlay_strength = strength"
        >
          {{ capitalize(strength) }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Image as ImageIcon, LoaderCircle } from 'lucide-vue-next'

const props = defineProps({
  assets: { type: Array, default: () => [] },
  uploading: { type: Boolean, default: false },
})
const emit = defineEmits(['upload'])
const card = defineModel('card', { type: Object, required: true })
const uploadError = ref('')
const selectedClass = 'border-primary bg-primary/5 ring-1 ring-primary'

const applyOptions = [
  { value: 'front', label: 'Front only' },
  { value: 'back', label: 'Back only' },
  { value: 'both', label: 'Both sides' },
]
const fitOptions = [
  { value: 'cover', label: 'Cover' },
  { value: 'contain', label: 'Contain' },
]
const positionOptions = ['center', 'top', 'bottom', 'left', 'right'].map(
  (value) => ({ value, label: capitalize(value) }),
)
const overlayOptions = [
  { value: 'none', label: 'None' },
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'brand', label: 'Brand color' },
]
const strengthOptions = ['low', 'medium', 'high']
const imageAssets = computed(() =>
  props.assets.filter(
    (asset) => asset.asset_type === 'image' && asset.processing_status === 'ready',
  ),
)
const selectedAsset = computed(() =>
  imageAssets.value.find(
    (asset) => asset.public_id === card.value.background_asset_public_id,
  ),
)
const previewStyle = computed(() => ({
  backgroundColor: card.value.theme?.background_color || undefined,
}))

function selectAsset(value) {
  const publicId = value === 'none' ? null : value
  const asset = imageAssets.value.find((item) => item.public_id === publicId)
  card.value.background_asset_public_id = publicId
  card.value.background_image_url = asset?.file_url || ''
}

function handleUpload(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  uploadError.value = ''
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/avif']
  if (!allowedTypes.includes(file.type) || file.size > 8 * 1024 * 1024) {
    uploadError.value = 'Choose a JPG, PNG, WebP or AVIF image under 8 MB.'
    return
  }
  emit('upload', file)
}

function capitalize(value) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}
</script>
