<template>
  <div class="space-y-8"><header><h2 class="text-xl font-extrabold">Storefront footer</h2><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Give customers a clear next step: browse the shop, read your policies, or get in touch. Your business colors and contact details carry through.</p></header>
    <div class="grid gap-4 sm:grid-cols-2"><label class="sm:col-span-2"><span class="field-label">Business description</span><Textarea v-model="footer.description" maxlength="500" rows="3" /></label><label class="sm:col-span-2"><span class="field-label">Copyright text</span><Input v-model="footer.copyright_text" maxlength="180" placeholder="© 2026 Your business" /></label><div class="sm:col-span-2"><span class="field-label">Footer logo</span><Select :model-value="footer.logo_asset_id || 'business-logo'" @update:model-value="footer.logo_asset_id = $event === 'business-logo' ? '' : $event"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="business-logo">Use business logo</SelectItem><SelectItem v-for="asset in imageAssets" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</SelectItem></SelectContent></Select></div><label><span class="field-label">Background</span><Input v-model="footer.background_color" type="color" class="h-11 p-1" /></label><label><span class="field-label">Text</span><Input v-model="footer.text_color" type="color" class="h-11 p-1" /></label><label><span class="field-label">Link color</span><Input v-model="footer.link_color" type="color" class="h-11 p-1" /></label></div>
    <IdentityFooterLinks :links="footer.links" :business-id="form.public_id" />
    <fieldset class="space-y-4 border-t pt-7"><legend class="font-extrabold">Optional custom footer content</legend><label><span class="field-label">Custom HTML</span><Textarea v-model="footer.custom_html" rows="7" class="font-mono text-xs" /></label><label><span class="field-label">Scoped CSS</span><Textarea v-model="footer.custom_css" rows="7" class="font-mono text-xs" /></label><p class="text-xs leading-5 text-muted-foreground">Custom content renders inside an isolated frame. Scripts, forms, remote CSS, and arbitrary JavaScript are never accepted.</p></fieldset>
  </div>
</template>
<script setup>
import IdentityFooterLinks from './IdentityFooterLinks.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
const props = defineProps({ form: { type: Object, required: true }, assets: { type: Array, default: () => [] } })
const footer = computed(() => props.form.branding.storefront.footer)
const imageAssets = computed(() => props.assets.filter((asset) => asset.asset_type === 'image' && asset.processing_status === 'ready'))
</script>
