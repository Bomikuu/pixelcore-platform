<template>
  <section class="h-dvh bg-[#101112] text-white">
    <StatePanel v-if="loading" kind="loading" title="Opening website studio" message="Loading the shared builder and this business’s data." />
    <StatePanel v-else-if="error" kind="error" title="Website studio unavailable" :message="error">
      <Button variant="outline" @click="load">Try again</Button>
    </StatePanel>
    <div v-else-if="setup" class="h-full overflow-hidden">
      <ClientOnly>
        <WebsiteEditor ref="editor" :document="setup.document" :data="setup.data" :adapter="adapter" :version="setup.version" show-setup @error="editorError" />
      </ClientOnly>
    </div>
    <Dialog :open="leaveOpen" @update:open="cancelLeave">
      <DialogContent>
        <DialogHeader><DialogTitle>Leave with unsaved changes?</DialogTitle><DialogDescription>The current draft has not finished saving. Stay to save or export your work.</DialogDescription></DialogHeader>
        <DialogFooter><Button variant="outline" @click="cancelLeave">Stay here</Button><Button variant="destructive" @click="confirmLeave">Leave without saving</Button></DialogFooter>
      </DialogContent>
    </Dialog>
  </section>
</template>
<script setup>
import { WebsiteEditor } from '@sitebuilder/vue'
import { createDjangoAdapter } from '@sitebuilder/editor'
definePageMeta({ layout: false })
const route = useRoute()
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const editor = ref(null)
const setup = shallowRef(null)
const adapter = shallowRef(null)
const loading = ref(true)
const error = ref('')
const leaveOpen = ref(false)
let leaveResolver
let sequence = 0
const kind = computed(() => ['event','layout'].includes(route.query.kind) ? route.query.kind : 'page')
const sourceId = computed(() => String(route.query.source || ''))
const backPath = computed(() => kind.value === 'layout' ? '/workspace/site' : kind.value === 'event' ? `/workspace/schedule/events/${sourceId.value}?tab=website` : `/workspace/site/pages/${sourceId.value}`)
onMounted(load)
watch(() => [business.activeBusiness?.public_id, route.query.source, route.query.kind], () => { if (business.activeBusiness) load() })
onBeforeUnmount(() => { sequence++; leaveResolver?.(false) })
function editorError(value) { error.value = value?.message || 'The shared editor could not open.' }
async function load() {
  const requestId = ++sequence
  loading.value = true
  error.value = ''
  try {
    if (!business.activeBusiness) await business.loadBusinesses()
    if (!sourceId.value) throw new Error('Open the studio from an existing page or event.')
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/website-builder/`, { method: 'POST', body: { kind: kind.value, sourceId: sourceId.value } })
    if (requestId !== sequence) return
    setup.value = response
    const caps = response.capabilities || {}
    adapter.value = createDjangoAdapter({ websiteId: response.id, baseUrl: 'website-builder/', request: apiFetch, capabilities: caps.features, sources: caps.sources, dataSources: caps.dataSources, brandKit: caps.brandKit, workspace: caps.workspace, exit: () => navigateTo(backPath.value), openPage: page => navigateTo(`/workspace/site/builder?kind=${page.kind}&source=${page.sourceId}`), openRegion: () => navigateTo(`/workspace/site/builder?kind=layout&source=${caps.workspace.layoutSourceId}`), changeSource: () => navigateTo(kind.value === 'event' ? '/workspace/schedule' : '/workspace/site'), openSource: () => navigateTo(kind.value === 'event' ? `/workspace/schedule/events/${sourceId.value}?tab=website` : kind.value === 'layout' ? '/workspace/site' : '/workspace/sell') })
  } catch (requestError) {
    if (requestId === sequence) error.value = requestError?.data?.error?.message || requestError.message || 'The website studio could not be loaded.'
  } finally { if (requestId === sequence) loading.value = false }
}
function guardLeave() {
  if (!editor.value?.hasUnsavedChanges?.()) return true
  leaveOpen.value = true
  return new Promise(resolve => { leaveResolver = resolve })
}
onBeforeRouteLeave(guardLeave)
onBeforeRouteUpdate(guardLeave)
function cancelLeave() { leaveOpen.value = false; leaveResolver?.(false); leaveResolver = undefined }
function confirmLeave() { leaveOpen.value = false; leaveResolver?.(true); leaveResolver = undefined }
</script>
