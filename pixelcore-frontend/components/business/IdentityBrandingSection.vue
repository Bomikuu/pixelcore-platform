<template>
  <div class="space-y-8">
    <header><h2 class="text-xl font-extrabold">Branding</h2><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">The recognizable name and imagery shared by your storefront, workspace, receipts, and displays.</p></header>

    <fieldset class="space-y-4">
      <legend class="font-extrabold">Brand images</legend>
      <div class="grid gap-4 sm:grid-cols-2">
        <article v-for="image in imageFields" :key="image.key" class="overflow-hidden rounded-[var(--card-radius)] border bg-background" :class="image.key === 'cover_image' ? 'sm:col-span-2' : ''">
          <div class="relative grid place-items-center overflow-hidden bg-muted" :class="image.previewClass">
            <img v-if="imageSource(image.key)" :src="imageSource(image.key)" :alt="`${image.label} preview`" class="h-full w-full" :class="image.fitClass" />
            <div v-else class="grid place-items-center gap-2 text-center text-muted-foreground"><component :is="image.icon" class="h-7 w-7" aria-hidden="true" /><span class="text-xs font-semibold">No {{ image.label.toLowerCase() }} uploaded</span></div>
            <Badge v-if="mediaFiles[image.key]" class="absolute left-3 top-3">New upload</Badge>
            <Button as-child :variant="imageSource(image.key) ? 'secondary' : 'default'" size="sm" class="absolute right-3 top-3"><label class="cursor-pointer" :for="`identity-${image.key}`"><Upload class="h-4 w-4" /> {{ imageSource(image.key) ? 'Replace' : 'Upload' }}</label></Button>
            <Input :id="`identity-${image.key}`" class="sr-only" type="file" accept="image/jpeg,image/png,image/webp" @change="$emit('select-image', $event, image.key)" />
          </div>
          <div class="p-4"><h3 class="text-sm font-extrabold">{{ image.label }}</h3><p class="mt-1 text-xs leading-5 text-muted-foreground">{{ image.guidance }}</p><Button v-if="mediaFiles[image.key]" variant="ghost" size="sm" type="button" class="mt-2 px-0" @click="$emit('clear-image', image.key)">Undo new upload</Button></div>
        </article>
      </div>
      <p class="text-xs leading-5 text-muted-foreground">JPG, PNG, or WebP, up to 5 MB. Use a square logo and favicon and a wide cover image.</p>
    </fieldset>

    <fieldset class="space-y-4 border-t pt-7">
      <legend class="font-extrabold">Business profile</legend>
      <div class="grid gap-4 sm:grid-cols-2">
        <label><span class="field-label">Display name</span><Input v-model="form.display_name" required maxlength="160" /></label>
        <label><span class="field-label">Legal name</span><Input v-model="form.legal_name" maxlength="200" /></label>
        <label class="sm:col-span-2"><span class="field-label">Tagline</span><Input v-model="form.tagline" maxlength="180" /></label>
        <label><span class="field-label">Industry</span><Input v-model="form.industry" maxlength="80" placeholder="Professional services" /></label>
        <label><span class="field-label">Website</span><Input v-model="form.website_url" type="url" /></label>
        <label class="sm:col-span-2"><span class="field-label">Description</span><Textarea v-model="form.description" maxlength="4000" rows="4" class="min-h-28" /></label>
      </div>
    </fieldset>

    <fieldset class="space-y-4 border-t pt-7">
      <legend class="font-extrabold">Public contact</legend>
      <div class="grid gap-4 sm:grid-cols-2">
        <label><span class="field-label">Email</span><Input v-model="form.contact_email" type="email" /></label>
        <label><span class="field-label">Phone</span><Input v-model="form.contact_phone" inputmode="tel" /></label>
        <label class="sm:col-span-2"><span class="field-label">Street address</span><Input v-model="form.address" /></label>
        <label><span class="field-label">City</span><Input v-model="form.city" /></label>
        <label><span class="field-label">Region</span><Input v-model="form.region" /></label>
        <label><span class="field-label">Postal code</span><Input v-model="form.postal_code" /></label>
        <div><span class="field-label">Country</span><Select v-model="form.country"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="PH">Philippines</SelectItem><SelectItem value="SG">Singapore</SelectItem><SelectItem value="US">United States</SelectItem><SelectItem value="CA">Canada</SelectItem><SelectItem value="AU">Australia</SelectItem></SelectContent></Select></div>
      </div>
    </fieldset>
  </div>
</template>

<script setup>
import { Image as ImageIcon, Images, Upload } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

const props = defineProps({ form: { type: Object, required: true }, mediaFiles: { type: Object, required: true }, mediaPreviews: { type: Object, required: true } })
defineEmits(['select-image', 'clear-image'])
const imageFields = [
  { key: 'cover_image', label: 'Cover image', guidance: 'Wide image for business profiles and branded surfaces.', previewClass: 'aspect-[3/1]', fitClass: 'object-cover', icon: Images },
  { key: 'logo', label: 'Business logo', guidance: 'Primary mark used throughout PixelCore.', previewClass: 'aspect-[2/1]', fitClass: 'object-contain p-5', icon: ImageIcon },
  { key: 'favicon', label: 'Favicon', guidance: 'Small browser and shortcut icon.', previewClass: 'aspect-[2/1]', fitClass: 'object-contain p-7', icon: ImageIcon },
]
function imageSource(key) { return props.mediaPreviews[key] || props.form[key] || '' }
</script>
