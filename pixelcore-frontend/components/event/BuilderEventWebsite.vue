<template>
  <WebsitePage :document="builder.document" :data="builder.data" :base-url="builder.baseUrl" :widgets="widgets" :analytics-consent="!payload.guest && analytics.consent.value" />
  <WebsiteAnalyticsConsent v-if="!payload.guest" :config="builder.document.analytics" :choice="analytics.choice.value" @choose="analytics.choose" />
</template>
<script setup>
import WebsiteAnalyticsConsent from '@/components/website/WebsiteAnalyticsConsent.vue'
import { pageHead } from '@sitebuilder/core'
import { WebsitePage } from '@sitebuilder/vue'
import { createVNode, render } from 'vue'
import EventRsvpWidget from './EventRsvpWidget.vue'
const props = defineProps({ payload: {type:Object,required:true}, endpoint: {type:String,default:''} })
const analytics = useWebsiteAnalyticsConsent(() => (props.payload.event.business?.slug || props.payload.business?.slug || '') + ':' + (props.payload.event.builder?.document.analytics?.provider || 'none'))
const emit = defineEmits(['updated'])
const appContext = getCurrentInstance().appContext
const builder = computed(() => props.payload.event.builder)
const widgets = computed(() => props.payload.guest && props.endpoint ? {
  'pixelcore.event-rsvp': (element) => {
    const vnode = createVNode(EventRsvpWidget,{payload:props.payload,endpoint:props.endpoint,variant:element.dataset.wbVariant,theme:builder.value.document.theme,onUpdated:value=>emit('updated',value)})
    vnode.appContext = appContext
    render(vnode,element)
    return () => render(null,element)
  },
} : {})
useHead(() => pageHead(builder.value.document,builder.value.data,{noIndex: true}))
</script>
