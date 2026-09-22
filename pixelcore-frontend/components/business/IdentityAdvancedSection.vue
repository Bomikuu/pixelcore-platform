<template>
  <div class="space-y-8"><header><h2 class="text-xl font-extrabold">Advanced</h2><p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">Add one isolated branding section or move the complete identity configuration between businesses using validated JSON.</p></header>
    <fieldset class="space-y-4"><legend class="font-extrabold">Additional storefront content</legend><label><span class="field-label">Custom HTML</span><Textarea v-model="advanced.custom_html" rows="8" class="font-mono text-xs" placeholder="<section class=&quot;brand-note&quot;>...</section>" /></label><label><span class="field-label">Scoped CSS</span><Textarea v-model="advanced.custom_css" rows="8" class="font-mono text-xs" placeholder=".brand-note { padding: 2rem; }" /></label><Alert><ShieldCheck class="h-4 w-4" /><AlertTitle>Isolated customization</AlertTitle><AlertDescription>Safe text markup is sanitized on save and rendered in a sandboxed frame. JavaScript, forms, remote resources, and selectors that can alter PixelCore controls are not available.</AlertDescription></Alert></fieldset>
    <fieldset class="space-y-4 border-t pt-7"><legend class="font-extrabold">JSON configuration</legend><p class="text-sm leading-6 text-muted-foreground">The visual editor and JSON file represent the same schema. Imported changes remain unsaved until you use the page’s Save identity action.</p><div class="flex flex-wrap gap-3"><Button type="button" variant="outline" @click="$emit('export-config')"><Download class="h-4 w-4" /> Export JSON</Button><Button as-child type="button" variant="outline"><label class="cursor-pointer" for="identity-json-import"><Upload class="h-4 w-4" /> Import JSON</label></Button><Input id="identity-json-import" type="file" accept="application/json,.json" class="sr-only" @change="importFile" /></div><p v-if="importError" class="text-sm text-destructive" role="alert">{{ importError }}</p></fieldset>
    <fieldset class="space-y-4 border-t pt-7"><legend class="font-extrabold">Restore defaults</legend><p class="text-sm leading-6 text-muted-foreground">Reset appearance settings while preserving business details, uploaded media, products, pages, and operational records.</p><Dialog v-model:open="resetOpen"><DialogTrigger as-child><Button type="button" variant="outline"><RotateCcw class="h-4 w-4" /> Restore appearance defaults</Button></DialogTrigger><DialogContent><DialogHeader><DialogTitle>Restore default appearance?</DialogTitle><DialogDescription>This replaces colors, typography, component styling, storefront appearance, social links, and workspace branding in the editor. Save identity to make the reset permanent.</DialogDescription></DialogHeader><DialogFooter><Button type="button" variant="outline" @click="resetOpen = false">Cancel</Button><Button type="button" @click="$emit('reset-config'); resetOpen = false">Restore defaults</Button></DialogFooter></DialogContent></Dialog></fieldset>
  </div>
</template>
<script setup>
import { Download, RotateCcw, ShieldCheck, Upload } from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
const props = defineProps({ form: { type: Object, required: true } })
const emit = defineEmits(['export-config', 'import-config', 'reset-config'])
const advanced = computed(() => props.form.branding.advanced)
const importError = ref('')
const resetOpen = ref(false)
async function importFile(event) { const file = event.target.files?.[0]; event.target.value = ''; if (!file) return; try { const payload = JSON.parse(await file.text()); emit('import-config', payload); importError.value = '' } catch { importError.value = 'Choose a valid PixelCore identity JSON file.' } }
</script>
