<template>
  <Button
    v-if="status.ready && status.available"
    data-smokey-chat-toggle
    type="button"
    variant="ghost"
    size="sm"
    :aria-label="status.opened ? 'Close Smokey chat' : 'Open Smokey chat'"
    :aria-expanded="status.opened"
    aria-controls="smokey-chat-drawer"
    @click="toggleAssistant($event.currentTarget)"
  >
    <MessageCircle class="h-4 w-4" /><span class="hidden sm:inline"
      >Ask Smokey</span
    >
  </Button>
</template>
<script setup>
import { MessageCircle } from "lucide-vue-next";
import { Button } from "@/components/ui/button";
const { status, toggleAssistant } = useSmokeyAssistant();
</script>
