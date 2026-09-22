<template>
  <section class="workspace-page space-y-5">
    <header class="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <NuxtLink
          to="/workspace/sell"
          class="inline-flex items-center gap-2 text-sm font-bold text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft class="h-4 w-4" aria-hidden="true" />
          Back to catalog
        </NuxtLink>
        <h1 class="mt-4 text-3xl font-extrabold tracking-[-.025em]">Add a product or service</h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          Choose the offering type first. PixelCore will show only the details needed for that sales or booking flow.
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button variant="outline" type="button" :disabled="saving" @click="save('draft')">Save draft</Button>
        <Button type="button" :disabled="saving || !canPublish" @click="save('published')">
          {{ saving ? 'Saving…' : 'Save & publish' }}
        </Button>
      </div>
    </header>

    <form class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_22rem]" @submit.prevent="save(form.status)">
      <div class="space-y-6">
        <section class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="basic-heading">
          <h2 id="basic-heading" class="text-base font-extrabold">
            {{ isService ? 'Service information' : 'Product information' }}
          </h2>
          <p class="mt-1 text-sm text-muted-foreground">
            {{ isService
              ? 'Describe what customers can book and what the appointment includes.'
              : 'Describe what customers will see in the catalog and checkout.' }}
          </p>
          <div class="mt-6 grid gap-5 sm:grid-cols-2">
            <label class="sm:col-span-2">
              <span class="field-label">Name</span>
              <Input
                v-model.trim="form.name"
                required
                maxlength="180"
                :placeholder="isService ? 'What can customers book?' : 'What are you selling?'"
              />
            </label>
            <label>
              <span class="field-label">Type</span>
              <NativeSelect v-model="form.offering_type">
                <option value="physical">Physical product</option>
                <option value="digital">Digital product</option>
                <option value="service">Bookable service</option>
              </NativeSelect>
            </label>
            <label>
              <span class="field-label">Category</span>
              <NativeSelect v-model="form.category_public_id">
                <option value="">Uncategorized</option>
                <option v-for="category in categories" :key="category.public_id" :value="category.public_id">
                  {{ category.name }}
                </option>
              </NativeSelect>
            </label>
            <label class="sm:col-span-2">
              <span class="field-label">Short summary</span>
              <Input
                v-model.trim="form.summary"
                maxlength="300"
                :placeholder="isService ? 'What should customers expect?' : 'A concise benefit customers can scan'"
              />
              <span class="mt-2 block text-xs text-muted-foreground">{{ form.summary.length }}/300 characters</span>
            </label>
            <label class="sm:col-span-2">
              <span class="field-label">Description</span>
              <Textarea
                v-model.trim="form.description"
                class="min-h-36 resize-y"
                maxlength="5000"
                :placeholder="isService
                  ? 'Describe the session, inclusions, preparation, and important booking details.'
                  : 'Describe the product, materials, inclusions, or important details.'"
              />
            </label>
          </div>
        </section>

        <section class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="media-heading">
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 id="media-heading" class="text-base font-extrabold">
                {{ isService ? 'Service image' : 'Product image' }}
              </h2>
              <p class="mt-1 text-sm text-muted-foreground">
                Add one clear listing image. JPG, PNG, WebP, or AVIF up to 8 MB.
              </p>
            </div>
            <ImageIcon class="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          </div>
          <div class="mt-6 grid gap-5 sm:grid-cols-[15rem_minmax(0,1fr)] sm:items-center">
            <ProductArtwork
              :name="form.name || (isService ? 'New service' : 'New product')"
              :type="form.offering_type"
              :media="previewMedia"
            />
            <div>
              <Button as-child variant="outline">
                <label class="cursor-pointer">
                  <Upload class="h-4 w-4" aria-hidden="true" />
                  {{ imageFile ? 'Replace image' : 'Upload image' }}
                  <Input
                    class="sr-only"
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/avif"
                    @change="selectImage"
                  />
                </label>
              </Button>
              <p v-if="imageFile" class="mt-3 text-sm font-semibold">{{ imageFile.name }}</p>
              <label class="mt-4 block">
                <span class="field-label">Image description</span>
                <Input v-model.trim="imageAlt" maxlength="250" placeholder="Describe the image for accessibility" />
              </label>
            </div>
          </div>
        </section>

        <section
          v-if="isService"
          class="rounded-xl border bg-card p-5 sm:p-6"
          aria-labelledby="booking-details-heading"
        >
          <div class="flex items-start gap-3">
            <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
              <CalendarClock class="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 id="booking-details-heading" class="text-base font-extrabold">Booking details</h2>
              <p class="mt-1 text-sm text-muted-foreground">
                Service fulfillment is fixed to booking. Staff hours and venue resources are assigned in Schedule.
              </p>
            </div>
          </div>
          <div class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <label>
              <span class="field-label">Price ({{ business.activeBusiness?.currency }})</span>
              <Input v-model="form.base_price" type="number" min="0" step="0.01" required />
            </label>
            <label>
              <span class="field-label">Duration (minutes)</span>
              <Input v-model.number="form.duration_minutes" type="number" min="5" max="1440" required />
            </label>
            <label>
              <span class="field-label">Capacity</span>
              <Input v-model.number="form.capacity" type="number" min="1" max="999" required />
            </label>
            <label>
              <span class="field-label">Tax rate (%)</span>
              <Input v-model="form.tax_rate" type="number" min="0" max="100" step="0.001" />
            </label>
          </div>
        </section>

        <section v-else class="rounded-xl border bg-card p-5 sm:p-6" aria-labelledby="commercial-heading">
          <h2 id="commercial-heading" class="text-base font-extrabold">Pricing & sale details</h2>
          <p class="mt-1 text-sm text-muted-foreground">
            PixelCore validates the final price again at checkout and POS.
          </p>
          <div class="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <label>
              <span class="field-label">Price ({{ business.activeBusiness?.currency }})</span>
              <Input v-model="form.base_price" type="number" min="0" step="0.01" required />
            </label>
            <label>
              <span class="field-label">Compare-at price</span>
              <Input v-model="form.compare_at_price" type="number" min="0" step="0.01" placeholder="Optional" />
            </label>
            <label>
              <span class="field-label">Tax rate (%)</span>
              <Input v-model="form.tax_rate" type="number" min="0" max="100" step="0.001" />
            </label>
            <label>
              <span class="field-label">SKU</span>
              <Input v-model.trim="form.sku" maxlength="80" placeholder="Optional" />
            </label>
            <label>
              <span class="field-label">Fulfillment</span>
              <NativeSelect v-model="form.fulfillment_type">
                <option v-if="form.offering_type === 'physical'" value="delivery">Delivery</option>
                <option v-if="form.offering_type === 'physical'" value="pickup">Pickup</option>
                <option v-if="form.offering_type === 'digital'" value="digital">Protected download</option>
                <option value="none">No fulfillment</option>
              </NativeSelect>
            </label>
          </div>
          <label v-if="form.offering_type === 'physical'" class="mt-5 flex items-start gap-3">
            <NativeCheckbox v-model="form.track_inventory" class="mt-1 h-4 w-4" />
            <span>
              <strong class="block text-sm">Track inventory</strong>
              <span class="mt-1 block text-xs leading-5 text-muted-foreground">
                Variants and location balances can be configured after the product is created.
              </span>
            </span>
          </label>
        </section>
      </div>

      <aside class="space-y-6 xl:sticky xl:top-24 xl:self-start">
        <section class="rounded-xl border bg-card p-5" aria-labelledby="publish-heading">
          <h2 id="publish-heading" class="text-base font-extrabold">Publication</h2>
          <div class="mt-5 space-y-4">
            <label>
              <span class="field-label">Status</span>
              <NativeSelect v-model="form.status">
                <option value="draft">Draft</option>
                <option value="published" :disabled="!canPublish">Published</option>
              </NativeSelect>
            </label>
            <div v-if="isService" class="rounded-lg border bg-muted/30 p-3">
              <div class="flex items-center gap-2 text-sm font-semibold">
                <CalendarCheck2 class="h-4 w-4 text-primary" aria-hidden="true" />
                Booking fulfillment
              </div>
              <p class="mt-1 text-xs leading-5 text-muted-foreground">
                Published services become available to Schedule for staff assignment.
              </p>
            </div>
            <p
              v-if="form.offering_type === 'digital'"
              class="rounded-lg bg-muted p-3 text-xs leading-5 text-muted-foreground"
            >
              Digital products remain drafts until a protected delivery asset is attached from the product detail page.
            </p>
          </div>
        </section>

        <section class="rounded-xl border bg-card p-5" aria-labelledby="readiness-heading">
          <h2 id="readiness-heading" class="text-base font-extrabold">Readiness</h2>
          <ul class="mt-4 space-y-3 text-sm">
            <li v-for="check in readiness" :key="check.label" class="flex items-start gap-3">
              <CheckCircle2
                v-if="check.complete"
                class="mt-0.5 h-4 w-4 shrink-0 text-primary"
                aria-hidden="true"
              />
              <Circle v-else class="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <span :class="check.complete ? 'font-semibold' : 'text-muted-foreground'">{{ check.label }}</span>
            </li>
          </ul>
        </section>

        <p
          v-if="error"
          class="rounded-xl border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive"
          role="alert"
        >
          {{ error }}
        </p>
        <Button class="w-full" type="submit" :disabled="saving">
          {{ saving ? `Saving ${offeringNoun.toLowerCase()}…` : form.status === 'published' ? 'Save & publish' : 'Save draft' }}
        </Button>
      </aside>
    </form>
  </section>
