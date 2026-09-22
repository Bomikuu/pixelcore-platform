<template>
  <div class="space-y-8">
    <IdentityMarketplaceHeroSettings
      v-if="form.branding.storefront.layout === 'marketplace'"
      :form="form"
      :assets="assets"
      @uploaded="$emit('uploaded', $event)"
    />
    <header><h2 class="text-xl font-extrabold">Hero & background</h2><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Set the storefront canvas and an optional global hero. Enabling it replaces existing page hero blocks without changing their saved content.</p></header>

    <fieldset class="space-y-4"><legend class="font-extrabold">Storefront background</legend><div class="grid gap-4 sm:grid-cols-2">
      <div><span class="field-label">Background type</span><Select v-model="background.type"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="color">Solid color</SelectItem><SelectItem value="gradient">Gradient</SelectItem><SelectItem value="image">Image</SelectItem></SelectContent></Select></div>
      <label><span class="field-label">Base color</span><Input v-model="background.color" type="color" class="h-11 p-1" /></label>
      <template v-if="background.type === 'gradient'"><label><span class="field-label">Gradient start</span><Input v-model="background.gradient_from" type="color" class="h-11 p-1" /></label><label><span class="field-label">Gradient end</span><Input v-model="background.gradient_to" type="color" class="h-11 p-1" /></label><label><span class="field-label">Angle</span><Input v-model.number="background.gradient_angle" type="number" min="0" max="360" /></label></template>
      <div v-if="background.type === 'image'" class="sm:col-span-2"><span class="field-label">Background image</span><Select :model-value="background.asset_id || 'none'" @update:model-value="background.asset_id = $event === 'none' ? '' : $event"><SelectTrigger><SelectValue placeholder="Choose an image" /></SelectTrigger><SelectContent><SelectItem value="none">No image selected</SelectItem><SelectItem v-for="asset in imageAssets" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</SelectItem></SelectContent></Select></div>
    </div></fieldset>

    <fieldset class="space-y-5 border-t pt-7"><div class="flex items-start justify-between gap-5"><div><legend class="font-extrabold">Global storefront hero</legend><p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">Keep this off to continue using the hero saved in your CMS page.</p></div><Switch v-model:checked="hero.enabled" aria-label="Enable global storefront hero" /></div>
      <div v-if="hero.enabled" class="grid gap-4 sm:grid-cols-2">
        <div><span class="field-label">Background type</span><Select v-model="hero.type"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="color">Color</SelectItem><SelectItem value="gradient">Gradient</SelectItem><SelectItem value="image">Image</SelectItem><SelectItem value="video">Video</SelectItem><SelectItem value="three">Three.js model</SelectItem></SelectContent></Select></div>
        <div><span class="field-label">Minimum height</span><Select v-model="hero.minimum_height"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="compact">Compact</SelectItem><SelectItem value="medium">Medium</SelectItem><SelectItem value="tall">Tall</SelectItem><SelectItem value="screen">Full screen</SelectItem></SelectContent></Select></div>
        <label class="sm:col-span-2"><span class="field-label">Heading</span><Input v-model="hero.heading" maxlength="180" /></label>
        <label class="sm:col-span-2"><span class="field-label">Supporting text</span><Textarea v-model="hero.description" maxlength="600" rows="3" /></label>
        <label><span class="field-label">Primary action label</span><Input v-model="hero.primary_cta_label" maxlength="80" /></label><label><span class="field-label">Primary action URL</span><Input v-model="hero.primary_cta_url" placeholder="/shop" /></label>
        <label><span class="field-label">Secondary action label</span><Input v-model="hero.secondary_cta_label" maxlength="80" /></label><label><span class="field-label">Secondary action URL</span><Input v-model="hero.secondary_cta_url" placeholder="/about" /></label>
        <div><span class="field-label">Text alignment</span><Select v-model="hero.alignment"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="left">Left</SelectItem><SelectItem value="center">Center</SelectItem><SelectItem value="right">Right</SelectItem></SelectContent></Select></div>
        <div><span class="field-label">Content position</span><Select v-model="hero.position"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="center_left">Center left</SelectItem><SelectItem value="center">Center</SelectItem><SelectItem value="center_right">Center right</SelectItem><SelectItem value="bottom_left">Bottom left</SelectItem><SelectItem value="bottom_center">Bottom center</SelectItem><SelectItem value="bottom_right">Bottom right</SelectItem></SelectContent></Select></div>
        <template v-if="hero.type === 'color'"><label><span class="field-label">Hero color</span><Input v-model="hero.background_color" type="color" class="h-11 p-1" /></label></template>
        <template v-if="hero.type === 'gradient'"><label><span class="field-label">Gradient start</span><Input v-model="hero.gradient_from" type="color" class="h-11 p-1" /></label><label><span class="field-label">Gradient end</span><Input v-model="hero.gradient_to" type="color" class="h-11 p-1" /></label><label><span class="field-label">Angle</span><Input v-model.number="hero.gradient_angle" type="number" min="0" max="360" /></label></template>
        <div v-if="['image', 'video', 'three'].includes(hero.type)" class="sm:col-span-2"><span class="field-label">Hero media</span><Select :model-value="hero.asset_id || 'none'" @update:model-value="hero.asset_id = $event === 'none' ? '' : $event"><SelectTrigger><SelectValue placeholder="Choose media" /></SelectTrigger><SelectContent><SelectItem value="none">No media selected</SelectItem><SelectItem v-for="asset in heroAssets" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</SelectItem></SelectContent></Select><p class="mt-2 text-xs text-muted-foreground">Upload approved images, MP4/WebM video, or GLB models in Site → Media.</p></div>
        <div v-if="['video', 'three'].includes(hero.type)" class="sm:col-span-2"><span class="field-label">Poster fallback</span><Select :model-value="hero.poster_asset_id || 'none'" @update:model-value="hero.poster_asset_id = $event === 'none' ? '' : $event"><SelectTrigger><SelectValue placeholder="Choose an image" /></SelectTrigger><SelectContent><SelectItem value="none">Use business cover</SelectItem><SelectItem v-for="asset in imageAssets" :key="asset.public_id" :value="asset.public_id">{{ asset.title }}</SelectItem></SelectContent></Select></div>
        <div v-if="hero.type === 'three'"><span class="field-label">Motion</span><Select v-model="hero.motion"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">Still</SelectItem><SelectItem value="rotate">Slow rotation</SelectItem><SelectItem value="interactive">Pointer interaction</SelectItem></SelectContent></Select></div>
        <label><span class="field-label">Overlay color</span><Input v-model="hero.overlay_color" type="color" class="h-11 p-1" /></label><label><span class="field-label">Overlay opacity · {{ Math.round(hero.overlay_opacity * 100) }}%</span><Input v-model.number="hero.overlay_opacity" type="range" min="0" max="0.9" step="0.05" class="shadow-none" /></label>
      </div>
    </fieldset>
  </div>
</template>

<script setup>
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import IdentityMarketplaceHeroSettings from './IdentityMarketplaceHeroSettings.vue'
defineEmits(['uploaded'])
const props = defineProps({ form: { type: Object, required: true }, assets: { type: Array, default: () => [] } })
const background = computed(() => props.form.branding.storefront.background)
const hero = computed(() => props.form.branding.storefront.hero)
const imageAssets = computed(() => props.assets.filter((asset) => asset.asset_type === 'image' && asset.processing_status === 'ready'))
const heroAssets = computed(() => props.assets.filter((asset) => asset.asset_type === ({ image: 'image', video: 'video', three: 'model' }[hero.value.type]) && asset.processing_status === 'ready'))
</script>
