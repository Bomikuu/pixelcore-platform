<template>
  <aside
    v-if="visible"
    class="fixed inset-x-4 bottom-4 z-40 mx-auto max-w-2xl border border-foreground/10 bg-foreground px-4 py-3 text-background shadow-[0_18px_50px_rgba(0,0,0,0.22)] sm:bottom-6 sm:flex sm:items-center sm:gap-4 sm:px-5"
    role="status"
    aria-label="Store announcement"
  >
    <div class="flex min-w-0 flex-1 items-start gap-3">
      <span class="mt-0.5 grid h-8 w-8 shrink-0 place-items-center bg-background/10" aria-hidden="true"><Megaphone class="h-4 w-4" /></span>
      <div class="min-w-0">
        <p class="font-bold leading-6">{{ settings.message }}</p>
        <a v-if="settings.label" :href="href" class="mt-1 inline-flex items-center gap-1 text-sm font-semibold text-background/75 underline decoration-background/30 underline-offset-4 transition-colors hover:text-background">
          {{ settings.label }}<ArrowUpRight class="h-3.5 w-3.5" aria-hidden="true" />
        </a>
      </div>
    </div>
    <Button type="button" variant="ghost" size="icon" class="absolute right-2 top-2 text-background hover:bg-background/10 hover:text-background sm:static" aria-label="Dismiss announcement" @click="dismiss">
      <X class="h-4 w-4" />
    </Button>
  </aside>
</template>

<script setup>
import { ArrowUpRight, Megaphone, X } from 'lucide-vue-next'

const props = defineProps({ settings: { type: Object, required: true }, href: { type: String, required: true }, storageKey: { type: String, required: true } })
const visible = ref(true)

onMounted(() => {
  try { visible.value = sessionStorage.getItem(props.storageKey) !== 'dismissed' } catch {}
})

function dismiss() {
  visible.value = false
  try { sessionStorage.setItem(props.storageKey, 'dismissed') } catch {}
}
</script>
