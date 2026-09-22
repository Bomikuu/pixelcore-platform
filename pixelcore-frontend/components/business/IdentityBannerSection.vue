<template>
  <div class="space-y-8"><header><h2 class="text-xl font-extrabold">Storefront banner</h2><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">A single concise promotion, announcement, shipping notice, or important message across the storefront.</p></header>
    <fieldset class="space-y-5"><div class="flex items-start justify-between gap-5"><div><legend class="font-extrabold">Banner visibility</legend><p class="mt-1 text-sm text-muted-foreground">Show one site-wide banner.</p></div><Switch v-model:checked="banner.enabled" aria-label="Enable storefront banner" /></div>
      <div v-if="banner.enabled" class="grid gap-4 sm:grid-cols-2"><label class="sm:col-span-2"><span class="field-label">Message</span><Input v-model="banner.text" maxlength="240" /></label><label><span class="field-label">Link label</span><Input v-model="banner.link_label" maxlength="80" /></label><label><span class="field-label">Link URL</span><Input v-model="banner.link_url" placeholder="/shop" /></label><label><span class="field-label">Background</span><Input v-model="banner.background_color" type="color" class="h-11 p-1" /></label><label><span class="field-label">Text</span><Input v-model="banner.text_color" type="color" class="h-11 p-1" /></label></div>
    </fieldset>
    <section class="border bg-muted/30 p-4 sm:p-6" aria-labelledby="banner-preview-heading"><div class="flex items-center justify-between"><div><h3 id="banner-preview-heading" class="font-extrabold">Storefront preview</h3><p class="mt-1 text-xs text-muted-foreground">The announcement spans the storefront above the main header and remains dismissible.</p></div><Eye class="h-5 w-5 text-primary" /></div><div class="relative mt-5 min-h-56 overflow-hidden border bg-background"><div class="relative flex min-h-10 items-center justify-center gap-2 px-10 py-2 text-center text-xs font-bold" :style="{ backgroundColor: banner.background_color, color: banner.text_color }"><Megaphone class="h-3.5 w-3.5" /><span>{{ banner.text || 'Your storefront announcement' }}</span><span v-if="banner.link_label" class="underline">{{ banner.link_label }}</span><X class="absolute right-3 h-3.5 w-3.5" /></div><div class="h-14 border-b" /><div class="mx-auto mt-8 h-3 w-2/5 bg-muted" /><div class="mx-auto mt-3 h-2 w-3/5 bg-muted" /></div></section>
  </div>
</template>
<script setup>
import { Eye, Megaphone, X } from 'lucide-vue-next'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
const props = defineProps({ form: { type: Object, required: true } })
const banner = computed(() => props.form.branding.storefront.banner)
watchEffect(() => { banner.value.dismissible = true; banner.value.position = 'top' })
</script>
