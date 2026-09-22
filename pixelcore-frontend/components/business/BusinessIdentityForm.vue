<template>
  <form :style="previewTheme" class="space-y-5" @submit.prevent="submit">
    <div class="flex flex-col gap-4 border-y bg-card px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-3"><Badge :variant="hasChanges ? 'default' : 'secondary'">{{ hasChanges ? 'Unsaved changes' : 'Saved' }}</Badge><p class="text-xs text-muted-foreground">Identity schema v{{ form.branding.schema_version }}</p></div>
      <div class="flex flex-wrap gap-2"><ButtonAnchor v-if="form.slug" :href="`/site/${form.slug}`" target="_blank" rel="noopener" variant="outline" size="sm"><ExternalLink class="h-4 w-4" /> View storefront</ButtonAnchor><Button type="submit" size="sm" :disabled="saving || !hasChanges"><LoaderCircle v-if="saving" class="h-4 w-4 animate-spin" /><Save v-else class="h-4 w-4" />{{ saving ? 'Saving identity…' : 'Save identity' }}</Button></div>
    </div>

    <div class="grid gap-5 lg:grid-cols-[11.5rem_minmax(0,1fr)] 2xl:grid-cols-[11.5rem_minmax(34rem,1fr)_24rem] lg:items-start">
      <IdentitySectionNav v-model="activeSection" />
      <Card class="shadow-none"><CardContent class="p-5 sm:p-7">
        <component :is="currentSection" :form="form" :assets="assets" :media-files="mediaFiles" :media-previews="mediaPreviews" @uploaded="assets.unshift($event)" @select-image="selectImage" @clear-image="clearPendingImage" @export-config="exportConfig" @import-config="importConfig" @reset-config="resetConfig" />
        <p v-if="error" class="mt-6 rounded-[var(--card-radius)] border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive" role="alert">{{ error }}</p>
      </CardContent></Card>
      <aside class="lg:col-start-2 2xl:sticky 2xl:top-16 2xl:col-start-3"><BrandPreview :business="form" :logo-preview="mediaPreviews.logo" :cover-preview="mediaPreviews.cover_image" :assets="assetMap" /></aside>
    </div>
  </form>
</template>

<script setup>
import { ExternalLink, LoaderCircle, Save } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ButtonAnchor } from '@/components/ui/button-anchor'
import { Card, CardContent } from '@/components/ui/card'
import { toast } from '@/components/ui/toast'
import { businessThemeStyle } from '@/utils/businessTheme'
import BrandPreview from './BrandPreview.vue'
import IdentityAdvancedSection from './IdentityAdvancedSection.vue'
import IdentityBannerSection from './IdentityBannerSection.vue'
import IdentityBrandingSection from './IdentityBrandingSection.vue'
import IdentityComponentsSection from './IdentityComponentsSection.vue'
import IdentityFooterSection from './IdentityFooterSection.vue'
import IdentityHeroSection from './IdentityHeroSection.vue'
import IdentityPopupSection from './IdentityPopupSection.vue'
import IdentitySectionNav from './IdentitySectionNav.vue'
import IdentitySocialsSection from './IdentitySocialsSection.vue'
import IdentityStorefrontLayoutSection from './IdentityStorefrontLayoutSection.vue'
import IdentityThemeSection from './IdentityThemeSection.vue'
import IdentityWorkspaceSection from './IdentityWorkspaceSection.vue'

const props = defineProps({ business: { type: Object, required: true } })
const emit = defineEmits(['saved', 'preview'])
const businessStore = useBusinessStore()
const { apiFetch } = useApiClient()
const activeSection = ref('branding')
const saving = ref(false)
const error = ref('')
const assets = ref([])
const mediaFiles = reactive({ logo: null, cover_image: null, favicon: null })
const mediaPreviews = reactive({ logo: '', cover_image: '', favicon: '' })
const form = reactive(buildForm(props.business))
const savedSnapshot = ref(snapshot(form))
const sectionComponents = { branding: IdentityBrandingSection, storefront: IdentityStorefrontLayoutSection, theme: IdentityThemeSection, components: IdentityComponentsSection, hero: IdentityHeroSection, banner: IdentityBannerSection, popup: IdentityPopupSection, footer: IdentityFooterSection, socials: IdentitySocialsSection, workspace: IdentityWorkspaceSection, advanced: IdentityAdvancedSection }
const currentSection = computed(() => sectionComponents[activeSection.value])
const hasChanges = computed(() => snapshot(form) !== savedSnapshot.value || Object.values(mediaFiles).some(Boolean))
const assetMap = computed(() => ({ ...(form.branding_assets || {}), ...Object.fromEntries(assets.value.map((asset) => [asset.public_id, { ...asset, url: asset.file_url }])) }))
const previewTheme = computed(() => businessThemeStyle(form))

