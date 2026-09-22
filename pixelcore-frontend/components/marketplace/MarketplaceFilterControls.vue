<template>
  <form class="space-y-5" @submit.prevent="apply">
    <div class="flex items-center justify-between gap-3">
      <h2 class="flex items-center gap-2 text-base font-semibold">
        <SlidersHorizontal class="h-4 w-4" aria-hidden="true" />
        Filters
        <Badge v-if="selectedCount" variant="secondary">{{ selectedCount }}</Badge>
      </h2>
      <Button type="button" variant="link" class="h-auto p-0 text-xs" @click="$emit('clear')">Reset all</Button>
    </div>

    <div>
      <Label :for="`${id}-search`">Search products</Label>
      <div class="relative mt-2">
        <Search class="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" aria-hidden="true" />
        <Input :id="`${id}-search`" v-model="model.search" class="pl-9" placeholder="Name or brand" />
      </div>
    </div>

    <Accordion type="multiple" :default-value="['categories', 'price', 'collections', 'availability']">
      <AccordionItem value="categories">
        <AccordionTrigger class="py-4 text-sm">Category</AccordionTrigger>
        <AccordionContent>
          <Input v-if="categories.length > 7" v-model="categorySearch" placeholder="Find a category" aria-label="Find a category" class="mb-3" />
          <div class="max-h-64 space-y-1 overflow-y-auto overscroll-contain">
            <Button
              type="button"
              variant="ghost"
              class="h-10 w-full justify-between gap-2 rounded-md px-2 text-sm font-normal"
              :class="!model.category || model.category === 'all' ? 'bg-secondary font-semibold text-primary' : ''"
              :aria-pressed="!model.category || model.category === 'all'"
              @click="model.category = ''"
            >
              All categories
              <Check v-if="!model.category || model.category === 'all'" class="h-4 w-4" aria-hidden="true" />
            </Button>
            <Button
              v-for="item in visibleCategories"
              :key="item.slug"
              type="button"
              variant="ghost"
              class="h-auto min-h-11 w-full justify-start gap-2 rounded-md px-2 text-left text-sm font-normal"
              :class="model.category === item.slug ? 'bg-secondary font-semibold text-primary' : ''"
              :aria-pressed="model.category === item.slug"
              @click="model.category = item.slug"
            >
              <img v-if="item.image" :src="item.image" alt="" class="h-7 w-7 shrink-0 rounded-full object-cover" />
              <span class="whitespace-normal">{{ item.name }}</span>
              <Check v-if="model.category === item.slug" class="ml-auto h-4 w-4 shrink-0" aria-hidden="true" />
            </Button>
            <p v-if="!visibleCategories.length" class="py-3 text-xs text-muted-foreground">No matching categories.</p>
          </div>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="price">
        <AccordionTrigger class="py-4 text-sm">Price range · {{ currency }}</AccordionTrigger>
        <AccordionContent>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <Label :for="`${id}-min`" class="text-xs text-muted-foreground">Minimum</Label>
              <Input :id="`${id}-min`" v-model="model.price_min" class="mt-1.5" type="number" min="0" step="0.01" placeholder="Any" />
            </div>
            <div>
              <Label :for="`${id}-max`" class="text-xs text-muted-foreground">Maximum</Label>
              <Input :id="`${id}-max`" v-model="model.price_max" class="mt-1.5" type="number" min="0" step="0.01" placeholder="Any" />
            </div>
          </div>
          <p v-if="priceError" role="alert" class="mt-2 text-xs text-destructive">{{ priceError }}</p>
          <p v-else-if="catalog?.facets?.price?.min != null" class="mt-3 text-xs leading-5 text-muted-foreground">
            Current results: {{ money(catalog.facets.price.min) }} – {{ money(catalog.facets.price.max) }}
          </p>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem v-if="catalog?.facets?.collections?.length" value="collections">
        <AccordionTrigger class="py-4 text-sm">Collection</AccordionTrigger>
        <AccordionContent class="space-y-1">
          <label
            v-for="item in catalog.facets.collections"
            :key="item.slug"
            class="flex min-h-10 cursor-pointer items-center gap-3 text-sm"
          >
            <NativeRadio v-model="model.collection" :value="item.slug" :name="`${id}-collection`" />
            {{ item.name }}
          </label>
          <Button v-if="model.collection" type="button" variant="link" class="h-auto p-0 text-xs" @click="model.collection = ''">Clear collection</Button>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="availability">
        <AccordionTrigger class="py-4 text-sm">Availability</AccordionTrigger>
        <AccordionContent>
          <label class="flex min-h-10 cursor-pointer items-center gap-3 text-sm">
            <Checkbox
              :checked="model.availability === 'in_stock'"
              @update:checked="model.availability = $event ? 'in_stock' : ''"
            />
            In stock only
          </label>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
    <div class="sticky bottom-0 border-t bg-background pb-1 pt-4">
      <Button type="submit" class="h-11 w-full gap-2" :disabled="Boolean(priceError)">
        Show results
        <ArrowRight class="h-4 w-4" aria-hidden="true" />
      </Button>
    </div>
  </form>
</template>

<script setup>
import { ArrowRight, Check, Search, SlidersHorizontal } from 'lucide-vue-next'

const props = defineProps({
  catalog: { type: Object, default: null },
  currency: { type: String, default: 'PHP' },
})
const emit = defineEmits(['apply', 'clear'])
const model = defineModel({ type: Object, required: true })
const id = useId()
const categorySearch = ref('')
const categories = computed(() => props.catalog?.facets?.categories || [])
const visibleCategories = computed(() => categories.value.filter(
  (item) => item.name.toLowerCase().includes(categorySearch.value.toLowerCase()),
))
const selectedCount = computed(() => Object.entries(model.value).filter(
  ([key, value]) => key !== 'ordering' && value !== '' && value != null && value !== 'all',
).length)
const priceError = computed(() => {
  const minimum = model.value.price_min
  const maximum = model.value.price_max
  if (minimum !== '' && maximum !== '' && Number(minimum) > Number(maximum)) {
    return 'Maximum price must be equal to or greater than minimum.'
  }
  return ''
})
function money(value) {
  return new Intl.NumberFormat('en-PH', { style: 'currency', currency: props.currency }).format(Number(value || 0))
}
function apply() {
  if (!priceError.value) emit('apply')
}
</script>
