<template>
  <section class="workspace-page space-y-8">
    <PageHeader title="Site" description="Publish a structured storefront without exposing raw HTML, scripts, styles, or unbounded 3D code.">
      <template #actions>
        <ButtonLink v-if="pages.length" variant="outline" :to="`/workspace/site/builder?kind=page&source=${(publishedHome || pages[0]).public_id}`">Visual studio</ButtonLink>
        <Button variant="outline" type="button" @click="templateOpen = true"><ShoppingBag class="h-4 w-4" aria-hidden="true" /> Commerce template</Button>
        <ButtonLink variant="outline"  to="/workspace/site/domains"><Globe2 class="h-4 w-4" aria-hidden="true" /> Domains</ButtonLink>
        <Button type="button" @click="creating = !creating"><Plus class="h-4 w-4" aria-hidden="true" /> New page</Button>
      </template>
    </PageHeader>

    <div class="grid gap-8 xl:grid-cols-[minmax(0,1fr)_22rem]">
      <section aria-labelledby="pages-heading">
        <div class="flex items-center justify-between gap-4">
          <h2 id="pages-heading" class="display-face text-2xl font-semibold">Pages</h2>
          <span v-if="site" class="text-sm text-muted-foreground">Site is <strong class="text-foreground">{{ site.status }}</strong></span>
        </div>
        <StatePanel v-if="loading" class="mt-4" kind="loading" title="Loading pages" message="Retrieving drafts and published revisions." />
        <StatePanel v-else-if="error" class="mt-4" kind="error" title="Pages unavailable" :message="error"><Button variant="outline" type="button" @click="load">Try again</Button></StatePanel>
        <StatePanel v-else-if="!pages.length" class="mt-4" title="Start with the home page" message="Create a page, arrange its blocks, preview it privately, then publish one immutable revision." />
        <div v-else class="mt-4 border-y bg-card">
          <NuxtLink v-for="page in pages" :key="page.public_id" :to="`/workspace/site/pages/${page.public_id}`" class="resource-row sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center">
            <span><span class="block font-bold">{{ page.title }}</span><span class="mt-1 block text-sm text-muted-foreground">{{ page.page_type === 'home' ? '/' : `/${page.slug}` }} · Revision {{ page.draft_revision?.number || 0 }}</span></span>
            <StatusPill :value="page.status" />
            <span class="inline-flex items-center gap-1 text-sm font-bold text-primary">Edit <ArrowRight class="h-4 w-4" aria-hidden="true" /></span>
          </NuxtLink>
        </div>
      </section>

      <aside class="border-t pt-6 xl:border-l xl:border-t-0 xl:pl-8 xl:pt-0">
        <form v-if="creating" class="space-y-4" @submit.prevent="createPage">
          <h2 class="font-bold">Create a page</h2>
          <div><label class="field-label" for="page-title">Page title</label><Input id="page-title" v-model.trim="form.title" required /></div>
          <div><label class="field-label" for="page-slug">URL slug</label><Input id="page-slug" v-model.trim="form.slug" pattern="[a-z0-9-]+" required /></div>
          <div><label class="field-label" for="page-type">Page type</label><NativeSelect id="page-type" v-model="form.page_type"><option value="standard">Standard</option><option value="home">Home</option><option value="policy">Policy</option></NativeSelect></div>
          <p v-if="saveError" role="alert" class="text-sm text-destructive">{{ saveError }}</p>
          <Button class="w-full" type="submit" :disabled="saving">{{ saving ? 'Creating page…' : 'Create page' }}</Button>
        </form>
        <div v-else>
          <h2 class="font-bold">Publishing model</h2>
          <ol class="mt-4 space-y-4 text-sm leading-6 text-muted-foreground">
            <li><strong class="text-foreground">Draft safely.</strong> Every save creates a new immutable revision.</li>
            <li><strong class="text-foreground">Preview privately.</strong> Signed links expire and carry no-index directives.</li>
            <li><strong class="text-foreground">Publish atomically.</strong> Visitors see one complete revision; rollback is another publish action.</li>
          </ol>
        </div>
      </aside>
    </div>
    <Dialog v-model:open="templateOpen"><DialogContent><DialogHeader><DialogTitle>Apply the commerce storefront</DialogTitle><DialogDescription>This creates an editable CMS home draft using real published products. Your catalog, custom pages, and current published page remain available until you publish the new revision.</DialogDescription></DialogHeader><Alert v-if="publishedHome"><AlertTitle>A published home page exists</AlertTitle><AlertDescription>Applying the template replaces its current draft, not the live revision. Confirm that you want to prepare this new draft.</AlertDescription></Alert><label v-if="publishedHome" class="flex items-start gap-3 text-sm"><NativeCheckbox v-model="templateConfirmed" class="mt-0.5" /><span>I understand the current home draft will be replaced.</span></label><DialogFooter><Button variant="outline" type="button" @click="templateOpen = false">Cancel</Button><Button type="button" :disabled="applyingTemplate || (publishedHome && !templateConfirmed)" @click="applyCommerceTemplate">{{ applyingTemplate ? 'Applying…' : 'Apply commerce template' }}</Button></DialogFooter></DialogContent></Dialog>
  </section>
</template>

<script setup>
import { ArrowRight, Globe2, Plus, ShoppingBag } from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'

const business = useBusinessStore()
const { apiFetch } = useApiClient()
const site = ref(null)
const pages = ref([])
const loading = ref(true)
const error = ref('')
const creating = ref(false)
const saving = ref(false)
const saveError = ref('')
const form = reactive({ title: '', slug: '', page_type: 'standard' })
const templateOpen = ref(false)
const templateConfirmed = ref(false)
const applyingTemplate = ref(false)
const publishedHome = computed(() => pages.value.find((page) => page.page_type === 'home' && page.status === 'published'))

watch(() => business.activeBusiness?.public_id, (value) => { if (value) load() })
onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses().catch(() => {})
  await load()
})

async function load() {
  if (!business.activeBusiness) return
  loading.value = true
  error.value = ''
  try {
    const id = business.activeBusiness.public_id
    const [siteResponse, pageResponse] = await Promise.all([apiFetch(`businesses/${id}/site/`), apiFetch(`businesses/${id}/site/pages/`)])
    site.value = siteResponse
    pages.value = pageResponse.results || []
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || 'Could not retrieve the site workspace.'
  } finally { loading.value = false }
}

async function createPage() {
  saving.value = true
  saveError.value = ''
  try {
    const page = await apiFetch(`businesses/${business.activeBusiness.public_id}/site/pages/`, { method: 'POST', body: form })
    await navigateTo(`/workspace/site/pages/${page.public_id}`)
  } catch (requestError) {
    saveError.value = requestError?.data?.error?.message || 'The page could not be created.'
  } finally { saving.value = false }
}

async function applyCommerceTemplate() {
  applyingTemplate.value = true
  try {
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/site/templates/commerce/`, { method: 'POST', body: { confirm_replace: templateConfirmed.value } })
    templateOpen.value = false
    toast({ title: 'Commerce draft created', description: 'Review the product-led home page before publishing it.' })
    await navigateTo(`/workspace/site/pages/${response.page.public_id}`)
  } catch (requestError) {
    toast({ title: 'Template not applied', description: requestError?.data?.error?.message || 'The commerce draft could not be created.', variant: 'destructive' })
  } finally { applyingTemplate.value = false }
}
</script>
