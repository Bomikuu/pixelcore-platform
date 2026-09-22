<template>
  <div class="space-y-5">
    <StatePanel
      v-if="loading"
      kind="loading"
      title="Loading RSVP settings"
      message="Preparing the response form and confirmation language."
    />

    <StatePanel
      v-else-if="loadError"
      kind="error"
      title="RSVP settings unavailable"
      :message="loadError"
    >
      <Button type="button" variant="outline" @click="loadSettings">
        <RefreshCw class="h-4 w-4" aria-hidden="true" />
        Try again
      </Button>
    </StatePanel>

    <section v-else class="overflow-hidden rounded-xl border bg-card">
      <div class="grid gap-5 border-b p-5 lg:grid-cols-[minmax(0,1fr)_20rem] lg:items-center">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h2 class="text-xl font-bold tracking-tight">Shape the guest response</h2>
            <Badge variant="secondary">Private invitation links</Badge>
          </div>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Set the response choices, deadline, and confirmation language guests see on their private RSVP page.
            Dress code and arrival information now live under Event website.
          </p>
        </div>

        <div class="space-y-3">
          <ButtonLink
            :to="previewUrl"
            target="_blank"
            rel="noopener"
            variant="outline"
            class="w-full justify-center"
          >
            <Eye class="h-4 w-4" aria-hidden="true" />
            Preview RSVP
            <ExternalLink class="h-4 w-4" aria-hidden="true" />
          </ButtonLink>
          <div class="rounded-xl bg-emerald-950 p-4 text-emerald-50">
            <p class="flex items-center gap-2 text-sm font-bold">
              <ShieldCheck class="h-4 w-4" aria-hidden="true" />
              Private by invitation
            </p>
            <p class="mt-2 text-xs leading-5 text-emerald-100/75">
              The preview uses sample guest data. Live responses remain tied to each guest's secure link.
            </p>
          </div>
        </div>
      </div>

      <form class="space-y-0" @submit.prevent="saveSettings">
        <div class="grid gap-6 p-5 xl:grid-cols-2">
          <section class="space-y-5" aria-labelledby="rsvp-language-heading">
            <div>
              <h3 id="rsvp-language-heading" class="text-base font-bold">Invitation language</h3>
              <p class="mt-1 text-sm text-muted-foreground">Use language that matches the event without changing the saved response values.</p>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <FieldGroup class="sm:col-span-2" label="Form heading" for-id="rsvp-heading">
                <Input id="rsvp-heading" v-model="form.rsvp.heading" maxlength="80" />
              </FieldGroup>
              <FieldGroup class="sm:col-span-2" label="Introduction" for-id="rsvp-subtitle">
                <Input id="rsvp-subtitle" v-model="form.rsvp.subtitle" maxlength="180" />
              </FieldGroup>
              <FieldGroup label="Accept option" for-id="rsvp-accept-label">
                <Input id="rsvp-accept-label" v-model="form.rsvp.accept_label" maxlength="60" />
              </FieldGroup>
              <FieldGroup label="Decline option" for-id="rsvp-decline-label">
                <Input id="rsvp-decline-label" v-model="form.rsvp.decline_label" maxlength="60" />
              </FieldGroup>
              <FieldGroup class="sm:col-span-2" label="Submit button" for-id="rsvp-submit-label">
                <Input id="rsvp-submit-label" v-model="form.rsvp.submit_label" maxlength="50" />
              </FieldGroup>
            </div>
          </section>

          <section class="space-y-5" aria-labelledby="rsvp-window-heading">
            <div>
              <h3 id="rsvp-window-heading" class="text-base font-bold">Response window</h3>
              <p class="mt-1 text-sm text-muted-foreground">A deadline closes both the visible form and the protected RSVP endpoint.</p>
            </div>
            <FieldGroup label="RSVP deadline" for-id="rsvp-deadline">
              <div class="flex flex-col gap-2 sm:flex-row">
                <Input id="rsvp-deadline" v-model="deadlineInput" class="min-w-0 flex-1" type="datetime-local" />
                <Button v-if="deadlineInput" type="button" variant="outline" @click="deadlineInput = ''">
                  Clear
                </Button>
              </div>
              <template #help>
                Guests see this in {{ timezoneLabel }}. Leave blank to keep responses open while the event RSVP status is open.
              </template>
            </FieldGroup>
            <FieldGroup label="Maximum party size per invitation" for-id="rsvp-party-limit">
              <Input
                id="rsvp-party-limit"
                v-model.number="form.rsvp.max_party_size"
                class="max-w-40"
                type="number"
                min="1"
                max="50"
              />
            </FieldGroup>
            <div class="grid gap-3 rounded-xl bg-muted/35 p-4 sm:grid-cols-2">
              <SettingSwitch v-model="form.rsvp.allow_maybe" label="Allow Maybe" description="Offer a non-final response." />
              <SettingSwitch v-model="form.rsvp.show_party_size" label="Party size" description="Ask how many people will attend." />
              <SettingSwitch v-model="form.rsvp.show_dietary_notes" label="Guest needs" description="Collect dietary and accessibility notes." />
              <SettingSwitch v-model="form.rsvp.show_guest_message" label="Guest message" description="Let guests leave a personal wish." />
            </div>
          </section>
        </div>

        <Separator />

        <div class="grid gap-6 p-5 xl:grid-cols-2">
          <section class="space-y-5" aria-labelledby="accepted-response-heading">
            <div>
              <h3 id="accepted-response-heading" class="text-base font-bold">Accepted response</h3>
              <p class="mt-1 text-sm text-muted-foreground">Shown after an attending guest submits.</p>
            </div>
            <FieldGroup label="Confirmation title" for-id="attending-title">
              <Input id="attending-title" v-model="form.rsvp.attending_title" maxlength="100" />
            </FieldGroup>
            <FieldGroup label="Confirmation message" for-id="attending-message">
              <Textarea id="attending-message" v-model="form.rsvp.attending_message" rows="4" maxlength="500" />
            </FieldGroup>
          </section>

          <section class="space-y-5" aria-labelledby="declined-response-heading">
            <div>
              <h3 id="declined-response-heading" class="text-base font-bold">Declined response</h3>
              <p class="mt-1 text-sm text-muted-foreground">A gracious close for guests who cannot attend.</p>
            </div>
            <FieldGroup label="Confirmation title" for-id="declining-title">
              <Input id="declining-title" v-model="form.rsvp.declining_title" maxlength="100" />
            </FieldGroup>
            <FieldGroup label="Confirmation message" for-id="declining-message">
              <Textarea id="declining-message" v-model="form.rsvp.declining_message" rows="4" maxlength="500" />
            </FieldGroup>
          </section>
        </div>

        <div class="flex flex-col gap-3 border-t bg-muted/15 p-5 sm:flex-row sm:items-center sm:justify-between">
          <div aria-live="polite">
            <p v-if="saveError" class="text-sm font-medium text-destructive">{{ saveError }}</p>
            <p v-else-if="saved" class="flex items-center gap-2 text-sm font-medium text-emerald-700">
              <Check class="h-4 w-4" aria-hidden="true" />
              RSVP settings saved
            </p>
            <p v-else class="text-xs text-muted-foreground">Changes apply to every private guest link.</p>
          </div>
          <Button type="submit" :disabled="saving">
            <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
            <Save v-else class="h-4 w-4" aria-hidden="true" />
            Save RSVP settings
          </Button>
        </div>
      </form>
    </section>
  </div>