</template>

<script setup>
import {
  ArrowLeft,
  CalendarCheck2,
  CalendarClock,
  CheckCircle2,
  Circle,
  Image as ImageIcon,
  Upload,
} from 'lucide-vue-next'
import { toast } from '@/components/ui/toast'

const router = useRouter()
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const categories = ref([])
const saving = ref(false)
const error = ref('')
const imageFile = ref(null)
const imagePreview = ref('')
const imageAlt = ref('')
const form = reactive({
  category_public_id: '',
  name: '',
  summary: '',
  description: '',
  offering_type: 'physical',
  status: 'draft',
  fulfillment_type: 'delivery',
  base_price: '',
  compare_at_price: '',
  tax_rate: '0',
  sku: '',
  track_inventory: true,
  duration_minutes: 60,
  capacity: 1,
  metadata: {},
})

const isService = computed(() => form.offering_type === 'service')
const offeringNoun = computed(() => isService.value ? 'Service' : 'Product')
const previewMedia = computed(() => imagePreview.value
  ? [{ url: imagePreview.value, alt_text: imageAlt.value }]
  : [])
const canPublish = computed(() => form.offering_type !== 'digital')
const readiness = computed(() => {
  const checks = [
    { label: `${offeringNoun.value} name added`, complete: Boolean(form.name) },
    { label: 'Customer summary added', complete: Boolean(form.summary) },
    { label: 'Price configured', complete: form.base_price !== '' },
    { label: `${offeringNoun.value} image added`, complete: Boolean(imageFile.value) },
  ]
  if (isService.value) {
    checks.push(
      { label: 'Duration configured', complete: Number(form.duration_minutes) >= 5 },
      { label: 'Capacity configured', complete: Number(form.capacity) >= 1 },
    )
  } else {
    checks.push({ label: 'Fulfillment selected', complete: Boolean(form.fulfillment_type) })
  }
  return checks
})

