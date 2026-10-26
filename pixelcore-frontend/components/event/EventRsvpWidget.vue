<template>
  <div class="builder-rsvp-widget" :class="variant === 'split' ? 'grid gap-6 lg:grid-cols-2' : ''">
    <figure v-if="variant === 'split' && hero" class="overflow-hidden">
      <img :src="hero.image_url" :alt="hero.alt_text || 'Event photograph'" class="h-full max-h-[42rem] w-full object-cover" />
    </figure>
    <div v-if="variant === 'cta' && !opened" class="py-6 text-center">
      <h2 class="mb-4 text-3xl">{{ payload.event?.website?.sections_config?.rsvp?.heading || 'Will you join us?' }}</h2>
      <Button @click="opened = true">Respond to your invitation</Button>
    </div>
    <EventRsvpResponsePage v-else :payload="payload" :endpoint="endpoint" embedded :presentation="presentation" @updated="$emit('updated', $event)" />
  </div>
</template>
<script setup>
import EventRsvpResponsePage from './EventRsvpResponsePage.vue'
const props = defineProps({ payload: {type:Object,required:true}, endpoint: {type:String,required:true}, variant: {type:String,default:'inline'}, theme: {type:Object,default:()=>({})} })
defineEmits(['updated'])
const opened = ref(false)
const hero = computed(() => props.payload.event?.website?.media?.find(item => item.placement === 'hero'))
const presentation = computed(() => ({'--event-heading':'var(--wb-heading-font), Georgia, serif','--event-body':'var(--wb-body-font), Arial, sans-serif','--event-bg':props.theme.colors?.surface || '#ffffff','--event-text':props.theme.colors?.text || '#19252e','--event-accent':props.theme.colors?.primary || '#3d5afe'}))
</script>
