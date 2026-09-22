<template>
  <WorkspaceShell v-if="showWorkspace" @sign-out="signOut">
    <slot />
  </WorkspaceShell>
  <div v-else class="min-h-screen">
    <header class="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <div class="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <NuxtLink to="/" aria-label="PixelCore home">
          <PixelCoreMark />
        </NuxtLink>

        <nav v-if="auth.isAuthenticated && !auth.user?.needs_onboarding" aria-label="Primary navigation" class="flex items-center gap-1 sm:gap-3">
          <ButtonLink variant="outline" :to="accountHome(auth.user)">
            {{ accountHome(auth.user) === '/employee' ? 'Employee portal' : 'Open workspace' }}
          </ButtonLink>
        </nav>

        <nav v-else-if="!auth.isAuthenticated" aria-label="Account navigation" class="flex items-center gap-2">
          <NuxtLink class="rounded-md px-3 py-2 text-sm font-semibold hover:bg-muted" to="/login">Sign in</NuxtLink>
          <ButtonLink class="rounded-md px-4 py-2 text-sm font-bold" to="/register">Create workspace</ButtonLink>
        </nav>
      </div>
    </header>

    <main>
      <slot />
    </main>
  </div>
  <Toaster />
</template>

<script setup>
import { Toaster } from '@/components/ui/toast'
import { accountHome } from '@/utils/accountHome'

const auth = useAuthStore()
const business = useBusinessStore()
const route = useRoute()
const showWorkspace = computed(() => /^\/(workspace|settings)(\/|$)/.test(route.path))

onMounted(async () => {
  if (auth.isAuthenticated && !business.activeBusiness) {
    await business.loadBusinesses().catch(() => {})
  }
})

async function signOut() {
  await auth.logout()
  business.$reset()
  await navigateTo('/')
}
</script>
