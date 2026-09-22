<template>
  <section class="rounded-xl border bg-card p-4 sm:p-5" aria-labelledby="operations-guide-title">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
      <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground">
        <component :is="icon" class="h-5 w-5" aria-hidden="true" />
      </span>
      <div class="min-w-0 flex-1">
        <h2 id="operations-guide-title" class="font-semibold leading-6">{{ title }}</h2>
        <p class="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{{ description }}</p>
      </div>
      <div class="flex shrink-0 gap-2 sm:ml-auto">
        <Button type="button" class="h-10 flex-1 gap-2 sm:flex-none" @click="learnMoreOpen = true">
          Learn more
          <ArrowUpRight class="h-4 w-4" aria-hidden="true" />
        </Button>
        <Button
          type="button"
          variant="outline"
          class="h-10 flex-1 gap-2 sm:flex-none"
          aria-label="Dismiss this explanation until the page is refreshed"
          @click="$emit('dismiss')"
        >
          <X class="h-4 w-4" aria-hidden="true" />
          Dismiss
        </Button>
      </div>
    </div>
  </section>

  <Dialog v-model:open="learnMoreOpen">
    <DialogContent class="flex max-h-[calc(100dvh-2rem)] flex-col overflow-hidden p-0 sm:max-w-2xl">
      <DialogHeader class="shrink-0 border-b px-6 py-5 pr-14">
        <DialogTitle class="flex items-center gap-3 text-xl">
          <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground">
            <component :is="icon" class="h-5 w-5" aria-hidden="true" />
          </span>
          {{ title }}
        </DialogTitle>
        <DialogDescription class="max-w-2xl pt-1 leading-6">{{ description }}</DialogDescription>
      </DialogHeader>

      <div class="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        <h3 class="font-semibold">How it works</h3>
        <p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">Each stage changes what the team can see or do next. Open the related record when a stage needs attention.</p>
        <ol v-if="workflowItems.length" class="mt-6" aria-label="Connected workflow">
          <li v-for="(item, index) in workflowItems" :key="`${item.label}-${index}`">
            <div class="flex items-start gap-4">
              <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl border bg-muted/30 text-primary">
                <component :is="stepIcon(item.label)" class="h-6 w-6" aria-hidden="true" />
              </span>
              <div class="min-w-0 pt-0.5">
                <h4 class="font-semibold leading-6">{{ item.label }}</h4>
                <p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">{{ item.detail }}</p>
              </div>
            </div>
            <div v-if="index < workflowItems.length - 1" class="ml-6 h-6 w-px bg-border" aria-hidden="true" />
          </li>
        </ol>
      </div>

      <DialogFooter class="shrink-0 border-t bg-muted/20 px-6 py-4">
        <Button type="button" @click="learnMoreOpen = false">Got it</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import {
  ArrowUpRight,
  BarChart3,
  Boxes,
  Building2,
  CircleDollarSign,
  CreditCard,
  FileText,
  Info,
  PackageCheck,
  PackageSearch,
  ReceiptText,
  ShoppingCart,
  Tags,
  UserRound,
  X,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  connection: { type: String, default: '' },
  details: { type: Array, default: () => [] },
  icon: { type: [Object, Function], default: Info },
})
defineEmits(['dismiss'])

const learnMoreOpen = ref(false)
const workflowSteps = computed(() => props.connection.split('→').map(step => step.trim()).filter(Boolean))
const workflowItems = computed(() => workflowSteps.value.map((label, index) => ({
  label,
  detail: props.details[index] || 'Review this stage before moving to the next connected record.',
})))

function stepIcon(step) {
  const value = step.toLowerCase()
  if (value.includes('supplier')) return Building2
  if (value.includes('inventory') || value.includes('stock')) return Boxes
  if (value.includes('receiv')) return PackageCheck
  if (value.includes('purchase order')) return ShoppingCart
  if (value.includes('product') || value.includes('variant') || value.includes('catalog')) return PackageSearch
  if (value.includes('customer')) return UserRound
  if (value.includes('payment')) return CreditCard
  if (value.includes('expense')) return ReceiptText
  if (value.includes('category')) return Tags
  if (value.includes('report') || value.includes('summary')) return BarChart3
  if (value.includes('invoice') || value.includes('quotation') || value.includes('order')) return FileText
  if (value.includes('cost') || value.includes('sales')) return CircleDollarSign
  return Info
}
</script>
