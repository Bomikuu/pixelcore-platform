<template>
  <Dialog :open="open" @update:open="handleOpen">
    <DialogContent
      class="max-h-[90dvh] w-[calc(100%-2rem)] overflow-y-auto p-0 [&>button]:rounded-full [&>button]:bg-background [&>button]:p-2 [&>button]:text-foreground [&>button]:opacity-100"
      :class="[widthClass, popup.dismissible || preview ? '' : '[&>button]:hidden']"
      :style="popupStyle"
      @escape-key-down="preventDismiss"
      @interact-outside="preventDismiss"
    >
      <div :class="popup.layout === 'split' && image && !posterOnly ? 'grid sm:grid-cols-2' : ''">
        <div v-if="image" :class="posterOnly ? '' : popup.layout === 'split' ? 'min-h-48' : 'aspect-[2/1] overflow-hidden'">
          <a v-if="posterOnly && popup.cta_url" :href="resolveLink(popup.cta_url)" :aria-label="popup.cta_text || popup.title || 'View promotion'" @click="followLink">
            <img :src="image.url" :alt="popup.title || image.title || 'Store promotion'" class="max-h-[80dvh] w-full object-contain" />
          </a>
          <img v-else :src="image.url" :alt="posterOnly ? popup.title || image.title || 'Store promotion' : ''" :class="posterOnly ? 'max-h-[80dvh] w-full object-contain' : 'h-full w-full object-cover'" />
        </div>
        <div :class="posterOnly ? 'sr-only' : 'flex flex-col justify-center p-6 sm:p-8'">
          <DialogHeader v-if="popup.mode !== 'custom'">
            <DialogTitle class="text-2xl">{{ popup.title || 'From the store' }}</DialogTitle>
            <DialogDescription v-if="popup.description" class="pt-2 text-current">{{ popup.description }}</DialogDescription>
            <DialogDescription v-else class="sr-only">A promotion from {{ identity.display_name }}</DialogDescription>
          </DialogHeader>
          <template v-else>
            <DialogHeader class="sr-only">
              <DialogTitle>{{ popup.title || 'Store promotion' }}</DialogTitle>
              <DialogDescription>Custom campaign content from {{ identity.display_name }}</DialogDescription>
            </DialogHeader>
            <SandboxedCustomization :html="popup.custom_html" :css="popup.custom_css" title="Custom popup content" height-class="h-64" />
          </template>
          <ButtonAnchor v-if="!posterOnly && popup.mode !== 'custom' && popup.cta_text && popup.cta_url" :href="resolveLink(popup.cta_url)" class="mt-6 w-fit gap-2" @click="followLink">
            {{ popup.cta_text }}
          </ButtonAnchor>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ButtonAnchor } from '@/components/ui/button-anchor'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { businessThemeStyle } from '@/utils/businessTheme'
import SandboxedCustomization from '@/components/business/SandboxedCustomization.vue'

const props = defineProps({
  identity: { type: Object, required: true },
  base: { type: String, required: true },
  preview: { type: Boolean, default: false },
})
const emit = defineEmits(['closed'])
const route = useRoute()
const open = ref(false)
let timer
const popup = computed(() => props.identity.branding?.storefront?.popup || {})
const image = computed(() => props.identity.branding_assets?.[popup.value.asset_id])
const posterOnly = computed(() => popup.value.mode !== 'custom' && popup.value.layout === 'poster' && Boolean(image.value))
const widthClass = computed(() => ({
  small: 'sm:max-w-sm',
  medium: 'sm:max-w-xl',
  large: 'sm:max-w-3xl',
}[popup.value.size] || 'sm:max-w-xl'))
const popupStyle = computed(() => ({
  ...businessThemeStyle(props.identity),
  borderRadius: { none: '0', small: '4px', medium: '8px', large: '12px', pill: '24px' }[popup.value.border_radius] || '12px',
  backgroundColor: popup.value.background_color,
  color: popup.value.text_color,
}))
// A changed campaign should not inherit an older campaign's dismissal.
const storageKey = computed(() => {
  const content = JSON.stringify(popup.value)
  let hash = 0
  for (let index = 0; index < content.length; index++) hash = ((hash << 5) - hash + content.charCodeAt(index)) | 0
  return `pixelcore-popup:${props.identity.slug}:${hash}`
})

function wasSeen() {
  if (popup.value.frequency === 'always') return false
  try {
    const storage = popup.value.frequency === 'daily' ? localStorage : sessionStorage
    const value = storage.getItem(storageKey.value)
    return popup.value.frequency === 'daily' ? value && Date.now() - Number(value) < 86400000 : Boolean(value)
  } catch {
    return false
  }
}

function remember() {
  if (props.preview || popup.value.frequency === 'always') return
  try {
    const storage = popup.value.frequency === 'daily' ? localStorage : sessionStorage
    storage.setItem(storageKey.value, String(Date.now()))
  } catch {
    // Storage restrictions must not prevent the visitor from closing a popup.
  }
}

function schedule() {
  clearTimeout(timer)
  open.value = false
  if (props.preview) {
    open.value = true
    return
  }
  const path = route.path.replace(/\/$/, '') || '/'
  const homePath = props.base.replace(/\/$/, '') || '/'
  if (!popup.value.enabled || (popup.value.home_only && path !== homePath) || wasSeen()) return
  timer = setTimeout(() => {
    open.value = true
    remember()
  }, Math.max(0, Number(popup.value.display_delay || 0)) * 1000)
}

onMounted(schedule)
watch([() => route.path, storageKey], () => {
  if (import.meta.client) schedule()
})
onBeforeUnmount(() => clearTimeout(timer))

function handleOpen(value) {
  if (value) return
  if (!popup.value.dismissible && !props.preview) return
  open.value = false
  remember()
  emit('closed')
}

function preventDismiss(event) {
  if (!popup.value.dismissible && !props.preview) event.preventDefault()
}

function followLink(event) {
  if (props.preview) {
    event.preventDefault()
    return
  }
  open.value = false
  remember()
}

function resolveLink(value) {
  return value?.startsWith('/') ? `${props.base}${value === '/' ? '' : value}` : value
}
</script>
