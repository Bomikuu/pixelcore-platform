<template>
  <div class="space-y-8"><header><h2 class="text-xl font-extrabold">Social media</h2><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Only configured profiles appear publicly. Platform names stay generic so the list can grow with your business.</p></header>
    <div class="flex justify-end"><Button type="button" :disabled="socials.length >= 8" @click="socials.push({ platform: 'instagram', url: '' })"><Plus class="h-4 w-4" /> Add profile</Button></div>
    <div v-if="socials.length" class="divide-y border-y"><div v-for="(social, index) in socials" :key="index" class="grid gap-3 py-4 sm:grid-cols-[12rem_1fr_auto] sm:items-end"><div><span class="field-label">Platform</span><Select v-model="social.platform"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="platform in platforms" :key="platform.value" :value="platform.value">{{ platform.label }}</SelectItem></SelectContent></Select></div><label><span class="field-label">HTTPS profile URL</span><Input v-model="social.url" type="url" placeholder="https://..." /></label><Button type="button" variant="ghost" size="icon" :aria-label="`Remove ${social.platform} profile`" @click="socials.splice(index, 1)"><Trash2 class="h-4 w-4" /></Button></div></div>
    <div v-else class="rounded-[var(--card-radius)] bg-muted px-6 py-10 text-center"><Share2 class="mx-auto h-6 w-6 text-muted-foreground" aria-hidden="true" /><p class="mt-3 font-bold">No social profiles configured</p><p class="mt-1 text-sm text-muted-foreground">Add only the channels your business actively maintains.</p></div>
  </div>
</template>
<script setup>
import { Plus, Share2, Trash2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
const props = defineProps({ form: { type: Object, required: true } })
const socials = computed(() => props.form.branding.socials)
const platforms = [{ value: 'facebook', label: 'Facebook' }, { value: 'instagram', label: 'Instagram' }, { value: 'tiktok', label: 'TikTok' }, { value: 'x', label: 'X / Twitter' }, { value: 'youtube', label: 'YouTube' }, { value: 'linkedin', label: 'LinkedIn' }]
</script>
