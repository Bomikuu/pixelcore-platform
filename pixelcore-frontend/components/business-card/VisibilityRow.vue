<template>
  <div class="flex items-start justify-between gap-5 border-b py-4 first:pt-0 last:border-b-0">
    <div class="flex min-w-0 items-start gap-3">
      <component :is="iconComponent" class="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
      <div>
        <Label :for="controlId" class="leading-5">{{ title }}</Label>
        <p class="mt-1 text-sm leading-5 text-muted-foreground">{{ description }}</p>
      </div>
    </div>
    <Switch
      :id="controlId"
      v-model:checked="model"
      :disabled="disabled"
      :aria-label="title"
    />
  </div>
</template>

<script setup>
import { Mail, MapPin, Phone, QrCode, Share2 } from 'lucide-vue-next'

const props = defineProps({
  icon: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  disabled: { type: Boolean, default: false },
})

const model = defineModel({ type: Boolean, default: false })
const controlId = useId()
const icons = {
  mail: Mail,
  phone: Phone,
  'map-pin': MapPin,
  'qr-code': QrCode,
  share: Share2,
}
const iconComponent = computed(() => icons[props.icon] || QrCode)
</script>
