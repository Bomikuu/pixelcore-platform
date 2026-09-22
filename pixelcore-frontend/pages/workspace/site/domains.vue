<template>
  <section class="workspace-page space-y-8">
    <PageHeader title="Domains" description="Connect a verified hostname before Caddy is permitted to request an on-demand certificate.">
      <template #actions><ButtonLink variant="outline"  to="/workspace/site">Back to pages</ButtonLink></template>
    </PageHeader>
    <div class="grid gap-8 xl:grid-cols-[minmax(0,1fr)_24rem]">
      <section>
        <StatePanel v-if="loading" kind="loading" title="Loading domains" message="Checking verified and pending hostnames." />
        <StatePanel v-else-if="!domains.length" title="No custom domain yet" message="Your platform subdomain and local /site/{slug} route remain available while you connect one." />
        <div v-else class="border-y bg-card">
          <div v-for="domain in domains" :key="domain.public_id" class="resource-row sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
            <div><p class="font-bold">{{ domain.hostname }}</p><p class="mt-1 text-sm text-muted-foreground">TXT: _pixelcore.{{ domain.hostname }}</p></div>
            <div class="flex items-center gap-2"><StatusPill :value="domain.is_active ? 'active' : 'pending'" /><Button variant="outline" v-if="!domain.is_active" type="button" @click="verify(domain)">Verify DNS</Button></div>
          </div>
        </div>
      </section>
      <form class="space-y-4 border-t pt-6 xl:border-l xl:border-t-0 xl:pl-8 xl:pt-0" @submit.prevent="addDomain">
        <h2 class="font-bold">Connect a hostname</h2>
        <div><label class="field-label" for="domain-hostname">Hostname</label><Input id="domain-hostname" v-model.trim="hostname" placeholder="shop.example.com" required /></div>
        <p class="text-xs leading-5 text-muted-foreground">Add the TXT record shown after saving. Domain activation occurs only after PixelCore resolves the exact verification value.</p>
        <p v-if="message" :class="messageTone" aria-live="polite" class="text-sm">{{ message }}</p>
        <Button class="w-full" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Add domain' }}</Button>
      </form>
    </div>
  </section>
</template>

<script setup>
const business = useBusinessStore()
const { apiFetch } = useApiClient()
const domains = ref([])
const hostname = ref('')
const loading = ref(true)
const saving = ref(false)
const message = ref('')
const messageTone = ref('text-muted-foreground')

onMounted(async () => { if (!business.activeBusiness) await business.loadBusinesses(); await load() })
async function load() { if (!business.activeBusiness) return; loading.value = true; domains.value = await apiFetch(`businesses/${business.activeBusiness.public_id}/site/domains/`).catch(() => []); loading.value = false }
async function addDomain() { saving.value = true; message.value = ''; try { const domain = await apiFetch(`businesses/${business.activeBusiness.public_id}/site/domains/`, { method: 'POST', body: { hostname: hostname.value } }); domains.value.unshift(domain); hostname.value = ''; message.value = `Add TXT value pixelcore-verification=${domain.verification_token}`; messageTone.value = 'text-foreground' } catch (error) { message.value = error?.data?.error?.message || 'The domain could not be added.'; messageTone.value = 'text-destructive' } finally { saving.value = false } }
async function verify(domain) { message.value = ''; try { const updated = await apiFetch(`businesses/${business.activeBusiness.public_id}/site/domains/${domain.public_id}/verify/`, { method: 'POST' }); Object.assign(domain, updated); message.value = `${domain.hostname} is verified and active.`; messageTone.value = 'text-primary' } catch (error) { message.value = error?.data?.error?.message || 'The DNS record is not visible yet.'; messageTone.value = 'text-destructive' } }
</script>

