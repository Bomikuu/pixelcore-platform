<template>
  <div class="overflow-hidden rounded-xl border bg-card">
    <div class="flex flex-col gap-3 border-b p-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="relative max-w-md flex-1"><Search class="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" /><Input v-model="search" type="search" class="pl-9" :aria-label="`Search ${kind}`" :placeholder="`Search ${kind}...`" /></div>
      <div class="flex items-center gap-3"><Select v-model="status"><SelectTrigger class="w-40" aria-label="Publication filter"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All statuses</SelectItem><SelectItem value="published">{{ isCategory ? 'Active' : 'Published' }}</SelectItem><SelectItem value="draft">{{ isCategory ? 'Inactive' : 'Draft' }}</SelectItem></SelectContent></Select><span class="text-sm tabular-nums text-muted-foreground">{{ filtered.length }} of {{ items.length }}</span></div>
    </div>
    <StatePanel v-if="!filtered.length" :title="items.length ? 'No matching results' : `No ${kind} yet`" :message="items.length ? 'Try another search or status filter.' : 'Create your first group and add the products customers should discover together.'" />
    <div v-else class="divide-y">
      <article v-for="item in filtered" :key="item.public_id" class="group grid items-center gap-4 p-4 transition-colors hover:bg-muted/40 sm:grid-cols-[6rem_minmax(0,1fr)_auto] sm:p-5">
        <NuxtLink :to="editPath(item)" :aria-label="`Edit ${item.name}`" class="aspect-[4/3] w-24 overflow-hidden rounded-lg border bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><img v-if="item.cover_url" :src="item.cover_url" alt="" class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03] motion-reduce:transform-none" /><ImageIcon v-else class="m-auto mt-6 h-6 w-6 text-muted-foreground" /></NuxtLink>
        <div class="min-w-0"><div class="flex flex-wrap items-center gap-3"><NuxtLink :to="editPath(item)" class="font-bold hover:underline">{{ item.name }}</NuxtLink><Badge :variant="published(item) ? 'secondary' : 'outline'">{{ published(item) ? (isCategory ? 'Active' : 'Published') : (isCategory ? 'Inactive' : 'Draft') }}</Badge></div><p class="mt-1 line-clamp-2 text-sm leading-6 text-muted-foreground">{{ item.description || 'Add a description to introduce this group.' }}</p><div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground"><span>/{{ item.slug }}</span><span v-if="isCategory" class="inline-flex items-center gap-1"><PanelTop class="h-3 w-3" />{{ item.show_in_header ? 'Shown in header' : 'Hidden from header' }}</span><template v-else><span>{{ item.offering_public_ids?.length || 0 }} products</span><span class="inline-flex items-center gap-1"><GalleryHorizontalEnd class="h-3 w-3" />{{ item.hero_settings?.enabled === false ? 'Compact introduction' : 'Full-screen hero' }}</span></template></div></div>
        <div class="flex items-center gap-2"><ButtonAnchor v-if="published(item)" :href="publicPath(item)" variant="ghost" size="icon" target="_blank" rel="noopener" :aria-label="`View ${item.name} on storefront`"><ExternalLink class="h-4 w-4" /></ButtonAnchor><ButtonLink :to="editPath(item)" variant="outline" size="sm"><Pencil class="mr-2 h-3.5 w-3.5" />Edit</ButtonLink></div>
      </article>
    </div>
  </div>
</template>
<script setup>
import { ExternalLink, GalleryHorizontalEnd, Image as ImageIcon, PanelTop, Pencil, Search } from 'lucide-vue-next'
const props = defineProps({ items: { type: Array, default: () => [] }, kind: { type: String, default: 'collections' }, slug: { type: String, default: '' } })
const route = useRoute()
const router = useRouter()
const search = computed({ get: () => String(route.query.search || ''), set: (value) => router.replace({ query: { ...route.query, search: value || undefined } }) })
const status = computed({ get: () => String(route.query.status || 'all'), set: (value) => router.replace({ query: { ...route.query, status: value === 'all' ? undefined : value } }) })
const isCategory = computed(() => props.kind === 'categories')
const published = (item) => isCategory.value ? item.is_active : item.is_published
const filtered = computed(() => props.items.filter((item) => `${item.name} ${item.description} ${item.slug}`.toLowerCase().includes(search.value.toLowerCase()) && (status.value === 'all' || published(item) === (status.value === 'published'))))
const editPath = (item) => isCategory.value ? { path: '/workspace/sell/categories', query: { ...route.query, edit: item.public_id } } : `/workspace/sell/collections/${item.public_id}`
const publicPath = (item) => `/site/${props.slug}/${isCategory.value ? `shop?category=${encodeURIComponent(item.slug)}` : `collection/${item.slug}`}`
</script>
