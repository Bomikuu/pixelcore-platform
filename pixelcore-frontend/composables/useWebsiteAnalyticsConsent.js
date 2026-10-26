import { createConsentStore } from '@sitebuilder/core'
export function useWebsiteAnalyticsConsent(scope) {
  const choice = ref('unset')
  let store, unsubscribe, stop
  const open = () => {
    unsubscribe?.()
    store?.destroy()
    choice.value = 'unset'
    const key = toValue(scope)
    if (!key) return
    let storage
    try { storage = window.localStorage } catch {}
    store = createConsentStore({ scope: key, storage, eventTarget: window })
    choice.value = store.value
    unsubscribe = store.subscribe(value => { choice.value = value })
  }
  onMounted(() => { stop = watch(() => toValue(scope), open, { immediate: true }) })
  onBeforeUnmount(() => { stop?.(); unsubscribe?.(); store?.destroy() })
  return { choice: readonly(choice), consent: computed(() => choice.value === 'allowed'), choose: value => store?.set(value) }
}
