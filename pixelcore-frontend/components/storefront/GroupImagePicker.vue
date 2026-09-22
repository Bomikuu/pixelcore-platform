<template>
  <div class="space-y-4">
    <div class="relative aspect-[16/10] overflow-hidden rounded-lg border bg-muted">
      <img v-if="selectedImage" :src="selectedImage" alt="Selected cover preview" class="h-full w-full object-cover" />
      <div v-else class="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground"><ImageIcon class="h-8 w-8" /><p class="text-sm">Choose a cover for this group</p></div>
    </div>
    <Select :model-value="modelValue || 'none'" @update:model-value="$emit('update:modelValue', $event === 'none' ? null : $event)"><SelectTrigger aria-label="Cover image"><SelectValue placeholder="Choose from media library" /></SelectTrigger><SelectContent><SelectItem value="none">No custom cover</SelectItem><SelectItem v-for="asset in imageAssets" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</SelectItem></SelectContent></Select>
    <label class="block"><span class="field-label">Upload a new image</span><Input type="file" accept="image/jpeg,image/png,image/webp" :disabled="uploading" @change="upload" /></label>
    <p class="text-xs leading-5 text-muted-foreground">JPG, PNG or WebP, up to 5 MB. A wide image works best for a collection hero.</p>
    <p v-if="uploading" role="status" class="text-sm">Uploading image...</p><p v-if="error" role="alert" class="text-sm text-destructive">{{ error }}</p>
  </div>
</template>
<script setup>
import { Image as ImageIcon } from 'lucide-vue-next'
const props = defineProps({ modelValue: { type: String, default: null }, assets: { type: Array, default: () => [] }, fallback: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue', 'uploaded'])
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const uploading = ref(false)
const error = ref('')
const imageAssets = computed(() => props.assets.filter((asset) => asset.asset_type === 'image' && asset.processing_status === 'ready'))
const selectedImage = computed(() => props.modelValue ? imageAssets.value.find((asset) => asset.public_id === props.modelValue)?.file_url || props.fallback : '')
async function upload(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  error.value = ''
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) { error.value = 'Choose a JPG, PNG or WebP image under 5 MB.'; return }
  uploading.value = true
  try {
    const body = new FormData()
    body.append('file', file); body.append('title', file.name); body.append('asset_type', 'image')
    const asset = await apiFetch(`businesses/${business.activeBusiness.public_id}/assets/`, { method: 'POST', body })
    emit('uploaded', asset); emit('update:modelValue', asset.public_id)
  } catch (exception) { error.value = exception?.data?.error?.message || 'The image could not be uploaded. Try again.' }
  finally { uploading.value = false }
}
</script>
