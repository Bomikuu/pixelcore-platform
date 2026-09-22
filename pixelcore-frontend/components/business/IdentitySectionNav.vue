<template>
  <nav class="flex gap-1 overflow-x-auto pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden lg:sticky lg:top-16 lg:block lg:space-y-1 lg:overflow-visible lg:pb-0" aria-label="Appearance sections">
    <Button
      v-for="section in sections"
      :key="section.id"
      type="button"
      variant="ghost"
      class="h-10 shrink-0 justify-start gap-3 px-3 text-muted-foreground lg:w-full"
      :class="modelValue === section.id ? 'bg-secondary text-foreground' : ''"
      :aria-current="modelValue === section.id ? 'page' : undefined"
      @click="$emit('update:modelValue', section.id)"
    >
      <component :is="section.icon" class="h-4 w-4 shrink-0" :class="modelValue === section.id ? 'text-primary' : ''" aria-hidden="true" />
      {{ section.label }}
    </Button>
  </nav>
</template>

<script setup>
import { Brush, Code2, Component, Flag, Image, LayoutPanelTop, Megaphone, MonitorCog, Share2, Store, UsersRound } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

defineProps({ modelValue: { type: String, required: true } })
defineEmits(['update:modelValue'])

const sections = [
  { id: 'branding', label: 'Branding', icon: Brush },
  { id: 'storefront', label: 'Shop layout', icon: Store },
  { id: 'theme', label: 'Colors & type', icon: Image },
  { id: 'components', label: 'Components', icon: Component },
  { id: 'hero', label: 'Hero & background', icon: LayoutPanelTop },
  { id: 'banner', label: 'Banner', icon: Flag },
  { id: 'popup', label: 'Popup', icon: Megaphone },
  { id: 'footer', label: 'Footer', icon: Share2 },
  { id: 'socials', label: 'Social media', icon: UsersRound },
  { id: 'workspace', label: 'Workspace', icon: MonitorCog },
  { id: 'advanced', label: 'Advanced', icon: Code2 },
]
</script>
