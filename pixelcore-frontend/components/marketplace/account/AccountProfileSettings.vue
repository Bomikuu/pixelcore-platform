<template>
  <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
    <Card>
      <CardHeader>
        <div class="flex items-start gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <UserRound class="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <CardTitle>Profile details</CardTitle>
            <CardDescription class="mt-1">
              Used for orders, bookings, receipts, and communication from this business.
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <form class="space-y-6" @submit.prevent="submit">
          <Alert v-if="error" variant="destructive">
            <CircleAlert class="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Profile not saved</AlertTitle>
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>

          <div class="grid gap-5 sm:grid-cols-2">
            <div class="space-y-2">
              <Label for="customer-first-name">First name</Label>
              <Input
                id="customer-first-name"
                v-model="form.first_name"
                autocomplete="given-name"
                maxlength="100"
                required
              />
            </div>

            <div class="space-y-2">
              <Label for="customer-last-name">Last name</Label>
              <Input
                id="customer-last-name"
                v-model="form.last_name"
                autocomplete="family-name"
                maxlength="100"
              />
            </div>
          </div>

          <div class="space-y-2">
            <Label for="customer-email">Email</Label>
            <Input
              id="customer-email"
              :model-value="email"
              type="email"
              autocomplete="email"
              disabled
            />
            <p class="text-sm leading-5 text-muted-foreground">
              Your email is tied to sign-in and verification. A verified email-change flow will be added separately.
            </p>
          </div>

          <div class="space-y-2">
            <Label for="customer-phone">Phone</Label>
            <Input
              id="customer-phone"
              v-model="form.phone"
              type="tel"
              inputmode="tel"
              autocomplete="tel"
              maxlength="32"
              placeholder="+63 912 345 6789"
            />
          </div>

          <div class="flex items-start justify-between gap-5 border-y py-5">
            <div class="min-w-0">
              <Label for="customer-marketing" class="leading-5">Product and offer updates</Label>
              <p class="mt-1 max-w-xl text-sm leading-5 text-muted-foreground">
                Allow {{ identity.display_name }} to send relevant storefront announcements to your account email.
              </p>
            </div>
            <Switch
              id="customer-marketing"
              v-model:checked="form.accepts_marketing"
              :disabled="saving"
              aria-label="Receive product and offer updates"
            />
          </div>

          <div class="flex justify-end">
            <Button type="submit" class="gap-2" :disabled="saving || !form.first_name.trim()">
              <LoaderCircle v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
              <Save v-else class="h-4 w-4" aria-hidden="true" />
              {{ saving ? 'Saving profile' : 'Save changes' }}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>

    <Card class="h-fit">
      <CardHeader>
        <CardTitle class="text-base">Store relationship</CardTitle>
        <CardDescription>This profile belongs only to {{ identity.display_name }}.</CardDescription>
      </CardHeader>
      <CardContent class="space-y-5 text-sm">
        <div>
          <p class="text-muted-foreground">Customer since</p>
          <p class="mt-1 font-medium">{{ customerSince }}</p>
        </div>
        <div>
          <p class="text-muted-foreground">Privacy</p>
          <p class="mt-1 leading-5">
            Profile details are not shared with other PixelCore businesses.
          </p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import {
  CircleAlert,
  LoaderCircle,
  Save,
  UserRound,
} from 'lucide-vue-next'

const props = defineProps({
  customer: { type: Object, default: null },
  user: { type: Object, default: null },
  identity: { type: Object, required: true },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits(['save'])

const form = reactive({
  first_name: '',
  last_name: '',
  phone: '',
  accepts_marketing: false,
})

const email = computed(() => props.customer?.email || props.user?.email || '')
const customerSince = computed(() => {
  if (!props.customer?.created_at) return 'No purchases yet'
  return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium' }).format(
    new Date(props.customer.created_at),
  )
})

watch(
  () => [props.customer, props.user],
  resetForm,
  { immediate: true, deep: true },
)

function resetForm() {
  form.first_name = props.customer?.first_name || props.user?.first_name || ''
  form.last_name = props.customer?.last_name || props.user?.last_name || ''
  form.phone = props.customer?.phone || props.user?.phone || ''
  form.accepts_marketing = Boolean(props.customer?.accepts_marketing)
}

function submit() {
  if (props.saving || !form.first_name.trim()) return

  emit('save', {
    first_name: form.first_name.trim(),
    last_name: form.last_name.trim(),
    phone: form.phone.trim(),
    accepts_marketing: form.accepts_marketing,
  })
}
</script>
