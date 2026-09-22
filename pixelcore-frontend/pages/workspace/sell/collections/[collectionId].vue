<template><section class="workspace-page space-y-5"><PageHeader :title="collection?.name || 'Collection'" description="Edit storefront grouping, visibility, and product membership."><template #actions><ButtonLink variant="outline" to="/workspace/sell/collections">Back to collections</ButtonLink></template></PageHeader><StatePanel v-if="loading" kind="loading" title="Loading collection" message="Retrieving products and settings." /><StatePanel v-else-if="error" kind="error" title="Collection unavailable" :message="error" /><CollectionEditor v-else :collection="collection" @saved="saved" /></section></template>
<script setup>
import { toast } from '@/components/ui/toast'
const route = useRoute(); const business = useBusinessStore(); const { apiFetch } = useApiClient(); const collection = ref(null); const loading = ref(true); const error = ref('')
onMounted(async () => { if (!business.activeBusiness) await business.loadBusinesses(); try { collection.value = await apiFetch(`businesses/${business.activeBusiness.public_id}/collections/${route.params.collectionId}/`) } catch (requestError) { error.value = requestError?.data?.error?.message || 'This collection could not be loaded.' } finally { loading.value = false } })
function saved(value) { collection.value = value; toast({ title: 'Collection updated', description: 'Storefront merchandising changes were saved.' }) }
</script>
