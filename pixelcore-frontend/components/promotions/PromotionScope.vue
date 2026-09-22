<template>
  <section class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="promotion-scope-heading">
    <h2 id="promotion-scope-heading" class="text-base font-extrabold">Catalog scope</h2>
    <p class="mt-1 text-sm text-muted-foreground">Choose exactly where this offer applies.</p>
    <fieldset class="mt-5 grid gap-3 sm:grid-cols-3">
      <legend class="sr-only">Apply this promotion to</legend>
      <label v-for="choice in choices" :key="choice.value" class="flex cursor-pointer items-start gap-3 rounded-lg border p-4" :class="scope === choice.value ? 'border-primary bg-secondary/40' : ''">
        <NativeRadio name="promotion-catalog-scope" :model-value="scope" :value="choice.value" class="mt-0.5" @update:model-value="$emit('update:scope', $event)" /><span><strong class="block text-sm">{{ choice.label }}</strong><span class="mt-1 block text-xs leading-5 text-muted-foreground">{{ choice.description }}</span></span>
      </label>
    </fieldset>
    <p v-if="scope === 'catalog'" class="mt-5 text-sm leading-6 text-muted-foreground">Applies to all current and future products and services.</p>
    <template v-else>
      <div class="mt-5 flex flex-wrap items-center justify-between gap-3 border-t pt-5"><p class="text-sm font-semibold">{{ selected.length }} {{ scope }} selected</p><Button type="button" variant="ghost" size="sm" :disabled="!selected.length" @click="clear">Clear selection</Button></div>
      <p v-if="scope === 'categories'" class="mt-2 text-xs leading-5 text-muted-foreground">Includes every product assigned directly to a selected category, including future additions. Select child categories separately.</p>
      <div v-if="scope === 'products'" class="mt-4 flex gap-2"><Input v-model="search" aria-label="Search products" placeholder="Search products" @keydown.enter.prevent="fetchPage(1)" /><Button type="button" variant="outline" @click="fetchPage(1)">Search</Button></div>
      <StatePanel v-if="loading" kind="loading" title="Loading choices" />
      <StatePanel v-else-if="error" kind="error" title="Choices unavailable" :message="error"><Button type="button" variant="outline" @click="fetchPage(page)">Retry</Button></StatePanel>
      <div v-else class="mt-4 overflow-hidden rounded-lg border">
        <div class="grid sm:grid-cols-2">
          <label v-for="item in items" :key="item.public_id" class="flex cursor-pointer items-center gap-3 border-b p-3 transition-colors hover:bg-muted/40" :class="selected.includes(item.public_id) ? 'bg-secondary/40' : ''">
            <NativeCheckbox v-model="form[field]" :value="item.public_id" />
            <img v-if="image(item)" :src="image(item)" alt="" class="h-12 w-12 shrink-0 rounded-md bg-muted object-cover" />
            <Package v-else class="h-6 w-6 shrink-0 text-muted-foreground" aria-hidden="true" />
            <span class="min-w-0"><strong class="block text-sm">{{ item.name }}</strong><span v-if="item.status" class="mt-1 block text-xs capitalize text-muted-foreground">{{ item.status }}</span></span>
          </label>
        </div>
        <p v-if="!items.length" class="p-5 text-sm text-muted-foreground">No {{ scope }} found. Adjust your search or add records to the catalog.</p>
        <RecordPagination :page="page" :count="count" :size="20" :busy="loading" @page="fetchPage" />
      </div>
    </template>
  </section>
</template>
<script setup>
import { Package } from 'lucide-vue-next'
import { productImages } from '~/utils/productImages'
import RecordPagination from '~/components/workspace/RecordPagination.vue'
const props = defineProps({ scope: { type: String, required: true }, form: { type: Object, required: true }, businessId: { type: String, required: true } })
defineEmits(['update:scope'])
const { apiFetch } = useApiClient()
const items = ref([]), count = ref(0), page = ref(1), search = ref(''), loading = ref(false), error = ref('')
let requestVersion = 0
const field = computed(() => props.scope === 'categories' ? 'category_ids' : 'offering_ids')
const selected = computed(() => props.form[field.value])
const choices = [{ value: 'catalog', label: 'Entire catalog', description: 'Every product and service.' }, { value: 'categories', label: 'Categories', description: 'All items in chosen categories.' }, { value: 'products', label: 'Specific products', description: 'Only the items you select.' }]
function clear() { props.form[field.value] = [] }
const image = (item) => props.scope === 'categories' ? item.cover_url : productImages(item)[0]?.url
async function fetchPage(value = 1) {
  const version = ++requestVersion
  if (props.scope === 'catalog') { loading.value = false; return }
  loading.value = true; error.value = ''; page.value = value
  const resource = props.scope === 'categories' ? 'categories' : 'offerings'
  const query = new URLSearchParams({ page: String(value), page_size: '20' })
  if (resource === 'offerings' && search.value) query.set('search', search.value)
  try {
    const response = await apiFetch(`businesses/${props.businessId}/${resource}/?${query}`)
    if (version !== requestVersion) return
    items.value = response.results || []; count.value = response.count || 0
  } catch (err) { if (version === requestVersion) error.value = err?.data?.error?.message || 'Could not load catalog choices.' }
  finally { if (version === requestVersion) loading.value = false }
}
watch(() => [props.scope, props.businessId], () => { search.value = ''; fetchPage(1) }, { immediate: true })
</script>
