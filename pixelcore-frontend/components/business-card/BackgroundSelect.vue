<template>
  <div class="space-y-2">
    <Label :for="controlId">{{ label }}</Label>
    <Select v-model="model">
      <SelectTrigger :id="controlId">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="option in options"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  options: { type: Array, required: true },
})

const model = defineModel({ type: String, required: true })
const controlId = useId()
</script>
