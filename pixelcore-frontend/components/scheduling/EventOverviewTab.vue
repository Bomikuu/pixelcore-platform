<template>
  <div>
    <section class="overflow-hidden rounded-xl border bg-card">
      <div class="border-b px-5 py-4 sm:px-6">
        <div class="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <h2 class="text-lg font-semibold">Event staffing</h2>
            <p class="mt-1 text-sm text-muted-foreground">Choose one accountable handler, then assemble everyone working on the event.</p>
          </div>
          <Button type="button" :disabled="saving || !isDirty" @click="saveStaffing">
            <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
            <Save v-else class="h-4 w-4" aria-hidden="true" />
            Save staffing
          </Button>
        </div>
      </div>

      <div class="grid xl:grid-cols-[21rem_minmax(0,1fr)]">
        <div class="border-b p-5 sm:p-6 xl:border-b-0 xl:border-r">
          <div class="flex items-center gap-2">
            <UserRoundCog class="h-5 w-5 text-primary" aria-hidden="true" />
            <h3 class="font-semibold">Primary handler</h3>
          </div>
          <p class="mt-2 text-sm leading-6 text-muted-foreground">The single person accountable for decisions, follow-ups, and handoffs.</p>

          <div v-if="selectedHandler" class="mt-5 flex items-center gap-3 rounded-xl bg-muted/30 p-3">
            <Avatar class="h-12 w-12 border bg-background">
              <AvatarImage v-if="selectedHandler.profile_image_url" :src="selectedHandler.profile_image_url" :alt="selectedHandler.display_name" />
              <AvatarFallback>{{ initials(selectedHandler.display_name) }}</AvatarFallback>
            </Avatar>
            <div class="min-w-0">
              <p class="truncate font-semibold">{{ selectedHandler.display_name }}</p>
              <p class="truncate text-sm text-muted-foreground">{{ selectedHandler.job_title || 'Event handler' }}</p>
            </div>
          </div>
          <div v-else class="mt-5 rounded-xl border border-dashed p-4 text-sm leading-6 text-muted-foreground">
            No primary handler has been assigned yet.
          </div>

          <div class="mt-5 grid gap-2">
            <Label for="event-handler">Accountable employee</Label>
            <Select v-model="handlerId">
              <SelectTrigger id="event-handler">
                <SelectValue placeholder="Choose an employee" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Not assigned</SelectItem>
                <SelectItem v-for="member in activeStaff" :key="member.public_id" :value="member.public_id">
                  {{ member.display_name }}{{ member.job_title ? ` · ${member.job_title}` : '' }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div class="p-5 sm:p-6">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 class="font-semibold">Assigned event team</h3>
              <p class="mt-1 text-sm text-muted-foreground">The primary handler is always included in this team.</p>
            </div>
            <Badge variant="outline">{{ selectedTeamIds.length }} assigned</Badge>
          </div>

          <div v-if="activeStaff.length" class="mt-5 grid gap-px overflow-hidden rounded-xl border bg-border sm:grid-cols-2">
            <label
              v-for="member in activeStaff"
              :key="member.public_id"
              class="flex cursor-pointer items-center gap-3 bg-card p-4 transition-colors hover:bg-muted/30 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-inset has-[:focus-visible]:ring-ring"
              :class="{ 'cursor-default bg-primary/5': member.public_id === handlerId }"
            >
              <Checkbox
                :checked="selectedTeamIds.includes(member.public_id)"
                :disabled="member.public_id === handlerId"
                :aria-label="`Assign ${member.display_name} to this event`"
                @update:checked="toggleTeamMember(member.public_id, $event)"
              />
              <Avatar class="h-10 w-10 border bg-background">
                <AvatarImage v-if="member.profile_image_url" :src="member.profile_image_url" :alt="member.display_name" />
                <AvatarFallback>{{ initials(member.display_name) }}</AvatarFallback>
              </Avatar>
              <span class="min-w-0 flex-1">
                <span class="flex items-center gap-2">
                  <strong class="truncate text-sm">{{ member.display_name }}</strong>
                  <Badge v-if="member.public_id === handlerId" variant="secondary" class="shrink-0">Primary</Badge>
                </span>
                <span class="mt-0.5 block truncate text-xs text-muted-foreground">{{ member.job_title || 'Team member' }}</span>
              </span>
            </label>
          </div>
          <div v-else class="mt-5 grid min-h-44 place-items-center rounded-xl border border-dashed px-6 text-center">
            <div class="max-w-sm">
              <Users class="mx-auto h-8 w-8 text-muted-foreground/50" aria-hidden="true" />
              <p class="mt-3 font-semibold">No active staff available</p>
              <p class="mt-1 text-sm leading-6 text-muted-foreground">Add or activate employees in Workforce before assigning an event team.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import {
  Loader2,
  Save,
  UserRoundCog,
  Users,
} from 'lucide-vue-next'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from '@/components/ui/toast'

const props = defineProps({
  businessId: { type: String, required: true },
  event: { type: Object, required: true },
  staff: { type: Array, default: () => [] },
})

const emit = defineEmits(['updated'])
const { apiFetch } = useApiClient()
const handlerId = ref(props.event.handler_public_id || 'none')
const selectedTeamIds = ref(normalizeIds(props.event.assigned_staff_public_ids || []))
const saving = ref(false)

const activeStaff = computed(() => props.staff.filter(member => member.is_active && member.employment_status === 'active'))
const selectedHandler = computed(() => activeStaff.value.find(member => member.public_id === handlerId.value) || null)
const originalTeamIds = computed(() => normalizeIds(props.event.assigned_staff_public_ids || []))
const isDirty = computed(() => (
  handlerId.value !== (props.event.handler_public_id || 'none')
  || selectedTeamIds.value.join('|') !== originalTeamIds.value.join('|')
))

watch(
  () => props.event,
  value => {
    handlerId.value = value.handler_public_id || 'none'
    selectedTeamIds.value = normalizeIds(value.assigned_staff_public_ids || [])
  },
)

watch(handlerId, value => {
  if (value !== 'none' && !selectedTeamIds.value.includes(value)) {
    selectedTeamIds.value = normalizeIds([...selectedTeamIds.value, value])
  }
})

function toggleTeamMember(publicId, checked) {
  if (publicId === handlerId.value) return
  const ids = checked
    ? [...selectedTeamIds.value, publicId]
    : selectedTeamIds.value.filter(id => id !== publicId)
  selectedTeamIds.value = normalizeIds(ids)
}

async function saveStaffing() {
  saving.value = true
  try {
    const saved = await apiFetch(`businesses/${props.businessId}/venue-events/${props.event.public_id}/`, {
      method: 'PATCH',
      body: {
        handler_public_id: handlerId.value === 'none' ? null : handlerId.value,
        assigned_staff_public_ids: selectedTeamIds.value,
      },
    })
    emit('updated', saved)
    toast({
      title: 'Event staffing updated',
      description: saved.handler_name
        ? `${saved.handler_name} leads a team of ${saved.assigned_staff_public_ids.length}.`
        : `${saved.assigned_staff_public_ids.length} team members are assigned without a primary handler.`,
    })
  } catch (error) {
    toast({
      title: 'Staffing could not be saved',
      description: error?.data?.error?.message || error?.data?.detail || 'Review the staff assignments and try again.',
      variant: 'destructive',
    })
  } finally {
    saving.value = false
  }
}

function normalizeIds(ids) {
  return [...new Set(ids.map(String))].sort()
}

function initials(name) {
  return String(name || '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0])
    .join('')
    .toUpperCase()
}
</script>
