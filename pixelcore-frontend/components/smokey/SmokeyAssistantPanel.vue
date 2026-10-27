<template>
  <template v-if="enabled && config">
    <Button
      variant="ghost"
      size="sm"
      class="gap-2"
      aria-label="Open Smokey assistant"
      @click="opened = true"
      ><MessageCircle class="h-4 w-4" /><span class="hidden sm:inline"
        >Ask Smokey</span
      ></Button
    >
    <Sheet v-if="config.presentation !== 'modal'" v-model:open="opened"
      ><SheetContent
        side="right"
        class="flex h-dvh w-full flex-col gap-5 sm:max-w-lg"
        ><SheetHeader
          ><SheetTitle>Smokey</SheetTitle
          ><SheetDescription
            >Your business reporting assistant</SheetDescription
          ></SheetHeader
        ><SmokeyConversation /></SheetContent
    ></Sheet>
    <Dialog v-else v-model:open="opened"
      ><DialogContent
        class="flex h-dvh max-h-dvh w-full max-w-none flex-col rounded-none sm:h-[min(48rem,90dvh)] sm:max-w-2xl sm:rounded-xl"
        ><DialogHeader
          ><DialogTitle>Smokey</DialogTitle
          ><DialogDescription
            >Your business reporting assistant</DialogDescription
          ></DialogHeader
        ><SmokeyConversation /></DialogContent
    ></Dialog>
  </template>
</template>
<script setup>
import { MessageCircle } from "lucide-vue-next";
import SmokeyConversation from "./SmokeyConversation.vue";
const { config, opened } = useSmokeyAssistant();
const business = useBusinessStore();
const route = useRoute();
const enabled = computed(
  () =>
    business.activeBusiness?.enabled_modules?.includes("smokey") &&
    route.path !== "/workspace/smokey/assistant",
);
</script>
