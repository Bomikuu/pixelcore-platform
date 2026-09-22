<template>
  <div class="space-y-5">
    <section class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-3">
      <div class="border-b p-4 sm:border-b-0 sm:border-r">
        <p class="text-sm text-muted-foreground">Selected for this event</p>
        <p class="mt-1 text-2xl font-bold tabular-nums">{{ selectedIds.length }}</p>
      </div>
      <div class="border-b p-4 sm:border-b-0 sm:border-r">
        <p class="text-sm text-muted-foreground">Products</p>
        <p class="mt-1 text-2xl font-bold tabular-nums">{{ selectedTypeCount('physical') }}</p>
      </div>
      <div class="p-4">
        <p class="text-sm text-muted-foreground">Services</p>
        <p class="mt-1 text-2xl font-bold tabular-nums">{{ selectedTypeCount('service') }}</p>
      </div>
    </section>

    <Card>
      <CardHeader class="border-b p-5">
        <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
          <div>
            <CardTitle class="text-lg">Products and services</CardTitle>
            <CardDescription>Attach catalog items used, sold, served, or prepared for this event.</CardDescription>
          </div>
          <div class="flex flex-col gap-2 sm:flex-row">
            <div class="relative sm:w-72">
              <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
              <Input v-model="search" class="pl-9" placeholder="Search the catalog" aria-label="Search event products" />
            </div>
            <Button type="button" :disabled="saving || !isDirty" @click="saveProducts">
              <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
              <Save v-else class="h-4 w-4" aria-hidden="true" />
              Save selection
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent class="space-y-5 p-5">
        <div v-if="pagedProducts.length" class="grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
          <article
            v-for="product in pagedProducts"
            :key="product.public_id"
            class="group grid grid-cols-[5.5rem_minmax(0,1fr)] overflow-hidden rounded-xl border bg-background transition-[border-color,box-shadow] hover:border-primary/35 hover:shadow-sm"
          >
            <div class="relative min-h-32 overflow-hidden bg-muted">
              <img v-if="productImage(product)" :src="productImage(product)" :alt="product.name" class="absolute inset-0 h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.03]" />
              <div v-else class="grid h-full place-items-center text-muted-foreground">
                <PackageOpen class="h-7 w-7" aria-hidden="true" />
              </div>
            </div>
            <div class="flex min-w-0 flex-col p-4">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate font-semibold">{{ product.name }}</p>
                  <p class="mt-1 text-xs text-muted-foreground">{{ typeLabel(product.offering_type) }} · {{ product.status }}</p>
                </div>
                <Badge v-if="isSelected(product.public_id)" variant="secondary" class="shrink-0">Added</Badge>
              </div>
              <p class="mt-3 line-clamp-2 text-sm leading-5 text-muted-foreground">{{ product.summary || 'No catalog summary yet.' }}</p>
              <div class="mt-auto flex items-end justify-between gap-3 pt-4">
                <p class="font-semibold tabular-nums">{{ formatMoney(product.base_price) }}</p>
                <Button
                  type="button"
                  size="sm"
                  :variant="isSelected(product.public_id) ? 'outline' : 'default'"
                  @click="toggleProduct(product.public_id)"
                >
                  <Minus v-if="isSelected(product.public_id)" class="h-4 w-4" aria-hidden="true" />
                  <Plus v-else class="h-4 w-4" aria-hidden="true" />
                  {{ isSelected(product.public_id) ? 'Remove' : 'Add' }}
                </Button>
              </div>
            </div>
          </article>
        </div>

        <div v-else class="rounded-xl border border-dashed px-6 py-12 text-center">
          <PackageSearch class="mx-auto h-9 w-9 text-muted-foreground/50" aria-hidden="true" />
          <p class="mt-4 font-semibold">{{ search ? 'No catalog items match this search' : 'The catalog is empty' }}</p>
          <p class="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            {{ search ? 'Try a product name, service name, or category.' : 'Create products or services in Catalog, then return here to attach them to the event.' }}
          </p>
        </div>

        <RecordPagination
          v-if="filteredProducts.length > pageSize"
          :page="page"
          :count="filteredProducts.length"
          :size="pageSize"
          :busy="saving"
          @page="page = $event"
        />
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { Loader2, Minus, PackageOpen, PackageSearch, Plus, Save, Search } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/toast'
import RecordPagination from '@/components/workspace/RecordPagination.vue'

const props = defineProps({
  businessId: { type: String, required: true },
  event: { type: Object, required: true },
  products: { type: Array, default: () => [] },
})

const emit = defineEmits(['updated'])
const { apiFetch } = useApiClient()
const selectedIds = ref([...(props.event.product_public_ids || [])])
const search = ref('')
const page = ref(1)
const pageSize = 9
const saving = ref(false)

const availableProducts = computed(() => props.products.filter(product => product.status !== 'archived'))
const filteredProducts = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) return availableProducts.value
  return availableProducts.value.filter(product => [
    product.name,
    product.summary,
    product.category_name,
    product.offering_type,
  ].some(value => String(value || '').toLowerCase().includes(query)))
})
const pagedProducts = computed(() => filteredProducts.value.slice((page.value - 1) * pageSize, page.value * pageSize))
const isDirty = computed(() => {
  const original = [...(props.event.product_public_ids || [])].sort()
  const current = [...selectedIds.value].sort()
  return original.join(':') !== current.join(':')
})

watch(search, () => {
  page.value = 1
})

watch(
  () => props.event.product_public_ids,
  value => {
    selectedIds.value = [...(value || [])]
  },
)

function isSelected(productId) {
  return selectedIds.value.includes(productId)
}

function toggleProduct(productId) {
  selectedIds.value = isSelected(productId)
    ? selectedIds.value.filter(id => id !== productId)
    : [...selectedIds.value, productId]
}

function selectedTypeCount(type) {
  return availableProducts.value.filter(product => isSelected(product.public_id) && product.offering_type === type).length
}

async function saveProducts() {
  saving.value = true
  try {
    const saved = await apiFetch(`businesses/${props.businessId}/venue-events/${props.event.public_id}/`, {
      method: 'PATCH',
      body: { product_public_ids: selectedIds.value },
    })
    emit('updated', saved)
    toast({
      title: 'Event catalog updated',
      description: `${saved.product_public_ids.length} catalog item${saved.product_public_ids.length === 1 ? '' : 's'} linked to this event.`,
    })
  } catch (error) {
    toast({
      title: 'Products could not be saved',
      description: error?.data?.error?.message || error?.data?.detail || 'Review the selection and try again.',
      variant: 'destructive',
    })
  } finally {
    saving.value = false
  }
}

function productImage(product) {
  return product.ordered_media?.find(item => item.role === 'cover')?.url
    || product.ordered_media?.[0]?.url
    || product.media?.[0]?.url
    || ''
}

function typeLabel(value) {
  return {
    physical: 'Physical product',
    digital: 'Digital product',
    service: 'Service',
  }[value] || 'Catalog item'
}

function formatMoney(value) {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: 'PHP',
    maximumFractionDigits: 2,
  }).format(Number(value || 0))
}
</script>
