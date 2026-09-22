<template>
  <div class="space-y-8">
    <header><h2 class="text-xl font-extrabold">Component character</h2><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Choose how sharp or soft common controls feel without styling every page independently.</p></header>
    <fieldset class="space-y-4"><legend class="font-extrabold">Corner shape</legend><div class="grid gap-4 sm:grid-cols-2"><div v-for="field in radiusFields" :key="field.key"><span class="field-label">{{ field.label }}</span><Select v-model="form.branding.style[field.key]"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="option in radii" :key="option.value" :value="option.value">{{ option.label }}</SelectItem></SelectContent></Select><p class="mt-1 text-xs text-muted-foreground">{{ field.help }}</p></div></div></fieldset>
    <fieldset class="space-y-4 border-t pt-7"><legend class="font-extrabold">Surface details</legend><div class="grid gap-4 sm:grid-cols-2">
      <div><span class="field-label">Border thickness</span><Select v-model="form.branding.style.border_width"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">None</SelectItem><SelectItem value="thin">Thin</SelectItem><SelectItem value="medium">Medium</SelectItem></SelectContent></Select></div>
      <div><span class="field-label">Shadow intensity</span><Select v-model="form.branding.style.shadow_intensity"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="none">None</SelectItem><SelectItem value="subtle">Subtle</SelectItem><SelectItem value="medium">Medium</SelectItem></SelectContent></Select></div>
      <div><span class="field-label">Content width</span><Select v-model="form.branding.style.content_width"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="compact">Compact</SelectItem><SelectItem value="standard">Standard</SelectItem><SelectItem value="wide">Wide</SelectItem><SelectItem value="full">Full width</SelectItem></SelectContent></Select></div>
    </div></fieldset>
  </div>
</template>

<script setup>
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
defineProps({ form: { type: Object, required: true } })
const radii = [{ value: 'none', label: 'Sharp' }, { value: 'small', label: 'Slightly rounded' }, { value: 'medium', label: 'Rounded' }, { value: 'large', label: 'Soft' }, { value: 'pill', label: 'Pill' }]
const radiusFields = [
  { key: 'button_radius', label: 'Buttons', help: 'Primary and secondary actions.' }, { key: 'card_radius', label: 'Cards', help: 'Grouped content and summaries.' }, { key: 'input_radius', label: 'Inputs', help: 'Fields, selectors, and text areas.' }, { key: 'modal_radius', label: 'Dialogs', help: 'Focused tasks and confirmations.' },
]
</script>