watch(form, () => emit('preview', form, { ...mediaPreviews }), { deep: true })
watch(() => props.business.public_id, async () => { replaceForm(buildForm(props.business)); await loadAssets() })
onMounted(loadAssets)
onBeforeUnmount(() => Object.values(mediaPreviews).forEach((url) => { if (url) URL.revokeObjectURL(url) }))

function deepMerge(base, override) { const result = JSON.parse(JSON.stringify(base || {})); Object.entries(override || {}).forEach(([key, value]) => { result[key] = value && typeof value === 'object' && !Array.isArray(value) && result[key] && typeof result[key] === 'object' && !Array.isArray(result[key]) ? deepMerge(result[key], value) : JSON.parse(JSON.stringify(value)) }); return result }
function buildForm(business) { const result = JSON.parse(JSON.stringify(business)); result.branding = deepMerge(business.branding_defaults || {}, business.branding || {}); return result }
function snapshot(value) { return JSON.stringify(value, (key, item) => ['branding_defaults', 'branding_assets', 'created_at', 'updated_at'].includes(key) ? undefined : item) }
function replaceForm(value) { Object.keys(form).forEach((key) => delete form[key]); Object.assign(form, value); savedSnapshot.value = snapshot(form); Object.keys(mediaFiles).forEach(clearPendingImage) }
async function loadAssets() { const response = await apiFetch(`businesses/${props.business.public_id}/assets/`); assets.value = response.results || [] }

function selectImage(event, key) { const file = event.target.files?.[0] || null; event.target.value = ''; if (!file) return; if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) { error.value = 'Choose a JPG, PNG, or WebP image no larger than 5 MB.'; toast({ title: 'Image not accepted', description: error.value, variant: 'destructive' }); return } if (mediaPreviews[key]) URL.revokeObjectURL(mediaPreviews[key]); mediaFiles[key] = file; mediaPreviews[key] = URL.createObjectURL(file); error.value = '' }
function clearPendingImage(key) { if (mediaPreviews[key]) URL.revokeObjectURL(mediaPreviews[key]); mediaFiles[key] = null; mediaPreviews[key] = '' }
function resetConfig() { form.branding = deepMerge({}, props.business.branding_defaults || {}); toast({ title: 'Defaults loaded', description: 'Review the preview, then save identity to apply them.' }) }
function importConfig(payload) { const imported = payload.business || payload; if (!imported.branding || imported.branding.schema_version !== 1) { toast({ title: 'Import not accepted', description: 'Choose a PixelCore identity file using schema version 1.', variant: 'destructive' }); return } form.branding = deepMerge(props.business.branding_defaults || {}, imported.branding); ['display_name', 'tagline', 'description', 'website_url', 'contact_email', 'contact_phone'].forEach((key) => { if (typeof imported[key] === 'string') form[key] = imported[key] }); toast({ title: 'Identity imported', description: 'The imported configuration is ready to review and save.' }) }
function exportConfig() { const payload = { schema_version: 1, exported_at: new Date().toISOString(), business: { display_name: form.display_name, tagline: form.tagline, description: form.description, website_url: form.website_url, contact_email: form.contact_email, contact_phone: form.contact_phone, branding: form.branding } }; const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${form.slug || 'business'}-identity.json`; anchor.click(); URL.revokeObjectURL(url); toast({ title: 'Identity exported', description: 'The JSON file contains the same configuration shown in this editor.' }) }

async function submit() { saving.value = true; error.value = ''; try { const body = new FormData(); const fields = ['display_name', 'legal_name', 'tagline', 'industry', 'description', 'website_url', 'contact_email', 'contact_phone', 'address', 'city', 'region', 'postal_code', 'country', 'timezone', 'locale', 'currency', 'tax_id', 'tax_status', 'prices_include_tax']; fields.forEach((field) => { const value = form[field]; body.append(field, typeof value === 'boolean' ? String(value) : typeof value === 'string' ? value.trim() : value ?? '') }); body.append('branding', JSON.stringify(form.branding)); Object.entries(mediaFiles).forEach(([field, file]) => { if (file) body.append(field, file) }); const updated = await businessStore.updateIdentity(body); replaceForm(buildForm(updated)); emit('saved', updated); toast({ title: 'Business identity updated', description: 'Your storefront and workspace now share the saved appearance.' }) } catch (exception) { error.value = exception?.data?.error?.message || 'PixelCore could not save this identity.'; toast({ title: 'Identity update failed', description: error.value, variant: 'destructive' }) } finally { saving.value = false } }
</script>
