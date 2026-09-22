<template>
  <section class="space-y-4">
    <div class="flex flex-wrap items-start justify-between gap-3"><div><h3 class="font-semibold">Custom hero slides</h3><p class="mt-1 text-sm leading-6 text-muted-foreground">Use your own copy with an image, video, 3D model, or particle animation. Custom slides replace product slides.</p></div><Button type="button" variant="outline" size="sm" :disabled="modelValue.length >= 5" @click="add"><Plus class="mr-2 h-4 w-4" />Add slide</Button></div>
    <p v-if="!modelValue.length" class="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">No custom slides. The hero uses selected product photography.</p>
    <Accordion type="single" collapsible class="space-y-3" :default-value="modelValue[0]?.id">
      <AccordionItem v-for="(slide, index) in modelValue" :key="slide.id" :value="slide.id" class="rounded-lg border bg-background px-4"><AccordionTrigger class="text-left">{{ index + 1 }}. {{ slide.heading || 'Untitled slide' }} <span class="ml-2 text-xs text-muted-foreground">{{ slide.type }}</span></AccordionTrigger><AccordionContent class="space-y-4">
        <div class="flex gap-2"><Button type="button" variant="outline" size="sm" :disabled="index === 0" @click="move(index, -1)" aria-label="Move slide earlier"><ArrowUp class="h-4 w-4" /></Button><Button type="button" variant="outline" size="sm" :disabled="index === modelValue.length - 1" @click="move(index, 1)" aria-label="Move slide later"><ArrowDown class="h-4 w-4" /></Button><Button type="button" variant="ghost" size="sm" class="ml-auto text-destructive" @click="remove(index)"><Trash2 class="mr-2 h-4 w-4" />Remove</Button></div>
        <label class="block"><span class="field-label">Background type</span><Select :model-value="slide.type" @update:model-value="update(index, { type: $event, asset_id: '' })"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="image">Image</SelectItem><SelectItem value="video">Video</SelectItem><SelectItem value="model">3D model</SelectItem><SelectItem value="particles">Particle animation</SelectItem></SelectContent></Select></label>
        <label class="block"><span class="field-label">Heading</span><Input :model-value="slide.heading" maxlength="180" @update:model-value="update(index, { heading: $event })" /></label><label class="block"><span class="field-label">Description</span><Textarea :model-value="slide.body" maxlength="600" @update:model-value="update(index, { body: $event })" /></label>
        <label v-if="slide.type !== 'particles'" class="block"><span class="field-label">Background media</span><Select :model-value="slide.asset_id || 'none'" @update:model-value="update(index, { asset_id: $event === 'none' ? '' : $event })"><SelectTrigger><SelectValue placeholder="Choose media" /></SelectTrigger><SelectContent><SelectItem value="none">Choose media</SelectItem><SelectItem v-for="asset in mediaFor(slide.type)" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</SelectItem></SelectContent></Select></label>
        <label v-if="slide.type !== 'image'" class="block"><span class="field-label">Poster image{{ slide.type === 'particles' ? ' (optional)' : ' (required)' }}</span><Select :model-value="slide.poster_asset_id || 'none'" @update:model-value="update(index, { poster_asset_id: $event === 'none' ? '' : $event })"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">Choose fallback image</SelectItem><SelectItem v-for="asset in mediaFor('image')" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</SelectItem></SelectContent></Select></label>
        <div class="grid gap-4 sm:grid-cols-2"><label><span class="field-label">Action label</span><Input :model-value="slide.label" maxlength="80" @update:model-value="update(index, { label: $event })" /></label><label><span class="field-label">Storefront path</span><Input :model-value="slide.path" placeholder="/shop" @update:model-value="update(index, { path: $event })" /></label></div>
        <label v-if="['model', 'particles'].includes(slide.type)" class="block"><span class="field-label">Motion</span><Select :model-value="slide.motion || 'subtle'" @update:model-value="update(index, { motion: $event })"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">Static scene</SelectItem><SelectItem value="subtle">Subtle rotation</SelectItem><SelectItem value="interactive">Pointer response</SelectItem></SelectContent></Select></label>
        <label class="block"><span class="field-label">Background color</span><Input type="color" :model-value="slide.background_color" @update:model-value="update(index, { background_color: $event })" /></label>
      </AccordionContent></AccordionItem>
    </Accordion>
    <label class="block"><span class="field-label">Add to media library</span><Input type="file" accept="image/jpeg,image/png,image/webp,video/mp4,video/webm,.glb" :disabled="uploading" @change="upload" /></label><p class="text-xs leading-5 text-muted-foreground">Images, MP4/WebM videos, or self-contained GLB models, up to 25 MB. Select uploaded media in a slide above.</p><p v-if="error" role="alert" class="text-sm text-destructive">{{ error }}</p><p v-if="uploading" role="status" class="text-sm">Uploading and validating media...</p>
  </section>
</template>
<script setup>
import { ArrowDown, ArrowUp, Plus, Trash2 } from 'lucide-vue-next'
const props = defineProps({ modelValue: { type: Array, default: () => [] }, assets: { type: Array, default: () => [] } })
const emit = defineEmits(['update:modelValue', 'uploaded'])
const { apiFetch } = useApiClient()
const business = useBusinessStore()
const error = ref(''), uploading = ref(false)
const mediaFor = (type) => props.assets.filter((asset) => asset.asset_type === type && asset.processing_status === 'ready')
function update(index, data) { emit('update:modelValue', props.modelValue.map((item, i) => i === index ? { ...item, ...data } : item)) }
function add() { emit('update:modelValue', [...props.modelValue, { id: crypto.randomUUID(), type: 'image', heading: '', body: '', asset_id: '', poster_asset_id: '', label: 'Explore', path: '/shop', background_color: '#17362F', motion: 'subtle' }]) }
function remove(index) { emit('update:modelValue', props.modelValue.filter((_, i) => i !== index)) }
function move(index, direction) { const items = [...props.modelValue]; [items[index], items[index + direction]] = [items[index + direction], items[index]]; emit('update:modelValue', items) }
async function upload(event) {
  const file = event.target.files?.[0]; event.target.value = ''; if (!file) return
  error.value = ''; if (file.size > 25 * 1024 * 1024) { error.value = 'Choose a file under 25 MB.'; return }
  uploading.value = true
  try { const body = new FormData(); body.append('file', file); body.append('title', file.name); body.append('asset_type', file.name.toLowerCase().endsWith('.glb') ? 'model' : file.type.startsWith('video/') ? 'video' : 'image'); const asset = await apiFetch(`businesses/${business.activeBusiness.public_id}/assets/`, { method: 'POST', body }); emit('uploaded', asset); if (asset.processing_status !== 'ready') error.value = asset.validation_error || 'Media is still processing. Select it when validation is complete.' }
  catch (exception) { error.value = exception?.data?.error?.message || 'The file could not be uploaded.' }
  finally { uploading.value = false }
}
</script>
