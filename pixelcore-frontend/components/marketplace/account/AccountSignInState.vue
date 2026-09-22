<template>
  <StatePanel
    title="Sign in to continue"
    message="This section contains private customer activity for this business."
  >
    <ButtonLink :to="signInUrl" class="gap-2">
      <LogIn class="h-4 w-4" aria-hidden="true" />
      Sign in
    </ButtonLink>
  </StatePanel>
</template>

<script setup>
import { LogIn } from 'lucide-vue-next'

defineProps({
  signInUrl: { type: String, required: true },
})
</script>
