<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Button
        :id="id"
        type="button"
        variant="outline"
        :class="cn(
          'w-full justify-start gap-2 text-left font-normal',
          !modelValue && 'text-muted-foreground',
          props.class,
        )"
        :aria-label="label"
      >
        <CalendarDays class="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
        <span class="truncate">{{ displayValue }}</span>
      </Button>
    </PopoverTrigger>
    <PopoverContent align="start" class="w-auto p-0">
      <Calendar
        :model-value="selectedDate"
        :min-value="minimumDate"
        :max-value="maximumDate"
        :calendar-label="label"
        initial-focus
        @update:model-value="selectDate"
      />
    </PopoverContent>
  </Popover>
</template>

<script setup>
import { parseDate } from '@internationalized/date'
import { CalendarDays } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'

const props = defineProps({
  modelValue: { type: String, default: '' },
  min: { type: String, default: '' },
  max: { type: String, default: '' },
  id: { type: String, default: undefined },
  label: { type: String, default: 'Choose a date' },
  class: { type: null, default: undefined },
})

const emit = defineEmits(['update:modelValue', 'change'])
const open = ref(false)

const selectedDate = computed(() => parseCalendarDate(props.modelValue))
const minimumDate = computed(() => parseCalendarDate(props.min))
const maximumDate = computed(() => parseCalendarDate(props.max))
const displayValue = computed(() => {
  if (!props.modelValue) return 'Choose a date'
  const date = new Date(`${props.modelValue}T12:00:00`)
  if (Number.isNaN(date.getTime())) return 'Choose a date'
  return new Intl.DateTimeFormat('en-PH', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
})

function parseCalendarDate(value) {
  if (!value) return undefined
  try {
    return parseDate(value)
  } catch {
    return undefined
  }
}

function selectDate(value) {
  if (!value) return
  emit('update:modelValue', value.toString())
  emit('change', value.toString())
  open.value = false
}
</script>
