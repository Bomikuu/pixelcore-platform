<template>
  <form class="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]" @submit.prevent="save">
    <div class="space-y-5">
      <section class="rounded-xl border bg-card p-5 sm:p-6"><h2 class="font-bold">Category details</h2><p class="mt-1 text-sm text-muted-foreground">Organize products into departments customers can browse.</p><div class="mt-5 space-y-4"><label class="block"><span class="field-label">Name</span><Input v-model.trim="form.name" required maxlength="120" /></label><label class="block"><span class="field-label">URL slug</span><Input v-model.trim="form.slug" pattern="[a-z0-9-]+" placeholder="Generated from the name" /></label><label class="block"><span class="field-label">Description</span><Textarea v-model.trim="form.description" class="min-h-28" /></label></div></section>
      <section class="rounded-xl border bg-card p-5 sm:p-6"><h2 class="font-bold">Category image</h2><p class="mb-5 mt-1 text-sm leading-6 text-muted-foreground">This image represents the category in the shop menu. Without a custom image, the store uses product photography.</p><GroupImagePicker v-model="form.cover_asset_public_id" :assets="assets" :fallback="category?.cover_url || ''" @uploaded="$emit('uploaded', $event)" /></section>
    </div>
    <aside class="space-y-5 xl:sticky xl:top-5"><section class="rounded-xl border bg-card p-5"><h2 class="font-bold">Visibility & ordering</h2><label class="mt-5 flex items-center justify-between gap-4 text-sm"><span>Active category</span><Switch v-model:checked="form.is_active" /></label><label class="mt-5 flex items-center justify-between gap-4 text-sm"><span>Show in shop header</span><Switch v-model:checked="form.show_in_header" /></label><label class="mt-5 block"><span class="field-label">Header order</span><Input v-model.number="form.header_order" type="number" min="0" /></label><label class="mt-4 block"><span class="field-label">Catalog sort order</span><Input v-model.number="form.sort_order" type="number" min="0" /></label><p class="mt-3 text-xs leading-5 text-muted-foreground">Lower numbers appear first. Inactive categories stay out of public browsing.</p><Button type="submit" class="mt-5 w-full" :disabled="saving"><Save class="mr-2 h-4 w-4" />{{ saving ? 'Saving...' : 'Save category' }}</Button><p v-if="error" role="alert" class="mt-3 text-sm text-destructive">{{ error }}</p></section></aside>
  </form>
</template>
<script setup>
import { Save } from 'lucide-vue-next'
import GroupImagePicker from './GroupImagePicker.vue'
const props = defineProps({ category: { type: Object, default: null }, assets: { type: Array, default: () => [] } })
const emit = defineEmits(['saved', 'uploaded'])
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const saving = ref(false)
const error = ref('')
const form = reactive({ name: '', slug: '', description: '', cover_asset_public_id: null, header_order: 0, sort_order: 0, show_in_header: true, is_active: true })
watch(() => props.category, (value) => { if (value) Object.keys(form).forEach((key) => { if (value[key] !== undefined) form[key] = value[key] }) }, { immediate: true })
async function save() {
  saving.value = true; error.value = ''
  try {
    const path = `businesses/${business.activeBusiness.public_id}/categories/${props.category ? `${props.category.public_id}/` : ''}`
    const updated = await apiFetch(path, { method: props.category ? 'PATCH' : 'POST', body: form })
    emit('saved', updated)
  } catch (exception) { error.value = exception?.data?.error?.message || 'The category could not be saved. Check the fields and try again.' }
  finally { saving.value = false }
}
</script>
