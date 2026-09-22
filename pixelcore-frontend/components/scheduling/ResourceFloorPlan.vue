<template>
  <div
    ref="floorRef"
    class="relative isolate w-full select-none overflow-hidden rounded-2xl border border-border bg-[#fbfcfa] shadow-inner"
    :class="expanded ? 'h-full min-h-0' : 'min-h-[580px]'"
    style="touch-action: none"
    @pointermove="moveDrag"
    @pointerup="finishDrag"
    @pointercancel="cancelDrag"
  >
    <div
      class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(100,116,139,.16)_1px,transparent_0)] [background-size:24px_24px]"
    />
    <div
      class="pointer-events-none absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-background/95 to-transparent"
    />

    <div
      class="pointer-events-none absolute left-4 top-4 z-30 flex flex-wrap gap-2 rounded-xl border bg-background/90 p-2 text-[11px] font-medium shadow-sm backdrop-blur"
    >
      <Badge class="border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-50">
        Green: available
      </Badge>
      <Badge class="border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-50">
        Red: reserved
      </Badge>
      <Badge class="border-sky-200 bg-sky-50 text-sky-700 hover:bg-sky-50">
        Blue: venue feature
      </Badge>
      <Badge variant="outline" class="bg-background/90 text-muted-foreground">
        Drag to rearrange
      </Badge>
    </div>

    <div
      v-if="!resources.length"
      class="absolute inset-0 flex flex-col items-center justify-center px-6 text-center"
    >
      <Building2 class="h-10 w-10 text-muted-foreground/35" aria-hidden="true" />
      <p class="mt-3 text-sm font-semibold">This venue plan is empty</p>
      <p class="mt-1 max-w-xs text-xs leading-5 text-muted-foreground">
        Add seating, a stage, an entrance, or another venue element to begin.
      </p>
    </div>

    <Button
      v-for="resource in resources"
      :key="resource.public_id"
      type="button"
      variant="outline"
      class="group absolute h-auto -translate-x-1/2 -translate-y-1/2 cursor-grab flex-col gap-0 overflow-hidden border-2 p-3 text-center shadow-md transition-[box-shadow,transform,background-color,border-color] hover:z-20 hover:scale-[1.025] hover:shadow-lg active:cursor-grabbing"
      :class="[
        shapeClass(resource.shape),
        resourceStateClass(resource),
        selectedResourceId === resource.public_id
          ? 'z-20 ring-2 ring-primary ring-offset-2'
          : 'z-10',
        dragging?.resourceId === resource.public_id ? 'scale-105 shadow-xl' : '',
      ]"
      :style="resourceStyle(resource)"
      :aria-label="resourceAriaLabel(resource)"
      @pointerdown="startDrag($event, resource)"
      @click="selectResource(resource)"
    >
      <Grip
        class="absolute right-1.5 top-1.5 h-3 w-3 opacity-25 transition-opacity group-hover:opacity-60"
        aria-hidden="true"
      />
      <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-background/70 shadow-sm">
        <component :is="elementIcon(resource.element_type)" class="h-6 w-6 opacity-85" aria-hidden="true" />
      </span>
      <span class="mt-2 max-w-[92%] truncate text-xs font-extrabold sm:text-sm">
        {{ resource.name }}
      </span>
      <span class="mt-0.5 max-w-[92%] truncate text-[10px] font-medium opacity-70 sm:text-[11px]">
        {{ resource.is_bookable ? `${resource.capacity} ${resource.capacity === 1 ? 'seat' : 'seats'}` : elementLabel(resource.element_type) }}
      </span>
      <span class="mt-2 flex items-center gap-1.5 rounded-full bg-background/65 px-2 py-1 text-[9px] font-bold shadow-sm">
        <span class="h-1.5 w-1.5 rounded-full" :class="statusDotClass(resource)" />
        {{ statusLabel(resource) }}
      </span>
    </Button>
  </div>
</template>

<script setup>
import {
  Armchair,
  Building2,
  DoorOpen,
  GlassWater,
  Grip,
  Landmark,
  Music2,
  PartyPopper,
  Store,
  UtensilsCrossed,
} from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const props = defineProps({
  resources: {
    type: Array,
    default: () => [],
  },
  bookings: {
    type: Array,
    default: () => [],
  },
  selectedResourceId: {
    type: String,
    default: '',
  },
  resourceWord: {
    type: String,
    default: 'Resource',
  },
  expanded: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select', 'move'])
const floorRef = ref(null)
const localPositions = reactive({})
const dragging = ref(null)
const suppressClickUntil = ref(0)
const activeStatuses = new Set(['pending', 'confirmed'])

watch(
  () => props.resources,
  (resources) => {
    for (const resource of resources) {
      if (dragging.value?.resourceId === resource.public_id) continue
      localPositions[resource.public_id] = {
        x: Number(resource.position_x ?? 20),
        y: Number(resource.position_y ?? 20),
      }
    }
  },
  { immediate: true, deep: true },
)

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value))
}

function activeBookings(resource) {
  return props.bookings.filter(
    booking => activeStatuses.has(booking.status)
      && booking.resources?.some(item => item.public_id === resource.public_id),
  )
}

function shapeClass(shape) {
  if (shape === 'rectangle') return 'rounded-lg'
  if (shape === 'square') return 'rounded-xl'
  return 'rounded-full'
}