watch(() => form.offering_type, (type) => {
  form.fulfillment_type = type === 'physical' ? 'delivery' : type === 'digital' ? 'digital' : 'booking'
  if (type === 'service') {
    form.compare_at_price = ''
    form.sku = ''
    form.track_inventory = false
  } else if (type === 'physical') {
    form.track_inventory = true
  }
  if (type === 'digital') form.status = 'draft'
})

onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses()
  const response = await apiFetch(
    `businesses/${business.activeBusiness.public_id}/categories/?page_size=100`,
  ).catch(() => ({ results: [] }))
  categories.value = response.results || []
})

function selectImage(event) {
  const file = event.target.files?.[0] || null
  imageFile.value = file
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
  imagePreview.value = file ? URL.createObjectURL(file) : ''
}

async function uploadImage() {
  if (!imageFile.value) return null
  const body = new FormData()
  body.append('title', form.name || imageFile.value.name)
  body.append('alt_text', imageAlt.value)
  body.append('asset_type', 'image')
  body.append('file', imageFile.value)
  const asset = await apiFetch(`businesses/${business.activeBusiness.public_id}/assets/`, {
    method: 'POST',
    body,
  })
  return asset.public_id
}

async function save(status) {
  if (!form.name || form.base_price === '') {
    error.value = `Add a ${offeringNoun.value.toLowerCase()} name and price before saving.`
    toast({
      title: `${offeringNoun.value} not ready`,
      description: error.value,
      variant: 'destructive',
      duration: 5000,
    })
    return
  }
  saving.value = true
  error.value = ''
  try {
    const assetId = await uploadImage()
    const payload = {
      ...form,
      status: status === 'published' && canPublish.value ? 'published' : 'draft',
      category_public_id: form.category_public_id || null,
      compare_at_price: form.compare_at_price || null,
      asset_public_ids: assetId ? [assetId] : [],
    }
    if (isService.value) {
      payload.fulfillment_type = 'booking'
      payload.compare_at_price = null
      payload.sku = ''
      payload.track_inventory = false
    } else {
      delete payload.duration_minutes
      payload.capacity = 1
    }
    const created = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/offerings/`,
      { method: 'POST', body: payload },
    )
    toast({
      title: payload.status === 'published' ? `${offeringNoun.value} published` : 'Draft saved',
      description: isService.value
        ? `${created.name} is ready for staff availability in Schedule.`
        : `${created.name} is now available in your catalog workspace.`,
      duration: 4500,
    })
    await router.push(`/workspace/sell/catalog/${created.public_id}`)
  } catch (requestError) {
    error.value = requestError?.data?.error?.message
      || `The ${offeringNoun.value.toLowerCase()} could not be saved. Review the details and try again.`
    toast({
      title: `${offeringNoun.value} could not be saved`,
      description: error.value,
      variant: 'destructive',
      duration: 6000,
    })
  } finally {
    saving.value = false
  }
}

onBeforeUnmount(() => {
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
})
</script>
