import { useToast } from '@/components/ui/toast'

const writableFields = [
  'display_name',
  'job_title',
  'headline',
  'email',
  'phone',
  'style',
  'orientation',
  'font_style',
  'color_mode',
  'typography_mode',
  'heading_font',
  'body_font',
  'accent_font',
  'custom_font_asset_public_id',
  'background_color',
  'text_color',
  'accent_color',
  'border_color',
  'ornament_color',
  'social_links',
  'show_social_links',
  'show_qr',
  'background_type',
  'background_asset_public_id',
  'background_apply_to',
  'background_image_fit',
  'background_image_position',
  'background_overlay',
  'background_overlay_strength',
  'show_email',
  'show_phone',
  'show_business_address',
  'is_published',
]

export function useBusinessCardWorkspace() {
  const business = useBusinessStore()
  const { apiFetch } = useApiClient()
  const { toast } = useToast()
  const card = ref(null)
  const assets = ref([])
  const loading = ref(true)
  const saving = ref(false)
  const uploadingBackground = ref(false)
  const uploadingFont = ref(false)
  const error = ref('')

  const publicPath = computed(() => card.value?.public_path || '')
  const publicUrl = computed(() => {
    if (!publicPath.value) return ''
    if (!import.meta.client) return publicPath.value
    return new URL(publicPath.value, window.location.origin).href
  })
  const canSave = computed(() => Boolean(card.value?.display_name?.trim()))

  onMounted(async () => {
    if (!business.activeBusiness) await business.loadBusinesses()
    await loadCard()
  })

  watch(
    () => business.activeBusiness?.public_id,
    async (nextId, previousId) => {
      if (nextId && previousId && nextId !== previousId) await loadCard()
    },
  )

  async function loadCard() {
    if (!business.activeBusiness) return
    loading.value = true
    error.value = ''
    try {
      const businessId = business.activeBusiness.public_id
      const [cardResponse, assetResponse] = await Promise.all([
        apiFetch(`businesses/${businessId}/business-cards/me/`),
        apiFetch(`businesses/${businessId}/assets/?page_size=100`),
      ])
      card.value = cardResponse
      assets.value = assetResponse.results || []
    } catch (requestError) {
      error.value =
        requestError?.data?.error?.message ||
        'Your business card could not be loaded.'
    } finally {
      loading.value = false
    }
  }

  async function uploadBackground(file) {
    if (!file || uploadingBackground.value) return
    uploadingBackground.value = true
    try {
      const body = new FormData()
      body.append('title', file.name)
      body.append('alt_text', `${card.value.business_name} card background`)
      body.append('file', file)
      const asset = await apiFetch(
        `businesses/${business.activeBusiness.public_id}/business-cards/me/background/`,
        { method: 'POST', body },
      )
      assets.value = [
        asset,
        ...assets.value.filter((item) => item.public_id !== asset.public_id),
      ]
      card.value.background_type = 'image'
      card.value.background_asset_public_id = asset.public_id
      card.value.background_image_url = asset.file_url
      toast({
        title: 'Background uploaded',
        description: 'Review the preview, then save the card to keep this selection.',
      })
    } catch (requestError) {
      toast({
        title: 'Background upload failed',
        description:
          requestError?.data?.error?.message ||
          'Choose another image and try again.',
        variant: 'destructive',
      })
    } finally {
      uploadingBackground.value = false
    }
  }

  async function saveCard() {
    if (!canSave.value || saving.value) return
    saving.value = true
    error.value = ''
    try {
      card.value = await apiFetch(
        `businesses/${business.activeBusiness.public_id}/business-cards/me/`,
        {
          method: 'PUT',
          body: Object.fromEntries(
            writableFields.map((field) => [field, card.value[field]]),
          ),
        },
      )
      toast({
        title: card.value.is_published
          ? 'Business card published'
          : 'Business card saved',
        description: card.value.is_published
          ? 'The public link and print view are ready.'
          : 'Your card remains private until you publish it.',
      })
    } catch (requestError) {
      error.value =
        requestError?.data?.error?.message ||
        'Review the card details and try again.'
      toast({
        title: 'Card not saved',
        description: error.value,
        variant: 'destructive',
      })
    } finally {
      saving.value = false
    }
  }

  async function uploadFont(file) {
    if (!file || uploadingFont.value) return
    uploadingFont.value = true
    try {
      const body = new FormData()
      body.append('title', file.name.replace(/\.woff2$/i, ''))
      body.append('file', file)
      const asset = await apiFetch(
        `businesses/${business.activeBusiness.public_id}/business-cards/me/font/`,
        { method: 'POST', body },
      )
      assets.value = [
        asset,
        ...assets.value.filter((item) => item.public_id !== asset.public_id),
      ]
      card.value.custom_font_asset_public_id = asset.public_id
      card.value.custom_font_url = asset.file_url
      card.value.accent_font = 'custom'
      card.value.typography_mode = 'custom'
      toast({
        title: 'Custom font ready',
        description: 'It now styles the name and accent text. Save the card to keep it.',
      })
    } catch (requestError) {
      toast({
        title: 'Font upload failed',
        description:
          requestError?.data?.error?.message ||
          'Choose a valid self-contained WOFF2 font and try again.',
        variant: 'destructive',
      })
    } finally {
      uploadingFont.value = false
    }
  }

  async function copyPublicLink() {
    if (!publicUrl.value) return
    await navigator.clipboard.writeText(publicUrl.value)
    toast({ title: 'Public link copied' })
  }

  function openPublicPreview() {
    if (!publicUrl.value) return
    window.open(publicUrl.value, '_blank', 'noopener,noreferrer')
  }

  function printCard() {
    if (!card.value) return
    document.body.classList.add('pixelcore-print-business-card')
    window.addEventListener(
      'afterprint',
      () => document.body.classList.remove('pixelcore-print-business-card'),
      { once: true },
    )
    window.print()
  }

  return {
    assets,
    canSave,
    card,
    copyPublicLink,
    error,
    loadCard,
    loading,
    openPublicPreview,
    printCard,
    publicPath,
    publicUrl,
    saveCard,
    saving,
    uploadBackground,
    uploadFont,
    uploadingBackground,
    uploadingFont,
  }
}
