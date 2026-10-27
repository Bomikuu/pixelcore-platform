<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button
        ref="trigger"
        type="button"
        variant="ghost"
        size="icon"
        class="h-9 w-9 shrink-0"
        :disabled="!business.activeBusiness?.public_id"
        aria-label="Search this business"
        title="Search this business"
      >
        <Search class="h-[1.125rem] w-[1.125rem]" aria-hidden="true" />
      </Button>
    </DialogTrigger>
    <DialogContent
      class="flex max-h-[calc(100dvh-2rem)] w-[calc(100vw-2rem)] max-w-2xl flex-col gap-0 overflow-hidden bg-card p-0 transition-none"
      :style="theme"
      @open-auto-focus="focusSearch"
    >
      <DialogHeader class="shrink-0 px-5 pb-4 pt-5 pr-12 text-left">
        <DialogTitle>Search</DialogTitle>
        <DialogDescription class="break-words">
          Find products, promotions, categories, and employees in
          {{ business.activeBusiness?.display_name || "your business" }}.
        </DialogDescription>
      </DialogHeader>
      <Command
        v-model:search-term="search"
        :filter-function="keepFiltered"
        :reset-search-term-on-blur="false"
        class="min-h-0 flex-1 rounded-none bg-card"
        @keydown.capture="guardComposition"
      >
        <div class="workspace-search-field relative shrink-0 border-t">
          <CommandInput
            ref="searchField"
            class="h-12 rounded-none pr-12 focus-visible:ring-0 focus-visible:ring-offset-0"
            aria-label="Search business records"
            placeholder="Search by name or code…"
            @compositionstart="composing = true"
            @compositionend="composing = false"
          />
          <Button
            v-if="search"
            type="button"
            variant="ghost"
            size="icon"
            class="absolute right-2 top-2 h-8 w-8"
            aria-label="Clear search"
            @click="clearSearch"
            ><X class="h-4 w-4" aria-hidden="true"
          /></Button>
        </div>
        <WorkspaceRecordSearch
          ref="recordSearch"
          :search="search"
          :active="open"
          :composing="composing"
          @choose="chooseRecord"
          @busy="searchBusy = $event"
        />
      </Command>
      <div
        class="flex shrink-0 flex-wrap items-center justify-between gap-2 border-t bg-muted/20 px-5 py-3 text-[0.6875rem] text-muted-foreground"
      >
        <span>↑ ↓ to browse · Enter to open</span><span>Esc to close</span>
      </div>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { Search, X } from "lucide-vue-next";
import { workspaceCreateRole } from "~/utils/workspaceQuickActions";
import WorkspaceRecordSearch from "~/components/workspace/WorkspaceRecordSearch.vue";
import { toast } from "~/components/ui/toast";

const business = useBusinessStore();
const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const open = ref(false);
const search = ref("");
const composing = ref(false);
const searchBusy = ref(false);
const recordSearch = ref(null);
const searchField = ref(null);
const trigger = ref(null);
const keepFiltered = (values) => values;
const { style: theme } = useWorkspaceTheme();

function focusSearch(event) {
  event?.preventDefault();
  nextTick(() => searchField.value?.$el?.querySelector("input")?.focus());
}
function clearSearch() {
  search.value = "";
  focusSearch();
}
function guardComposition(event) {
  if (event.target?.closest?.("button")) return;
  if (
    event.key === "Enter" &&
    (event.isComposing || composing.value || searchBusy.value)
  ) {
    event.preventDefault();
    event.stopPropagation();
    if (!event.isComposing && !composing.value)
      recordSearch.value?.submitSearch();
  }
}
watch(open, (value) => {
  if (value) {
    search.value = "";
    composing.value = false;
  }
});
watch(
  () => [
    route.fullPath,
    business.activeBusiness?.public_id,
    workspaceCreateRole(auth.user, business.activeBusiness),
    JSON.stringify(business.activeBusiness?.enabled_modules || []),
    auth.user?.id,
  ],
  () => {
    open.value = false;
  },
);
async function chooseRecord(record) {
  open.value = false;
  try {
    await router.push(record.to);
  } catch {
    toast({
      title: "Could not open the record",
      description: "Try again from Search.",
      variant: "destructive",
    });
  }
}
</script>

<style scoped>
.workspace-search-field::after {
  content: "";
  position: absolute;
  inset-inline: 0;
  bottom: 0;
  height: 2px;
  background: hsl(var(--primary));
  pointer-events: none;
  transform: scaleX(0);
  transition: transform 150ms ease;
}
.workspace-search-field:focus-within::after {
  transform: scaleX(1);
}
@media (prefers-reduced-motion: reduce) {
  .workspace-search-field::after {
    transition: none;
  }
}
</style>
