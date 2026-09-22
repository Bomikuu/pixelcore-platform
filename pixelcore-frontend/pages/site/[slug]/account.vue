<template>
  <StatePanel
    v-if="identityPending"
    class="mx-auto max-w-xl py-24"
    kind="loading"
    title="Loading account"
    message="Preparing this business account."
  />
  <StatePanel
    v-else-if="identityError || !identity"
    class="mx-auto max-w-xl py-24"
    kind="error"
    title="Business unavailable"
    message="This customer account could not be found."
  />
  <StorefrontFrame
    v-else
    :identity="identity"
    :navigation="navigation"
    :base="siteBase"
  >
    <MarketplaceAccountHub
      :active-tab="activeTab"
      :identity="identity"
      :user="auth.user"
      :portal="portal"
      :wishlist-products="wishlistProducts"
      :authenticated="auth.isAuthenticated"
      :loading="accountPending"
      :error="portalError"
      :profile-saving="profileSaving"
      :profile-error="profileError"
      :address-saving="addressSaving"
      :address-error="addressError"
      :base="siteBase"
      :slug="slug"
      :sign-in-url="signInUrl"
      @update:active-tab="setActiveTab"
      @save-profile="saveProfile"
      @save-address="saveAddress"
      @remove-address="removeAddress"
    />
  </StorefrontFrame>
</template>

<script setup>
import { useToast } from '@/components/ui/toast'

definePageMeta({ layout: 'storefront' })

const allowedTabs = [
  'overview',
  'profile',
  'orders',
  'bookings',
  'wishlist',
  'payments',
  'addresses',
]

const route = useRoute()
const router = useRouter()
const slug = String(route.params.slug)
const auth = useAuthStore()
const wishlist = useWishlistStore()
const { apiFetch } = useApiClient()
const { toast } = useToast()
const {
  identity,
  navigation,
  pending: identityPending,
  error: identityError,
  baseURL,
  siteBase,
} = useStorefrontContext(slug)

const activeTab = ref(validTab(route.query.tab))
const portal = ref(null)
const accountPending = ref(true)
const portalError = ref('')
const profileSaving = ref(false)
const profileError = ref('')
const addressSaving = ref(false)
const addressError = ref('')
const signInUrl = computed(() => `/login?next=${encodeURIComponent(route.fullPath)}`)

const { data: catalog } = useAsyncData(
  `account-products:${slug}`,
  () => $fetch(`public/${slug}/storefront/products/?page_size=60`, { baseURL }),
)

const wishlistProducts = computed(() =>
  (catalog.value?.results || []).filter((product) => wishlist.ids.includes(product.public_id)),
)

watch(
  () => route.query.tab,
  (value) => {
    activeTab.value = validTab(value)
  },
)

onMounted(async () => {
  wishlist.hydrate(slug)
  await auth.restoreSession()

  if (auth.isAuthenticated) {
    try {
      await wishlist.mergeIfSignedIn(slug)
      await refreshPortal()
    } catch (error) {
      portalError.value = error?.data?.error?.message || 'Your customer records could not be loaded.'
    }
  }

  accountPending.value = false
})

function validTab(value) {
  const requested = Array.isArray(value) ? value[0] : value
  return allowedTabs.includes(requested) ? requested : 'overview'
}

function setActiveTab(value) {
  const nextTab = validTab(value)
  activeTab.value = nextTab
  const query = { ...route.query }

  if (nextTab === 'overview') delete query.tab
  else query.tab = nextTab

  router.replace({ query })
}

async function refreshPortal() {
  portal.value = await apiFetch(`public/${slug}/portal/`)
}

async function saveProfile(payload) {
  if (profileSaving.value) return

  profileSaving.value = true
  profileError.value = ''

  try {
    const customer = await apiFetch(`public/${slug}/portal/`, {
      method: 'PATCH',
      body: payload,
    })

    portal.value = {
      ...(portal.value || {}),
      customer,
    }
    toast({
      title: 'Profile updated',
      description: `Your details for ${identity.value.display_name} are saved.`,
    })
  } catch (error) {
    profileError.value = requestErrorMessage(
      error,
      'Check your profile details and try again.',
    )
    toast({
      title: 'Profile not saved',
      description: profileError.value,
      variant: 'destructive',
    })
  } finally {
    profileSaving.value = false
  }
}

async function saveAddress({ addressId, data }) {
  if (addressSaving.value) return

  addressSaving.value = true
  addressError.value = ''

  try {
    const path = addressId
      ? `public/${slug}/portal/addresses/${addressId}/`
      : `public/${slug}/portal/addresses/`

    await apiFetch(path, {
      method: addressId ? 'PATCH' : 'POST',
      body: data,
    })
    await refreshPortal()
    toast({
      title: addressId ? 'Address updated' : 'Address added',
      description: data.is_default
        ? 'This is now your default checkout address.'
        : 'The address is ready to use at checkout.',
    })
  } catch (error) {
    addressError.value = requestErrorMessage(
      error,
      'Check the address details and try again.',
    )
    toast({
      title: 'Address not saved',
      description: addressError.value,
      variant: 'destructive',
    })
  } finally {
    addressSaving.value = false
  }
}

async function removeAddress(addressId) {
  if (addressSaving.value) return

  addressSaving.value = true
  addressError.value = ''

  try {
    await apiFetch(`public/${slug}/portal/addresses/${addressId}/`, {
      method: 'DELETE',
    })
    await refreshPortal()
    toast({
      title: 'Address removed',
      description: 'Earlier orders still keep their original delivery details.',
    })
  } catch (error) {
    addressError.value = requestErrorMessage(
      error,
      'This address could not be removed. Try again.',
    )
    toast({
      title: 'Address not removed',
      description: addressError.value,
      variant: 'destructive',
    })
  } finally {
    addressSaving.value = false
  }
}

function requestErrorMessage(error, fallback) {
  return error?.data?.error?.message || error?.data?.detail || fallback
}
</script>
