<template>
  <main class="business-card-public min-h-screen overflow-x-hidden" :style="pageStyle">
    <div class="business-card-public__glow" aria-hidden="true" />

    <header class="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-5 sm:px-6 lg:px-8">
      <div class="flex min-w-0 items-center gap-3">
        <div class="grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-full border border-white/20 bg-white/10">
          <img
            v-if="card?.logo_url && !headerLogoFailed"
            :src="card.logo_url"
            :alt="`${card.business_name} logo`"
            class="h-full w-full object-contain p-1.5"
            @error="headerLogoFailed = true"
          />
          <span v-else class="font-bold text-white" aria-hidden="true">
            {{ businessInitial }}
          </span>
        </div>
        <div class="min-w-0 text-white">
          <p class="truncate text-sm font-semibold">{{ card?.business_name || 'Business card' }}</p>
          <p class="truncate text-xs text-white/60">Digital business card</p>
        </div>
      </div>

      <ButtonAnchor
        v-if="card?.business_website_url"
        :href="card.business_website_url"
        target="_blank"
        rel="noopener"
        variant="secondary"
        size="sm"
        class="gap-2"
      >
        Visit website
        <ArrowUpRight class="h-4 w-4" aria-hidden="true" />
      </ButtonAnchor>
    </header>

    <section class="relative z-10 mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-7xl items-center px-4 pb-16 pt-6 sm:px-6 lg:px-8">
      <StatePanel
        v-if="pending"
        kind="loading"
        class="mx-auto w-full max-w-lg border-white/15 bg-white/95"
        title="Opening business card"
        message="Preparing the public contact card."
      />
      <StatePanel
        v-else-if="error || !card"
        kind="error"
        class="mx-auto w-full max-w-lg border-white/15 bg-white/95"
        title="Business card unavailable"
        message="This card may be private, unpublished, or no longer available."
      />

      <div v-else class="mx-auto grid w-full items-center gap-8 lg:grid-cols-[minmax(0,1fr)_18rem] lg:gap-12">
        <div class="min-w-0">
          <BusinessCardCanvas
            :card="card"
            :qr-fallback-url="publicCardUrl"
            printable
          />
        </div>

        <aside class="mx-auto w-full max-w-md border-t border-white/20 pt-6 text-white lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">
            Connect
          </p>
          <h1 class="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            {{ card.display_name }}
          </h1>
          <p v-if="card.job_title" class="mt-2 text-sm text-white/70">
            {{ card.job_title }} · {{ card.business_name }}
          </p>
          <p v-if="card.headline" class="mt-5 text-sm leading-6 text-white/70">
            {{ card.headline }}
          </p>

          <nav
            v-if="card.social_links?.length"
            class="mt-6 flex flex-wrap gap-2"
            aria-label="Social profiles"
          >
            <ButtonAnchor
              v-for="profile in card.social_links"
              :key="profile.platform"
              :href="profile.url"
              target="_blank"
              rel="noopener noreferrer"
              variant="outline"
              size="icon"
              class="border-white/25 bg-transparent text-white hover:bg-white/10 hover:text-white"
              :aria-label="`Open ${socialPlatformLabel(profile.platform)}`"
              :title="socialPlatformLabel(profile.platform)"
            >
              <SocialPlatformIcon
                :platform="profile.platform"
                class="h-4 w-4"
              />
            </ButtonAnchor>
          </nav>

          <div class="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-1 print:hidden">
            <Button
              type="button"
              variant="secondary"
              class="gap-2"
              @click="copyPublicLink"
            >
              <Check v-if="copied" class="h-4 w-4" aria-hidden="true" />
              <Copy v-else class="h-4 w-4" aria-hidden="true" />
              {{ copied ? 'Link copied' : 'Copy card link' }}
            </Button>
            <Button
              type="button"
              variant="outline"
              class="gap-2 border-white/30 bg-transparent text-white hover:bg-white/10 hover:text-white"
              @click="printCard"
            >
              <Printer class="h-4 w-4" aria-hidden="true" />
              Print both sides
            </Button>
          </div>

          <p class="mt-5 flex items-start gap-2 text-xs leading-5 text-white/50">
            <ShieldCheck class="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            Shared by {{ card.display_name }} through PixelCore.
          </p>
        </aside>
      </div>
    </section>
  </main>
</template>

<script setup>
import SocialPlatformIcon from '@/components/site/SocialPlatformIcon.vue'
import {
  ArrowUpRight,
  Check,
  Copy,
  Printer,
  ShieldCheck,
} from 'lucide-vue-next'
import { socialPlatformLabel } from '@/utils/socialProfiles'

definePageMeta({ layout: false })

const route = useRoute()
const requestUrl = useRequestURL()
const config = useRuntimeConfig()
const baseURL = import.meta.server
  ? config.apiInternalBaseUrl
  : config.public.apiBaseUrl
const copied = ref(false)
const headerLogoFailed = ref(false)
let copiedTimer

const {
  data: card,
  pending,
  error,
} = await useFetch(`public/business-cards/${route.params.cardId}/`, {
  baseURL,
  key: `business-card-${route.params.cardId}`,
})

const businessInitial = computed(() =>
  String(card.value?.business_name || 'B').charAt(0).toUpperCase(),
)
const publicCardUrl = computed(() =>
  new URL(route.path, requestUrl.origin).href,
)
const pageStyle = computed(() => ({
  '--public-card-primary': card.value?.theme?.primary_color || '#165B4C',
  '--public-card-secondary': card.value?.theme?.secondary_color || '#17362F',
  '--public-card-accent': card.value?.theme?.accent_color || '#D8922B',
}))

watch(
  () => card.value?.logo_url,
  () => {
    headerLogoFailed.value = false
  },
)

useHead(() => ({
  title: card.value
    ? `${card.value.display_name} · ${card.value.business_name}`
    : 'Business card · PixelCore',
  meta: [
    {
      name: 'description',
      content: card.value?.headline || `Contact ${card.value?.display_name || 'this business'}.`,
    },
    { name: 'robots', content: 'noindex, nofollow' },
  ],
}))

onMounted(() => {
  if (route.query.print === '1') {
    window.setTimeout(() => window.print(), 800)
  }
})

onBeforeUnmount(() => {
  window.clearTimeout(copiedTimer)
})

async function copyPublicLink() {
  await navigator.clipboard.writeText(window.location.href.split('?')[0])
  copied.value = true
  window.clearTimeout(copiedTimer)
  copiedTimer = window.setTimeout(() => {
    copied.value = false
  }, 2000)
}

function printCard() {
  window.print()
}
</script>

<style scoped>
.business-card-public {
  color: white;
  background:
    radial-gradient(circle at 15% 20%, color-mix(in srgb, var(--public-card-accent) 25%, transparent), transparent 32rem),
    linear-gradient(145deg, var(--public-card-secondary), color-mix(in srgb, var(--public-card-primary) 62%, #071412));
}

.business-card-public__glow {
  position: fixed;
  inset: auto -12rem -18rem auto;
  width: 34rem;
  aspect-ratio: 1;
  border-radius: 999px;
  background: color-mix(in srgb, var(--public-card-accent) 18%, transparent);
  filter: blur(1px);
  pointer-events: none;
}

@media print {
  .business-card-public {
    min-height: auto;
    background: white;
  }

  .business-card-public > :not(section),
  aside {
    display: none;
  }

  section {
    display: block;
    min-height: auto;
    max-width: none;
    padding: 0;
  }

  section > div {
    display: block;
  }
}
</style>
