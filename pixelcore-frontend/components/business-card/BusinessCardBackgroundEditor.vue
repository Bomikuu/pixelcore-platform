<template>
  <div class="space-y-6">
    <div>
      <Label class="mb-3 block">Background source</Label>
      <div class="grid gap-3 sm:grid-cols-2">
        <Button
          v-for="option in backgroundOptions"
          :key="option.value"
          type="button"
          variant="outline"
          class="h-auto min-h-20 justify-start gap-3 whitespace-normal p-4 text-left"
          :class="card.background_type === option.value ? selectedClass : ''"
          :aria-pressed="card.background_type === option.value"
          @click="chooseBackground(option.value)"
        >
          <component
            :is="option.icon"
            class="h-5 w-5 shrink-0 text-primary"
            aria-hidden="true"
          />
          <span>
            <span class="block font-semibold">{{ option.label }}</span>
            <span class="mt-1 block text-xs font-normal text-muted-foreground">
              {{ option.description }}
            </span>
          </span>
        </Button>
      </div>
    </div>

    <Alert v-if="card.background_type === 'generated'">
      <Shapes class="h-4 w-4" aria-hidden="true" />
      <AlertTitle>Built from your identity</AlertTitle>
      <AlertDescription>
        The selected template combines your brand colors with a deliberate geometric
        composition. No uploaded artwork is required.
      </AlertDescription>
    </Alert>

    <template v-else>
      <BusinessCardImageBackgroundControls
        v-model:card="card"
        :assets="assets"
        :uploading="uploading"
        @upload="$emit('upload', $event)"
      />

      <Alert>
        <ShieldCheck class="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Readability stays protected</AlertTitle>
        <AlertDescription>
          Contact details sit on a controlled surface, while each template reduces its
          generated accents when photography is present.
        </AlertDescription>
      </Alert>
    </template>
  </div>
</template>

<script setup>
import { Image as ImageIcon, Shapes, ShieldCheck } from 'lucide-vue-next'

const props = defineProps({
  assets: { type: Array, default: () => [] },
  uploading: { type: Boolean, default: false },
})
defineEmits(['upload'])

const card = defineModel('card', { type: Object, required: true })
const selectedClass = 'border-primary bg-primary/5 ring-1 ring-primary'
const backgroundOptions = [
  {
    value: 'generated',
    label: 'Generated pattern',
    description: 'Brand-led geometry created without an image.',
    icon: Shapes,
  },
  {
    value: 'image',
    label: 'Image background',
    description: 'Use restrained photography, texture, or artwork.',
    icon: ImageIcon,
  },
]

function chooseBackground(value) {
  card.value.background_type = value
  if (value !== 'image') return
  const selected = props.assets.find(
    (asset) => asset.public_id === card.value.background_asset_public_id,
  )
  card.value.background_image_url = selected?.file_url || ''
}
</script>