</template>

<script setup>
import {
  Check,
  ExternalLink,
  Eye,
  Loader2,
  RefreshCw,
  Save,
  ShieldCheck,
} from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ButtonLink } from '@/components/ui/button-link'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import FieldGroup from '@/components/workspace/FieldGroup.vue'
import SettingSwitch from '@/components/workspace/SettingSwitch.vue'
import StatePanel from '@/components/workspace/StatePanel.vue'
import {
  buildRsvpPreviewPath,
  cloneEventSectionsConfig,
  normalizeEventSectionsConfig,
} from '@/utils/eventRsvpConfig'

const props = defineProps({
  businessId: { type: String, required: true },
  eventId: { type: String, required: true },
})

const emit = defineEmits(['updated'])
const { apiFetch } = useApiClient()
const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
const saveError = ref('')
const saved = ref(false)
const deadlineInput = ref('')
const loadedSections = ref(normalizeEventSectionsConfig())
const website = ref(null)
const form = reactive(normalizeEventSectionsConfig())

const endpoint = computed(() => `businesses/${props.businessId}/venue-events/${props.eventId}/website/`)
const previewUrl = computed(() => buildRsvpPreviewPath({
  eventId: props.eventId,
  businessId: props.businessId,
}))
const timezoneLabel = computed(() => website.value?.timezone || 'the event timezone')

onMounted(loadSettings)

watch(() => props.eventId, () => {
  void loadSettings()
})

async function loadSettings() {
  loading.value = true
  loadError.value = ''
  try {
    const response = await apiFetch(endpoint.value)
    website.value = response
    assignSections(response.sections_config)
  } catch (error) {
    loadError.value = apiError(error, 'Reload the page or try again in a moment.')
  } finally {
    loading.value = false
  }
}

function assignSections(value) {
  const normalized = normalizeEventSectionsConfig(value)
  loadedSections.value = cloneEventSectionsConfig(normalized)
  Object.assign(form, cloneEventSectionsConfig(normalized))
  deadlineInput.value = localDateTime(normalized.rsvp.deadline)
  saved.value = false
}

async function saveSettings() {
  saving.value = true
  saveError.value = ''
  saved.value = false
  try {
    const nextSections = cloneEventSectionsConfig({
      ...loadedSections.value,
      rsvp: {
        ...form.rsvp,
        deadline: deadlineInput.value ? new Date(deadlineInput.value).toISOString() : null,
      },
    })
    const response = await apiFetch(endpoint.value, {
      method: 'PATCH',
      body: { sections_config: nextSections },
    })
    website.value = response
    assignSections(response.sections_config)
    saved.value = true
    emit('updated', response)
    toast({
      title: 'RSVP settings saved',
      description: 'Private guest links now use the updated response form.',
    })
  } catch (error) {
    saveError.value = apiError(error, 'Review the RSVP settings and try again.')
  } finally {
    saving.value = false
  }
}

function localDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60 * 1000).toISOString().slice(0, 16)
}

function apiError(error, fallback) {
  const sectionsError = error?.data?.sections_config
  if (Array.isArray(sectionsError)) return sectionsError.join(' ')
  return error?.data?.error?.message || error?.data?.detail || error?.message || fallback
}
</script>
