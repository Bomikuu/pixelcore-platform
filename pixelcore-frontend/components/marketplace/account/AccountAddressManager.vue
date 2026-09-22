<template>
  <section aria-labelledby="saved-addresses-heading">
    <div class="flex flex-col gap-4 border-b pb-5 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 id="saved-addresses-heading" class="text-xl font-semibold">Saved addresses</h2>
        <p class="mt-1 text-sm leading-5 text-muted-foreground">
          Keep delivery and billing destinations ready for checkout.
        </p>
      </div>
      <Button type="button" class="gap-2" @click="openCreateDialog">
        <Plus class="h-4 w-4" aria-hidden="true" />
        Add address
      </Button>
    </div>

    <Alert v-if="error" variant="destructive" class="mt-6">
      <CircleAlert class="h-4 w-4" aria-hidden="true" />
      <AlertTitle>Address not updated</AlertTitle>
      <AlertDescription>{{ error }}</AlertDescription>
    </Alert>

    <div v-if="addresses.length" class="mt-6 grid gap-4 sm:grid-cols-2">
      <Card v-for="address in addresses" :key="address.public_id" class="flex flex-col">
        <CardHeader>
          <div class="flex items-start justify-between gap-4">
            <div class="flex min-w-0 items-start gap-3">
              <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <MapPin class="h-4 w-4" aria-hidden="true" />
              </div>
              <div class="min-w-0">
                <CardTitle class="truncate text-base">
                  {{ address.label || 'Delivery address' }}
                </CardTitle>
                <Badge v-if="address.is_default" variant="secondary" class="mt-2">Default</Badge>
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              :aria-label="`Edit ${address.label || 'delivery address'}`"
              @click="openEditDialog(address)"
            >
              <Pencil class="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </CardHeader>
        <CardContent class="text-sm leading-6 text-muted-foreground">
          <p class="font-medium text-foreground">{{ address.recipient_name }}</p>
          <p>{{ address.line1 }}</p>
          <p v-if="address.line2">{{ address.line2 }}</p>
          <p>{{ locality(address) }}</p>
          <p>{{ address.country }}</p>
          <p v-if="address.phone" class="mt-3">{{ address.phone }}</p>
        </CardContent>
      </Card>
    </div>

    <div v-else class="mt-6 flex flex-col items-center border-y py-14 text-center">
      <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <MapPinned class="h-6 w-6" aria-hidden="true" />
      </div>
      <h2 class="mt-5 text-lg font-semibold">No saved addresses</h2>
      <p class="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
        Add a destination now, or let checkout save one to your customer profile later.
      </p>
      <Button type="button" variant="outline" class="mt-5 gap-2" @click="openCreateDialog">
        <Plus class="h-4 w-4" aria-hidden="true" />
        Add your first address
      </Button>
    </div>

    <Dialog v-model:open="dialogOpen">
      <DialogScrollContent class="max-w-2xl">
        <DialogHeader>
          <div class="flex items-start gap-3 pr-8">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <MapPin class="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <DialogTitle>{{ editingAddress ? 'Edit address' : 'Add address' }}</DialogTitle>
              <DialogDescription class="mt-1">
                Add the details that should appear during checkout and delivery.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <form class="space-y-5" @submit.prevent="submitAddress">
          <Alert v-if="error" variant="destructive">
            <CircleAlert class="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Review this address</AlertTitle>
            <AlertDescription>{{ error }}</AlertDescription>
          </Alert>

          <div class="grid gap-5 sm:grid-cols-2">
            <div class="space-y-2">
              <Label for="address-label">Label</Label>
              <Input id="address-label" v-model="form.label" maxlength="80" placeholder="Home or Office" />
            </div>
            <div class="space-y-2">
              <Label for="address-recipient">Recipient name</Label>
              <Input
                id="address-recipient"
                v-model="form.recipient_name"
                autocomplete="name"
                maxlength="180"
                required
              />
            </div>
          </div>

          <div class="space-y-2">
            <Label for="address-line-1">Street address</Label>
            <Input
              id="address-line-1"
              v-model="form.line1"
              autocomplete="address-line1"
              maxlength="255"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="address-line-2">Unit, floor, or landmark <span class="text-muted-foreground">(optional)</span></Label>
            <Input
              id="address-line-2"
              v-model="form.line2"
              autocomplete="address-line2"
              maxlength="255"
            />
          </div>

          <div class="grid gap-5 sm:grid-cols-2">
            <div class="space-y-2">
              <Label for="address-city">City or municipality</Label>
              <Input id="address-city" v-model="form.city" autocomplete="address-level2" maxlength="100" required />
            </div>
            <div class="space-y-2">
              <Label for="address-region">Province or region</Label>
              <Input id="address-region" v-model="form.region" autocomplete="address-level1" maxlength="100" required />
            </div>
            <div class="space-y-2">
              <Label for="address-postal-code">Postal code</Label>
              <Input id="address-postal-code" v-model="form.postal_code" autocomplete="postal-code" maxlength="24" />
            </div>
            <div class="space-y-2">
              <Label for="address-country">Country code</Label>
              <Input
                id="address-country"
                v-model="form.country"
                autocomplete="country"
                maxlength="2"
                placeholder="PH"
                required
              />
              <p class="text-xs text-muted-foreground">Use the two-letter code, such as PH.</p>
            </div>
          </div>

          <div class="space-y-2">
            <Label for="address-phone">Delivery phone</Label>
            <Input
              id="address-phone"
              v-model="form.phone"
              type="tel"
              inputmode="tel"
              autocomplete="tel"
              maxlength="32"
              placeholder="+63 912 345 6789"
            />
          </div>

          <div class="flex items-start justify-between gap-5 border-y py-4">
            <div>
              <Label for="address-default" class="leading-5">Use as default address</Label>
              <p class="mt-1 text-sm leading-5 text-muted-foreground">
                {{ defaultAddressHelp }}
              </p>
            </div>
            <Switch
              id="address-default"
              v-model:checked="form.is_default"
              :disabled="saving || Boolean(editingAddress?.is_default)"
            />
          </div>

          <Alert v-if="confirmingDelete" variant="destructive">
            <TriangleAlert class="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Remove this saved address?</AlertTitle>
            <AlertDescription>
              This does not change addresses already recorded on earlier orders.
            </AlertDescription>
          </Alert>

          <DialogFooter class="gap-2 sm:justify-between">
            <div>
              <Button
                v-if="editingAddress"
                type="button"
                variant="destructive"
                class="gap-2"
                :disabled="saving"
                @click="handleDelete"
              >
                <Trash2 class="h-4 w-4" aria-hidden="true" />
                {{ confirmingDelete ? 'Confirm removal' : 'Remove address' }}
              </Button>
            </div>
            <div class="flex flex-col-reverse gap-2 sm:flex-row">
              <Button type="button" variant="outline" :disabled="saving" @click="dialogOpen = false">
                Cancel
              </Button>
              <Button type="submit" class="gap-2" :disabled="saving || !isComplete">
                <LoaderCircle v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
                <Save v-else class="h-4 w-4" aria-hidden="true" />
                {{ saving ? 'Saving address' : 'Save address' }}
              </Button>
            </div>
          </DialogFooter>
        </form>
      </DialogScrollContent>
    </Dialog>
  </section>
