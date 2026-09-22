<template>
  <div class="space-y-5">
    <Alert>
      <PencilRuler class="h-4 w-4" aria-hidden="true" />
      <AlertTitle>This is the shared venue plan</AlertTitle>
      <AlertDescription>
        Changes made here also appear in Venue Studio. You can build the same layout from either place without creating a separate event-only copy.
      </AlertDescription>
    </Alert>

    <section class="overflow-hidden rounded-xl border bg-card">
      <div class="grid lg:grid-cols-[17rem_minmax(0,1fr)]">
        <aside class="border-b bg-muted/15 p-4 lg:border-b-0 lg:border-r">
          <div class="grid gap-2">
            <Label for="event-layout">Venue layout</Label>
            <Select v-model="selectedLayoutId">
              <SelectTrigger id="event-layout">
                <SelectValue placeholder="Choose a floor plan" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No floor plan</SelectItem>
                <SelectItem v-for="layout in matchingLayouts" :key="layout.public_id" :value="layout.public_id">
                  {{ layout.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="mt-3 grid gap-2">
            <Button type="button" size="sm" :disabled="saving || !associationDirty" @click="associateLayout">
              <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
              <Link2 v-else class="h-4 w-4" aria-hidden="true" />
              Use for this event
            </Button>
            <div class="grid grid-cols-2 gap-2">
              <Button type="button" size="sm" variant="outline" @click="openLayoutEditor()">
                <Plus class="h-4 w-4" aria-hidden="true" />
                New
              </Button>
              <Button type="button" size="sm" variant="outline" :disabled="!selectedLayout" @click="openLayoutEditor(selectedLayout)">
                <Pencil class="h-4 w-4" aria-hidden="true" />
                Details
              </Button>
            </div>
          </div>

          <div v-if="selectedLayout" class="mt-5 border-y py-4">
            <p class="font-semibold">{{ selectedLayout.name }}</p>
            <p class="mt-1 text-sm leading-6 text-muted-foreground">{{ selectedLayout.description || 'A reusable plan for this venue.' }}</p>
            <dl class="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt class="text-muted-foreground">Elements</dt>
                <dd class="mt-1 font-semibold tabular-nums">{{ floorResources.length }}</dd>
              </div>
              <div>
                <dt class="text-muted-foreground">Guest seats</dt>
                <dd class="mt-1 font-semibold tabular-nums">{{ totalSeats }}</dd>
              </div>
            </dl>
          </div>

          <div class="mt-5">
            <p class="text-sm font-semibold">Add to the plan</p>
            <p class="mt-1 text-xs leading-5 text-muted-foreground">Select an element, then adjust its size and position.</p>
            <div class="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-1">
              <Button
                v-for="element in elementOptions"
                :key="element.value"
                type="button"
                size="sm"
                variant="outline"
                class="justify-start bg-background"
                :disabled="!selectedLayout"
                @click="openResourceEditor(null, element.value)"
              >
                <component :is="element.icon" class="h-4 w-4 text-primary" aria-hidden="true" />
                {{ element.label }}
              </Button>
            </div>
          </div>
        </aside>

        <div class="min-w-0 p-4 sm:p-5">
          <div class="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h3 class="font-semibold">{{ selectedLayout?.name || 'Choose or create a venue layout' }}</h3>
              <p class="mt-1 text-sm text-muted-foreground">
                {{ selectedLayout ? 'Drag elements to position them. Select an element to edit its capacity, shape, and size.' : 'An event layout keeps seating, stage, service areas, and other venue details together.' }}
              </p>
            </div>
            <div class="flex shrink-0 flex-wrap items-center gap-2">
              <Badge v-if="selectedLayoutId === event.layout_public_id" variant="secondary" class="w-fit">
                Assigned to event
              </Badge>
              <Button type="button" size="sm" variant="outline" :disabled="!selectedLayout" @click="fullscreenOpen = true">
                <Maximize2 class="h-4 w-4" aria-hidden="true" />
                Fullscreen plan
              </Button>
            </div>
          </div>

          <ResourceFloorPlan
            v-if="selectedLayout"
            :resources="floorResources"
            :bookings="[]"
            :selected-resource-id="selectedResourceId"
            resource-word="Element"
            @select="resource => openResourceEditor(resource)"
            @move="persistResourceMove"
          />
          <div v-else class="grid min-h-[32rem] place-items-center rounded-xl border border-dashed bg-muted/10 px-6 text-center">
            <div class="max-w-sm">
              <LayoutTemplate class="mx-auto h-10 w-10 text-muted-foreground/45" aria-hidden="true" />
              <p class="mt-4 font-semibold">No venue plan selected</p>
              <p class="mt-2 text-sm leading-6 text-muted-foreground">Choose an existing reusable layout or create one for this venue.</p>
              <Button type="button" class="mt-5" @click="openLayoutEditor()">
                <Plus class="h-4 w-4" aria-hidden="true" />
                Create venue layout
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <Dialog v-model:open="fullscreenOpen">
      <DialogContent class="flex h-[94vh] w-[96vw] max-w-none flex-col gap-0 overflow-hidden p-0 sm:max-w-none">
        <DialogHeader class="shrink-0 border-b px-5 py-4 pr-14">
          <div class="flex flex-wrap items-center gap-3">
            <DialogTitle>{{ selectedLayout?.name || 'Venue plan' }}</DialogTitle>
            <Badge v-if="selectedLayoutId === event.layout_public_id" variant="secondary">Assigned to event</Badge>
          </div>
          <DialogDescription>Arrange the floor plan with the same controls available in the event workspace.</DialogDescription>
        </DialogHeader>

        <div class="grid min-h-0 flex-1 lg:grid-cols-[18rem_minmax(0,1fr)]">
          <aside class="min-h-0 overflow-y-auto border-b bg-muted/15 p-4 lg:border-b-0 lg:border-r">
            <div class="grid gap-2">
              <Label for="fullscreen-event-layout">Venue layout</Label>
              <Select v-model="selectedLayoutId">
                <SelectTrigger id="fullscreen-event-layout">
                  <SelectValue placeholder="Choose a floor plan" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No floor plan</SelectItem>
                  <SelectItem v-for="layout in matchingLayouts" :key="layout.public_id" :value="layout.public_id">
                    {{ layout.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button type="button" size="sm" class="mt-3 w-full" :disabled="saving || !associationDirty" @click="associateLayout">
              <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
              <Link2 v-else class="h-4 w-4" aria-hidden="true" />
              Use for this event
            </Button>

            <div v-if="selectedLayout" class="mt-5 border-y py-4">
              <p class="font-semibold">{{ selectedLayout.name }}</p>
              <dl class="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt class="text-muted-foreground">Elements</dt>
                  <dd class="mt-1 font-semibold tabular-nums">{{ floorResources.length }}</dd>
                </div>
                <div>
                  <dt class="text-muted-foreground">Guest seats</dt>
                  <dd class="mt-1 font-semibold tabular-nums">{{ totalSeats }}</dd>
                </div>
              </dl>
            </div>

            <div class="mt-5">
              <p class="text-sm font-semibold">Add to the plan</p>
              <p class="mt-1 text-xs leading-5 text-muted-foreground">New elements open with controls for capacity, shape, and size.</p>
              <div class="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-1">
                <Button
                  v-for="element in elementOptions"
                  :key="`fullscreen-${element.value}`"
                  type="button"
                  size="sm"
                  variant="outline"
                  class="justify-start bg-background"
                  :disabled="!selectedLayout"
                  @click="openResourceEditor(null, element.value)"
                >
                  <component :is="element.icon" class="h-4 w-4 text-primary" aria-hidden="true" />
                  {{ element.label }}
                </Button>
              </div>
            </div>
          </aside>

          <div class="min-h-0 min-w-0 bg-background p-4">
            <ResourceFloorPlan
              v-if="selectedLayout"
              expanded
              :resources="floorResources"
              :bookings="[]"
              :selected-resource-id="selectedResourceId"
              resource-word="Element"
              @select="resource => openResourceEditor(resource)"
              @move="persistResourceMove"
            />
            <div v-else class="grid h-full place-items-center rounded-xl border border-dashed text-center">
              <div>
                <LayoutTemplate class="mx-auto h-10 w-10 text-muted-foreground/45" aria-hidden="true" />
                <p class="mt-4 font-semibold">Choose a venue layout</p>
                <p class="mt-1 text-sm text-muted-foreground">Select a floor plan from the sidebar to begin arranging it.</p>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="layoutEditorOpen">
      <DialogContent class="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{{ editingLayoutId ? 'Edit venue layout' : 'Create venue layout' }}</DialogTitle>
          <DialogDescription>Layouts stay reusable across events scheduled at the same business location.</DialogDescription>
        </DialogHeader>
        <div class="grid gap-4 py-2">
          <div class="grid gap-2">
            <Label for="layout-name">Layout name</Label>
            <Input id="layout-name" v-model.trim="layoutForm.name" placeholder="Garden reception plan" />
          </div>
          <div v-if="!event.location_public_id" class="grid gap-2">
            <Label>Business location</Label>
            <Select v-model="layoutForm.location_public_id">
              <SelectTrigger><SelectValue placeholder="Choose a location" /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="location in locations" :key="location.public_id" :value="location.public_id">{{ location.name }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label>Layout type</Label>
            <Select v-model="layoutForm.layout_type">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="event">Event or wedding</SelectItem>
                <SelectItem value="restaurant">Restaurant dining</SelectItem>
                <SelectItem value="room">Room or studio</SelectItem>
                <SelectItem value="general">General venue</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label for="layout-description">Description</Label>
            <Textarea id="layout-description" v-model.trim="layoutForm.description" rows="3" placeholder="Describe when this layout should be used." />
          </div>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" @click="layoutEditorOpen = false">Cancel</Button>
          <Button type="button" :disabled="saving || !layoutForm.name || !layoutForm.location_public_id" @click="saveLayout">
            <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
            {{ editingLayoutId ? 'Save details' : 'Create layout' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="resourceEditorOpen">
      <DialogContent class="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{{ editingResourceId ? 'Edit venue element' : 'Add venue element' }}</DialogTitle>
          <DialogDescription>Define how this item appears and whether it can hold guests.</DialogDescription>
        </DialogHeader>
        <div class="grid gap-4 py-2 sm:grid-cols-2">
          <div class="grid gap-2 sm:col-span-2">
            <Label for="resource-name">Name</Label>
            <Input id="resource-name" v-model.trim="resourceForm.name" placeholder="Table 1" />
          </div>
          <div class="grid gap-2">
            <Label>Element type</Label>
            <Select v-model="resourceForm.element_type" @update:model-value="applyElementDefaults">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="element in elementOptions" :key="element.value" :value="element.value">{{ element.label }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label>Shape</Label>
            <Select v-model="resourceForm.shape">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="round">Round</SelectItem>
                <SelectItem value="square">Square</SelectItem>
                <SelectItem value="rectangle">Rectangle</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label for="resource-capacity">Capacity</Label>
            <Input id="resource-capacity" v-model.number="resourceForm.capacity" type="number" min="1" max="1000" :disabled="!resourceForm.is_bookable" />
          </div>
          <div class="flex items-center justify-between gap-4 rounded-xl border px-4 py-3">
            <div>
              <Label for="resource-bookable">Guest seating</Label>
              <p class="mt-1 text-xs text-muted-foreground">Allow guests to be assigned here.</p>
            </div>
            <Switch id="resource-bookable" v-model:checked="resourceForm.is_bookable" />
          </div>
          <div class="grid gap-2">
            <Label for="resource-width">Width (%)</Label>
            <Input id="resource-width" v-model.number="resourceForm.width" type="number" min="4" max="80" />
          </div>
          <div class="grid gap-2">
            <Label for="resource-height">Height (%)</Label>
            <Input id="resource-height" v-model.number="resourceForm.height" type="number" min="4" max="80" />
          </div>
          <div class="grid gap-2 sm:col-span-2 sm:max-w-48">
            <Label for="resource-rotation">Rotation</Label>
            <Input id="resource-rotation" v-model.number="resourceForm.rotation" type="number" min="-180" max="180" />
          </div>
        </div>
        <DialogFooter class="gap-2 sm:justify-between">
          <Button v-if="editingResourceId" type="button" variant="ghost" class="text-destructive" :disabled="saving" @click="removeResource">
            <Trash2 class="h-4 w-4" aria-hidden="true" />
            Remove
          </Button>
          <div class="flex justify-end gap-2">
            <Button type="button" variant="outline" @click="resourceEditorOpen = false">Cancel</Button>
            <Button type="button" :disabled="saving || !resourceForm.name" @click="saveResource">
              <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
              {{ editingResourceId ? 'Save element' : 'Add element' }}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import {
  Armchair,
  Building2,
  DoorOpen,
  GlassWater,
  Landmark,
  LayoutTemplate,
  Link2,
  Loader2,
  Maximize2,
  Music2,
  PartyPopper,
  Pencil,
  PencilRuler,
  Plus,
  Store,
  Trash2,
  UtensilsCrossed,
} from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import ResourceFloorPlan from '@/components/scheduling/ResourceFloorPlan.vue'

const props = defineProps({
  businessId: { type: String, required: true },
  event: { type: Object, required: true },
  layouts: { type: Array, default: () => [] },
  resources: { type: Array, default: () => [] },
  resourceTypes: { type: Array, default: () => [] },
  locations: { type: Array, default: () => [] },
})

const emit = defineEmits(['updated'])
const { apiFetch } = useApiClient()
const localLayouts = ref([...props.layouts])
const localResources = ref([...props.resources])
const localResourceTypes = ref([...props.resourceTypes])
const selectedLayoutId = ref(props.event.layout_public_id || 'none')
const selectedResourceId = ref('')
const layoutEditorOpen = ref(false)
const resourceEditorOpen = ref(false)
const fullscreenOpen = ref(false)
const editingLayoutId = ref('')
const editingResourceId = ref('')
const saving = ref(false)

const layoutForm = reactive({
  name: '',
  layout_type: 'event',
  location_public_id: props.event.location_public_id || '',
  description: '',
  width: 100,
  height: 100,
  is_active: true,
})
const resourceForm = reactive({
  resource_type_public_id: '',
  name: '',
  element_type: 'table',
  is_bookable: true,
  capacity: 8,
  shape: 'round',
  width: 14,
  height: 14,
  rotation: 0,
  position_x: 20,
  position_y: 20,
})

const elementOptions = [
  { value: 'table', label: 'Table or seating', icon: Armchair },
  { value: 'stage', label: 'Stage', icon: PartyPopper },
  { value: 'dance_floor', label: 'Dance floor', icon: Music2 },
  { value: 'bar', label: 'Bar', icon: GlassWater },
  { value: 'buffet', label: 'Buffet station', icon: UtensilsCrossed },
  { value: 'entrance', label: 'Entrance', icon: DoorOpen },
  { value: 'booth', label: 'Booth or exhibit', icon: Store },
  { value: 'service', label: 'Service area', icon: Building2 },
  { value: 'decor', label: 'Decor or landmark', icon: Landmark },
  { value: 'other', label: 'Custom element', icon: Building2 },
]

const matchingLayouts = computed(() => localLayouts.value.filter(layout => (
  !props.event.location_public_id || layout.location_public_id === props.event.location_public_id
)))
const selectedLayout = computed(() => matchingLayouts.value.find(layout => layout.public_id === selectedLayoutId.value) || null)
const floorResources = computed(() => localResources.value.filter(resource => resource.layout_public_id === selectedLayoutId.value))
const totalSeats = computed(() => floorResources.value
  .filter(resource => resource.is_active && resource.is_bookable)
  .reduce((total, resource) => total + Number(resource.capacity || 0), 0))
const associationDirty = computed(() => selectedLayoutId.value !== (props.event.layout_public_id || 'none'))

watch(() => props.layouts, value => { localLayouts.value = [...value] })
watch(() => props.resources, value => { localResources.value = [...value] })
watch(() => props.resourceTypes, value => { localResourceTypes.value = [...value] })
watch(() => props.event.layout_public_id, value => { selectedLayoutId.value = value || 'none' })

async function associateLayout() {
  saving.value = true
  try {
    const saved = await apiFetch(`businesses/${props.businessId}/venue-events/${props.event.public_id}/`, {
      method: 'PATCH',
      body: { layout_public_id: selectedLayoutId.value === 'none' ? null : selectedLayoutId.value },
    })
    emit('updated', saved)
    toast({ title: 'Event venue updated', description: saved.layout_name ? `${saved.layout_name} is now assigned to this event.` : 'The floor plan was removed from this event.' })
  } catch (error) {
    failedToast(error, 'The event layout could not be assigned.')
  } finally {
    saving.value = false
  }
}

function openLayoutEditor(layout = null) {
  editingLayoutId.value = layout?.public_id || ''
  Object.assign(layoutForm, {
    name: layout?.name || '',
    layout_type: layout?.layout_type || 'event',
    location_public_id: layout?.location_public_id || props.event.location_public_id || props.locations[0]?.public_id || '',
    description: layout?.description || '',
    width: Number(layout?.width || 100),
    height: Number(layout?.height || 100),
    is_active: layout?.is_active ?? true,
  })
  layoutEditorOpen.value = true
}

async function saveLayout() {
  saving.value = true
  try {
    const url = editingLayoutId.value
      ? `businesses/${props.businessId}/resource-layouts/${editingLayoutId.value}/`
      : `businesses/${props.businessId}/resource-layouts/`
    const saved = await apiFetch(url, {
      method: editingLayoutId.value ? 'PATCH' : 'POST',
      body: { ...layoutForm },
    })
    const index = localLayouts.value.findIndex(layout => layout.public_id === saved.public_id)
    if (index >= 0) localLayouts.value.splice(index, 1, saved)
    else localLayouts.value.push(saved)
    selectedLayoutId.value = saved.public_id
    layoutEditorOpen.value = false
    toast({ title: editingLayoutId.value ? 'Layout details updated' : 'Venue layout created', description: `${saved.name} is ready for event elements.` })
    if (!editingLayoutId.value) await associateLayout()
  } catch (error) {
    failedToast(error, 'The venue layout could not be saved.')
  } finally {
    saving.value = false
  }
}

function openResourceEditor(resource = null, elementType = 'table') {
  const defaults = elementDefaults(resource?.element_type || elementType)
  editingResourceId.value = resource?.public_id || ''
  selectedResourceId.value = resource?.public_id || ''
  Object.assign(resourceForm, {
    resource_type_public_id: resource?.resource_type_public_id || '',
    name: resource?.name || `${defaults.label} ${floorResources.value.length + 1}`,
    element_type: resource?.element_type || elementType,
    is_bookable: resource?.is_bookable ?? defaults.isBookable,
    capacity: Number(resource?.capacity || defaults.capacity),
    shape: resource?.shape || defaults.shape,
    width: Number(resource?.width || defaults.width),
    height: Number(resource?.height || defaults.height),
    rotation: Number(resource?.rotation || 0),
    position_x: Number(resource?.position_x || 20 + (floorResources.value.length % 4) * 18),
    position_y: Number(resource?.position_y || 24 + (floorResources.value.length % 3) * 24),
  })
  resourceEditorOpen.value = true
}

function applyElementDefaults(value) {
  const defaults = elementDefaults(value)
  if (!editingResourceId.value) resourceForm.name = `${defaults.label} ${floorResources.value.length + 1}`
  Object.assign(resourceForm, {
    is_bookable: defaults.isBookable,
    capacity: defaults.capacity,
    shape: defaults.shape,
    width: defaults.width,
    height: defaults.height,
  })
}

async function ensureResourceType() {
  const desiredName = elementDefaults(resourceForm.element_type).label
  const existing = localResourceTypes.value.find(type => type.name.toLowerCase() === desiredName.toLowerCase())
    || localResourceTypes.value[0]
  if (existing) return existing
  const created = await apiFetch(`businesses/${props.businessId}/resource-types/`, {
    method: 'POST',
    body: {
      name: desiredName,
      singular_label: desiredName,
      plural_label: `${desiredName}s`,
      icon: 'layout-grid',
      is_active: true,
    },
  })
  localResourceTypes.value.push(created)
  return created
}

async function saveResource() {
  if (!selectedLayout.value) return
  saving.value = true
  try {
    const resourceType = localResourceTypes.value.find(type => type.public_id === resourceForm.resource_type_public_id)
      || await ensureResourceType()
    const url = editingResourceId.value
      ? `businesses/${props.businessId}/resources/${editingResourceId.value}/`
      : `businesses/${props.businessId}/resources/`
    const saved = await apiFetch(url, {
      method: editingResourceId.value ? 'PATCH' : 'POST',
      body: {
        ...resourceForm,
        resource_type_public_id: resourceType.public_id,
        location_public_id: selectedLayout.value.location_public_id,
        layout_public_id: selectedLayout.value.public_id,
        capacity: Number(resourceForm.capacity || 1),
        width: Number(resourceForm.width),
        height: Number(resourceForm.height),
        rotation: Number(resourceForm.rotation),
        position_x: Number(resourceForm.position_x),
        position_y: Number(resourceForm.position_y),
        is_active: true,
        metadata: {},
      },
    })
    const index = localResources.value.findIndex(resource => resource.public_id === saved.public_id)
    if (index >= 0) localResources.value.splice(index, 1, saved)
    else localResources.value.push(saved)
    selectedResourceId.value = saved.public_id
    resourceEditorOpen.value = false
    toast({ title: editingResourceId.value ? 'Venue element updated' : 'Venue element added', description: `${saved.name} was saved to ${selectedLayout.value.name}.` })
  } catch (error) {
    failedToast(error, 'The venue element could not be saved.')
  } finally {
    saving.value = false
  }
}

async function removeResource() {
  const resource = localResources.value.find(item => item.public_id === editingResourceId.value)
  if (!resource) return
  saving.value = true
  try {
    await apiFetch(`businesses/${props.businessId}/resources/${resource.public_id}/`, { method: 'DELETE' })
    localResources.value = localResources.value.filter(item => item.public_id !== resource.public_id)
    selectedResourceId.value = ''
    resourceEditorOpen.value = false
    toast({ title: 'Venue element removed', description: `${resource.name} was removed from the shared layout.` })
  } catch (error) {
    failedToast(error, 'The venue element could not be removed.')
  } finally {
    saving.value = false
  }
}

async function persistResourceMove({ resource, position_x, position_y }) {
  const previous = { position_x: resource.position_x, position_y: resource.position_y }
  Object.assign(resource, { position_x, position_y })
  try {
    await apiFetch(`businesses/${props.businessId}/resources/${resource.public_id}/`, {
      method: 'PATCH',
      body: { position_x, position_y },
    })
  } catch (error) {
    Object.assign(resource, previous)
    failedToast(error, 'The new position could not be saved.')
  }
}

function elementDefaults(value) {
  return {
    table: { label: 'Table', isBookable: true, capacity: 8, shape: 'round', width: 14, height: 14 },
    stage: { label: 'Stage', isBookable: false, capacity: 1, shape: 'rectangle', width: 34, height: 14 },
    dance_floor: { label: 'Dance floor', isBookable: false, capacity: 1, shape: 'square', width: 28, height: 28 },
    bar: { label: 'Bar', isBookable: false, capacity: 1, shape: 'rectangle', width: 24, height: 10 },
    buffet: { label: 'Buffet', isBookable: false, capacity: 1, shape: 'rectangle', width: 28, height: 10 },
    entrance: { label: 'Entrance', isBookable: false, capacity: 1, shape: 'rectangle', width: 18, height: 8 },
    booth: { label: 'Booth', isBookable: true, capacity: 4, shape: 'rectangle', width: 18, height: 14 },
    service: { label: 'Service area', isBookable: false, capacity: 1, shape: 'rectangle', width: 20, height: 12 },
    decor: { label: 'Decor', isBookable: false, capacity: 1, shape: 'round', width: 10, height: 10 },
    other: { label: 'Custom element', isBookable: false, capacity: 1, shape: 'rectangle', width: 18, height: 12 },
  }[value] || { label: 'Element', isBookable: false, capacity: 1, shape: 'rectangle', width: 18, height: 12 }
}

function failedToast(error, fallback) {
  toast({
    title: fallback,
    description: error?.data?.error?.message || error?.data?.detail || 'Please review the details and try again.',
    variant: 'destructive',
  })
}
</script>
