<template><section class="workspace-page space-y-5"><PageHeader title="New collection" description="Create an editorial product group for the public storefront."><template #actions><ButtonLink variant="outline" to="/workspace/sell/collections">Cancel</ButtonLink></template></PageHeader><CollectionEditor @saved="saved" /></section></template>
<script setup>
import { toast } from '@/components/ui/toast'
async function saved(collection) { toast({ title: 'Collection created', description: `${collection.name} is ready to merchandise.` }); await navigateTo(`/workspace/sell/collections/${collection.public_id}`) }
</script>