function resourceStateClass(resource) {
  if (!resource.is_active) {
    return 'border-slate-300 bg-slate-100 text-slate-600 hover:border-slate-400 hover:bg-slate-100'
  }
  if (!resource.is_bookable) {
    return {
      stage: 'border-violet-300 bg-violet-100 text-violet-950 hover:border-violet-400 hover:bg-violet-100',
      dance_floor: 'border-fuchsia-300 bg-fuchsia-50 text-fuchsia-950 hover:border-fuchsia-400 hover:bg-fuchsia-50',
      bar: 'border-cyan-300 bg-cyan-50 text-cyan-950 hover:border-cyan-400 hover:bg-cyan-50',
      buffet: 'border-amber-300 bg-amber-50 text-amber-950 hover:border-amber-400 hover:bg-amber-50',
      entrance: 'border-blue-300 bg-blue-50 text-blue-950 hover:border-blue-400 hover:bg-blue-50',
    }[resource.element_type] || 'border-sky-300 bg-sky-50 text-sky-950 hover:border-sky-400 hover:bg-sky-50'
  }
  return activeBookings(resource).length
    ? 'border-rose-300 bg-rose-100 text-rose-950 hover:border-rose-400 hover:bg-rose-100'
    : 'border-emerald-300 bg-emerald-100 text-emerald-950 hover:border-emerald-400 hover:bg-emerald-100'
}

function statusLabel(resource) {
  if (!resource.is_active) return 'Hidden'
  if (!resource.is_bookable) return 'Plan element'
  const count = activeBookings(resource).length
  return count ? `${count} ${count === 1 ? 'booking' : 'bookings'}` : 'Available'
}

function statusDotClass(resource) {
  if (!resource.is_active) return 'bg-slate-500'
  if (!resource.is_bookable) return 'bg-sky-500'
  return activeBookings(resource).length ? 'bg-rose-500' : 'bg-emerald-500'
}

function resourceStyle(resource) {
  const position = localPositions[resource.public_id] || {
    x: Number(resource.position_x ?? 20),
    y: Number(resource.position_y ?? 20),
  }
  const compactShape = resource.shape === 'round' || resource.shape === 'square'
  return {
    left: `${position.x}%`,
    top: `${position.y}%`,
    width: `${clamp(Number(resource.width || 16), 4, 80)}%`,
    minWidth: '7.5rem',
    maxWidth: compactShape ? '11rem' : 'none',
    height: compactShape ? 'auto' : `${clamp(Number(resource.height || 16), 4, 80)}%`,
    minHeight: '5.5rem',
    aspectRatio: compactShape ? '1 / 1' : 'auto',
    rotate: `${clamp(Number(resource.rotation || 0), -180, 180)}deg`,
  }
}

function resourceAriaLabel(resource) {
  if (!resource.is_active) {
    return `${resource.name}, ${resource.capacity} capacity, inactive. Drag to move or press Enter to view.`
  }
  if (!resource.is_bookable) {
    return `${resource.name}, ${elementLabel(resource.element_type)}, venue feature. Drag to move or press Enter to view.`
  }
  const count = activeBookings(resource).length
  return `${resource.name}, ${resource.capacity} capacity, ${count ? `${count} bookings` : 'available'}. Drag to move or press Enter to view.`
}

function elementIcon(value) {
  return {
    table: Armchair,
    stage: PartyPopper,
    dance_floor: Music2,
    bar: GlassWater,
    buffet: UtensilsCrossed,
    entrance: DoorOpen,
    booth: Store,
    service: Building2,
    decor: Landmark,
    other: Building2,
  }[value] || Building2
}

function elementLabel(value) {
  return {
    table: 'Seating',
    stage: 'Stage',
    dance_floor: 'Dance floor',
    bar: 'Bar',
    buffet: 'Buffet station',
    entrance: 'Entrance',
    booth: 'Booth',
    service: 'Service area',
    decor: 'Decor',
    other: 'Venue element',
  }[value] || 'Venue element'
}

function startDrag(event, resource) {
  if (event.button !== 0 && event.pointerType === 'mouse') return
  event.currentTarget.setPointerCapture?.(event.pointerId)
  dragging.value = {
    resourceId: resource.public_id,
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    moved: false,
  }
}

function moveDrag(event) {
  if (!dragging.value || event.pointerId !== dragging.value.pointerId || !floorRef.value) return
  const rectangle = floorRef.value.getBoundingClientRect()
  const delta = Math.hypot(
    event.clientX - dragging.value.startX,
    event.clientY - dragging.value.startY,
  )
  if (delta > 4) dragging.value.moved = true
  if (!dragging.value.moved) return

  event.preventDefault()
  localPositions[dragging.value.resourceId] = {
    x: Math.round(clamp(((event.clientX - rectangle.left) / rectangle.width) * 100, 6, 94)),
    y: Math.round(clamp(((event.clientY - rectangle.top) / rectangle.height) * 100, 10, 92)),
  }
}

function finishDrag(event) {
  if (!dragging.value || event.pointerId !== dragging.value.pointerId) return
  const drag = dragging.value
  dragging.value = null
  if (!drag.moved) return

  suppressClickUntil.value = Date.now() + 250
  const resource = props.resources.find(item => item.public_id === drag.resourceId)
  const position = localPositions[drag.resourceId]
  if (resource && position) {
    emit('move', {
      resource,
      position_x: position.x,
      position_y: position.y,
    })
  }
}

function cancelDrag() {
  if (!dragging.value) return
  const resource = props.resources.find(item => item.public_id === dragging.value.resourceId)
  if (resource) {
    localPositions[resource.public_id] = {
      x: Number(resource.position_x ?? 20),
      y: Number(resource.position_y ?? 20),
    }
  }
  dragging.value = null
}

function selectResource(resource) {
  if (Date.now() < suppressClickUntil.value) return
  emit('select', resource)
}
</script>
