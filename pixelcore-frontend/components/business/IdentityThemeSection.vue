<template>
  <div class="space-y-8">
    <header><h2 class="text-xl font-extrabold">Colors & typography</h2><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Set a dependable palette and a restrained type system. Contrast remains visible in the preview while you work.</p></header>
    <fieldset class="space-y-4"><legend class="font-extrabold">Color roles</legend><div class="grid gap-4 sm:grid-cols-2"><label v-for="color in colors" :key="color.key"><span class="field-label">{{ color.label }}</span><span class="flex min-h-11 items-center gap-2 rounded-[var(--input-radius)] border bg-background p-2"><Input v-model="form.branding[color.key]" type="color" class="h-8 w-10 cursor-pointer border-0 bg-transparent p-0 shadow-none" :aria-label="`${color.label} color picker`" /><Input v-model.trim="form.branding[color.key]" pattern="#[0-9A-Fa-f]{6}" class="h-8 min-w-0 flex-1 border-0 bg-transparent uppercase shadow-none" :aria-label="`${color.label} hexadecimal color`" /></span><span class="mt-1 block text-xs text-muted-foreground">{{ color.help }}</span></label></div></fieldset>
    <fieldset class="space-y-4 border-t pt-7"><legend class="font-extrabold">Typography</legend><div class="grid gap-4 sm:grid-cols-2">
      <div><span class="field-label">Primary font</span><Select v-model="form.branding.typography.primary_font"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="font in fonts" :key="font" :value="font">{{ font }}</SelectItem></SelectContent></Select></div>
      <div><span class="field-label">Heading font</span><Select v-model="form.branding.typography.heading_font"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="font in fonts" :key="font" :value="font">{{ font }}</SelectItem></SelectContent></Select></div>
      <div><span class="field-label">Body weight</span><Select v-model="bodyWeight"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="400">Regular</SelectItem><SelectItem value="500">Medium</SelectItem><SelectItem value="600">Semibold</SelectItem></SelectContent></Select></div>
      <div><span class="field-label">Heading weight</span><Select v-model="headingWeight"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="600">Semibold</SelectItem><SelectItem value="700">Bold</SelectItem><SelectItem value="800">Extra bold</SelectItem></SelectContent></Select></div>
      <div><span class="field-label">Base font size</span><Select v-model="form.branding.typography.base_font_size"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="14px">Compact · 14 px</SelectItem><SelectItem value="15px">Dense · 15 px</SelectItem><SelectItem value="16px">Standard · 16 px</SelectItem><SelectItem value="18px">Comfortable · 18 px</SelectItem></SelectContent></Select></div>
    </div></fieldset>
  </div>
</template>

<script setup>
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
const props = defineProps({ form: { type: Object, required: true } })
const fonts = ['Manrope', 'Newsreader', 'Plus Jakarta Sans', 'Inter', 'Poppins', 'Montserrat', 'Playfair Display', 'system-ui']
const colors = [
  { key: 'primary_color', label: 'Primary', help: 'Actions, active states, and charts.' }, { key: 'secondary_color', label: 'Secondary', help: 'Strong brand surfaces and workspace navigation.' }, { key: 'accent_color', label: 'Accent', help: 'Sparing highlights and emphasis.' }, { key: 'background_color', label: 'Background', help: 'Default storefront canvas.' }, { key: 'text_color', label: 'Text', help: 'Primary reading color.' }, { key: 'muted_text_color', label: 'Muted text', help: 'Supporting descriptions and labels.' }, { key: 'link_color', label: 'Links', help: 'Text links and quiet actions.' },
]
const bodyWeight = computed({ get: () => String(props.form.branding.typography.body_weight), set: (value) => { props.form.branding.typography.body_weight = Number(value) } })
const headingWeight = computed({ get: () => String(props.form.branding.typography.heading_weight), set: (value) => { props.form.branding.typography.heading_weight = Number(value) } })
</script>