</template>

<script setup>
import {
  CircleAlert,
  LoaderCircle,
  MapPin,
  MapPinned,
  Pencil,
  Plus,
  Save,
  Trash2,
  TriangleAlert,
} from 'lucide-vue-next'

const props = defineProps({
  addresses: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits(['save', 'remove'])

const dialogOpen = ref(false)
const editingAddress = ref(null)
const confirmingDelete = ref(false)
const form = reactive(emptyAddress())

const isComplete = computed(() =>
  Boolean(
    form.recipient_name.trim()
    && form.line1.trim()
    && form.city.trim()
    && form.region.trim()
    && /^[A-Za-z]{2}$/.test(form.country.trim()),
  ),
)
const defaultAddressHelp = computed(() =>
  editingAddress.value?.is_default
    ? 'To replace this default, set another saved address as the default.'
    : 'Checkout will select this destination first.',
)

watch(
  () => props.saving,
  (saving, wasSaving) => {
    if (wasSaving && !saving && !props.error) {
      dialogOpen.value = false
      resetDialog()
    }
  },
)

watch(dialogOpen, (open) => {
  if (!open && !props.saving) resetDialog()
})

function emptyAddress() {
  return {
    label: '',
    recipient_name: '',
    line1: '',
    line2: '',
    city: '',
    region: '',
    postal_code: '',
    country: 'PH',
    phone: '',
    is_default: false,
  }
}

function resetDialog() {
  editingAddress.value = null
  confirmingDelete.value = false
  Object.assign(form, emptyAddress())
}

function openCreateDialog() {
  resetDialog()
  dialogOpen.value = true
}

function openEditDialog(address) {
  editingAddress.value = address
  confirmingDelete.value = false
  Object.assign(form, emptyAddress(), address)
  dialogOpen.value = true
}

function submitAddress() {
  if (props.saving || !isComplete.value) return

  emit('save', {
    addressId: editingAddress.value?.public_id || null,
    data: {
      label: form.label.trim(),
      recipient_name: form.recipient_name.trim(),
      line1: form.line1.trim(),
      line2: form.line2.trim(),
      city: form.city.trim(),
      region: form.region.trim(),
      postal_code: form.postal_code.trim(),
      country: form.country.trim().toUpperCase(),
      phone: form.phone.trim(),
      is_default: form.is_default,
    },
  })
}

function handleDelete() {
  if (!editingAddress.value || props.saving) return
  if (!confirmingDelete.value) {
    confirmingDelete.value = true
    return
  }

  emit('remove', editingAddress.value.public_id)
}

function locality(address) {
  return [address.city, address.region, address.postal_code].filter(Boolean).join(', ')
}
</script>
