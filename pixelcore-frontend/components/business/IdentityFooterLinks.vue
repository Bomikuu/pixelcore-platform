<template>
  <fieldset class="space-y-5 border-t pt-7">
    <legend class="text-base font-extrabold">Information & policy links</legend>
    <div class="flex flex-wrap items-start justify-between gap-4">
      <p class="max-w-xl text-sm leading-6 text-muted-foreground">Add a label, then select a published page or enter a URL. Links appear in this order after you save identity. Up to eight links.</p>
      <Button type="button" variant="outline" size="sm" :disabled="links.length >= 8" @click="addLink('')"><Plus class="h-4 w-4" aria-hidden="true" />Custom link</Button>
    </div>
    <div class="flex flex-wrap gap-2" aria-label="Suggested footer links">
      <Button v-for="label in suggestions" :key="label" type="button" variant="outline" size="sm" :disabled="links.length >= 8 || hasLabel(label)" @click="addLink(label)"><Plus class="h-3.5 w-3.5" aria-hidden="true" />{{ label }}</Button>
    </div>
    <div class="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-muted px-4 py-3">
      <p class="max-w-xl text-xs leading-5 text-muted-foreground">Need a policy page? Create it in Site → Pages, add your own terms or policy content, and publish it before linking here.</p>
      <ButtonLink to="/workspace/site" variant="outline" size="sm"><FileText class="h-4 w-4" aria-hidden="true" />Manage pages</ButtonLink>
    </div>
    <p v-if="loading" class="text-sm text-muted-foreground" role="status">Loading published pages…</p>
    <div v-if="error" class="flex items-center justify-between gap-3 text-sm text-destructive" role="alert"><span>{{ error }}</span><Button type="button" variant="outline" size="sm" @click="loadPages">Retry</Button></div>
    <ol v-if="links.length" class="divide-y border-y">
      <li v-for="(link, index) in links" :key="index" class="space-y-3 py-5">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-bold">{{ link.label || 'New link' }}</span>
          <div class="flex gap-1">
            <Button type="button" variant="ghost" size="icon" :disabled="index === 0" :aria-label="`Move ${link.label || 'link'} up`" @click="move(index, -1)"><ArrowUp class="h-4 w-4" aria-hidden="true" /></Button>
            <Button type="button" variant="ghost" size="icon" :disabled="index === links.length - 1" :aria-label="`Move ${link.label || 'link'} down`" @click="move(index, 1)"><ArrowDown class="h-4 w-4" aria-hidden="true" /></Button>
            <Button type="button" variant="ghost" size="icon" class="text-destructive" :aria-label="`Remove ${link.label || 'link'}`" @click="links.splice(index, 1)"><Trash2 class="h-4 w-4" aria-hidden="true" /></Button>
          </div>
        </div>
        <div class="grid gap-3 sm:grid-cols-2">
          <label><span class="field-label">Link label</span><Input v-model.trim="link.label" maxlength="80" required /></label>
          <div><Label :for="`footer-page-${index}`" class="field-label">Published page</Label>
            <Select :model-value="pages.some((page) => pagePath(page) === link.url) ? link.url : 'custom-url'" @update:model-value="selectPage(link, $event)">
              <SelectTrigger :id="`footer-page-${index}`"><SelectValue placeholder="Choose a page" /></SelectTrigger>
              <SelectContent><SelectItem value="custom-url">Enter a URL below</SelectItem><SelectItem v-for="page in pages" :key="page.public_id" :value="pagePath(page)">{{ page.title }}</SelectItem></SelectContent>
            </Select>
          </div>
          <label class="sm:col-span-2"><span class="field-label">Destination</span><Input v-model.trim="link.url" required placeholder="/terms or https://…" /><span class="mt-1 block text-xs text-muted-foreground">Paths beginning with / stay within this business’s storefront.</span></label>
        </div>
      </li>
    </ol>
    <p v-else class="border-y py-6 text-sm text-muted-foreground">No policy links yet. Choose a suggested link above to start.</p>
    <Button v-if="hasMore" type="button" variant="ghost" size="sm" :disabled="loading" @click="loadPages">Load more published-page choices</Button>
  </fieldset>
</template>
<script setup>
import { ArrowDown, ArrowUp, FileText, Plus, Trash2 } from 'lucide-vue-next'
const props = defineProps({ links: { type: Array, required: true }, businessId: { type: String, required: true } })
const { apiFetch } = useApiClient()
const pages = ref([])
const loading = ref(false)
const error = ref('')
const hasMore = ref(false)
const nextPage = ref(1)
const suggestions = ['Terms of Agreement', 'Privacy Policy', 'Shipping & Delivery', 'Returns & Refunds', 'Contact Us', 'FAQs']
const hasLabel = (label) => props.links.some((link) => link.label.trim().toLowerCase() === label.toLowerCase())
const pagePath = (page) => page.page_type === 'home' ? '/' : `/${page.slug}`
function addLink(label) { if (props.links.length < 8) props.links.push({ label, url: '' }) }
function move(index, offset) { const [link] = props.links.splice(index, 1); props.links.splice(index + offset, 0, link) }
function selectPage(link, value) { link.url = value === 'custom-url' ? '' : value }
async function loadPages() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const response = await apiFetch(`businesses/${props.businessId}/site/pages/?page=${nextPage.value}&page_size=100`)
    pages.value.push(...(response.results || []).filter((page) => page.status === 'published'))
    hasMore.value = Boolean(response.next)
    nextPage.value += 1
  } catch { error.value = 'Published pages could not be loaded. Retry or enter a known page URL.' }
  finally { loading.value = false }
}
onMounted(loadPages)
</script>
