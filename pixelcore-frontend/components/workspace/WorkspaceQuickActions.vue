<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child>
      <Button
        ref="trigger"
        type="button"
        size="sm"
        class="h-9 shrink-0 gap-2 px-2.5 sm:px-3"
        :disabled="!business.activeBusiness?.public_id"
        aria-label="Open quick actions"
      >
        <Plus class="h-4 w-4" aria-hidden="true" />
        <span class="hidden sm:inline">Quick actions</span>
      </Button>
    </DialogTrigger>
    <DialogContent
      class="flex max-h-[calc(100dvh-2rem)] w-[calc(100vw-2rem)] max-w-2xl flex-col gap-0 overflow-hidden bg-card p-0 transition-none"
      :style="theme"
      @close-auto-focus="afterPaletteClose"
    >
      <DialogHeader class="shrink-0 px-5 pb-4 pt-5 pr-12 text-left">
        <DialogTitle>Quick actions</DialogTitle>
        <DialogDescription class="break-words"
          >Create something for
          {{
            business.activeBusiness?.display_name || "your business"
          }}.</DialogDescription
        >
      </DialogHeader>
      <div class="min-h-0 overflow-y-auto px-4 pb-4">
        <div
          v-if="preparing"
          class="flex items-center gap-3 border-b bg-muted/30 px-5 py-3 text-sm"
          role="status"
        >
          <LoaderCircle
            class="h-4 w-4 animate-spin motion-reduce:animate-none"
            aria-hidden="true"
          />Preparing {{ preparing.label.toLowerCase() }}…
        </div>
        <Alert v-if="error" variant="destructive" class="m-3 w-auto"
          ><AlertTitle>Could not open this action</AlertTitle
          ><AlertDescription
            >{{ error }} Choose it again to retry.</AlertDescription
          ></Alert
        >
        <p
          v-if="!available.length"
          class="px-3 py-4 text-xs leading-5 text-muted-foreground"
        >
          Creation shortcuts follow your role and enabled modules. Ask an owner
          or administrator if you need access.
        </p>
        <section
          v-for="group in groups"
          :key="group.label"
          :aria-label="group.label"
          class="pt-3"
        >
          <h3 class="mb-2 px-1 text-xs font-semibold text-muted-foreground">
            {{ group.label }}
          </h3>
          <div class="grid gap-2 sm:grid-cols-2">
            <Button
              type="button"
              variant="outline"
              v-for="action in group.actions"
              :key="action.id"
              :disabled="Boolean(preparing)"
              class="group h-auto min-h-20 w-full justify-start gap-3 whitespace-normal rounded-lg bg-card px-3 py-3 text-left transition-colors duration-200 hover:border-primary/40 hover:bg-secondary/60 focus-visible:border-primary/50 motion-reduce:transition-none"
              @click="chooseAction(action)"
            >
              <span
                class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-secondary text-primary"
                ><component
                  :is="icons[action.icon]"
                  class="h-[1.125rem] w-[1.125rem]"
                  aria-hidden="true"
              /></span>
              <span class="min-w-0 flex-1"
                ><strong class="block text-sm font-semibold">{{
                  action.label
                }}</strong
                ><span
                  class="mt-1 block text-xs leading-5 text-muted-foreground"
                  >{{ action.description }}</span
                ></span
              >
              <ArrowUpRight
                v-if="action.to"
                class="h-3.5 w-3.5 shrink-0 text-muted-foreground"
                aria-hidden="true"
              /><ChevronRight
                v-else
                class="h-3.5 w-3.5 shrink-0 text-muted-foreground"
                aria-hidden="true"
              />
            </Button>
          </div>
        </section>
      </div>
      <div
        class="flex shrink-0 flex-wrap items-center justify-between gap-2 border-t bg-muted/20 px-5 py-3 text-[0.6875rem] text-muted-foreground"
      >
        <span>Tab to browse · Enter to open</span><span>Esc to close</span>
      </div>
    </DialogContent>
  </Dialog>
  <OperationsCreateDialog
    v-if="operation"
    :key="`${operation.businessId}-${operation.action.id}`"
    v-model:open="operationOpen"
    :view="operation.action.resource"
    :business-id="operation.businessId"
    v-bind="operation.references"
    @created="operation.onCreated"
    @closed="restoreTriggerFocus"
  />
</template>

<script setup>
import {
  ArrowUpRight,
  ChevronRight,
  ClipboardList,
  FileText,
  LoaderCircle,
  PackagePlus,
  Plus,
  ReceiptText,
  ShoppingCart,
  Tags,
  Truck,
  UserPlus,
} from "lucide-vue-next";
import {
  availableWorkspaceActions,
  loadQuickActionReferences,
  workspaceCreateRole,
} from "~/utils/workspaceQuickActions";
import OperationsCreateDialog from "~/components/operations/OperationsCreateDialog.vue";
import { toast } from "~/components/ui/toast";

const business = useBusinessStore();
const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const { apiFetch } = useApiClient();
const open = ref(false);
const trigger = ref(null);
const error = ref("");
const preparing = ref(null);
const operation = ref(null);
const operationOpen = ref(false);
let pendingOperation = null;
let controller;
let version = 0;
const icons = {
  ClipboardList,
  FileText,
  PackagePlus,
  ReceiptText,
  ShoppingCart,
  Tags,
  Truck,
  UserPlus,
};
const { style: theme } = useWorkspaceTheme();
const available = computed(() =>
  availableWorkspaceActions(auth.user, business.activeBusiness),
);
const groups = computed(() =>
  ["Commerce", "Operations", "Workforce"]
    .map((label) => ({
      label,
      actions: available.value.filter((action) => action.group === label),
    }))
    .filter((group) => group.actions.length),
);
function cancelPreparation() {
  version += 1;
  controller?.abort();
  preparing.value = null;
  pendingOperation = null;
}
watch(open, (value) => {
  if (value) {
    error.value = "";
  } else if (preparing.value) cancelPreparation();
});
watch(
  () => [
    business.activeBusiness?.public_id,
    workspaceCreateRole(auth.user, business.activeBusiness),
    JSON.stringify(business.activeBusiness?.enabled_modules || []),
    auth.user?.id,
  ],
  () => {
    cancelPreparation();
    open.value = false;
    operationOpen.value = false;
  },
);
watch(
  () => route.fullPath,
  () => {
    cancelPreparation();
    open.value = false;
    operationOpen.value = false;
  },
);
onBeforeUnmount(cancelPreparation);

async function chooseAction(action) {
  if (preparing.value || !available.value.some((item) => item.id === action.id))
    return;
  error.value = "";
  if (action.to) {
    open.value = false;
    try {
      await router.push(action.to);
    } catch {
      toast({
        title: "Could not open the create page",
        description: "Try again from Quick actions.",
        variant: "destructive",
      });
    }
    return;
  }
  const businessId = business.activeBusiness.public_id;
  const attempt = ++version;
  controller?.abort();
  controller = new AbortController();
  preparing.value = action;
  try {
    const references = await loadQuickActionReferences(
      apiFetch,
      businessId,
      action.resource,
      controller.signal,
    );
    if (
      attempt !== version ||
      !open.value ||
      business.activeBusiness?.public_id !== businessId
    )
      return;
    pendingOperation = {
      businessId,
      businessName: business.activeBusiness.display_name,
      action,
      references,
    };
    preparing.value = null;
    open.value = false;
  } catch (requestError) {
    if (attempt === version && open.value) {
      controller?.abort();
      error.value =
        requestError?.data?.error?.message ||
        "The form’s choices could not be loaded.";
    }
  } finally {
    if (attempt === version) preparing.value = null;
  }
}
function afterPaletteClose(event) {
  if (!pendingOperation) return;
  event.preventDefault();
  const snapshot = pendingOperation;
  operation.value = {
    ...snapshot,
    onCreated: (record) => onCreated(record, snapshot),
  };
  pendingOperation = null;
  operationOpen.value = true;
}
function restoreTriggerFocus(event) {
  event.preventDefault();
  trigger.value?.$el?.focus();
}
function onCreated(record, created) {
  const recordLabel = created.action.label.replace(/^(Add|Create|Record) /, "");
  if (business.activeBusiness?.public_id === created.businessId)
    toast({
      title: `${recordLabel.charAt(0).toUpperCase()}${recordLabel.slice(1)} saved`,
      description: `Added to ${created.businessName}.`,
    });
  window.dispatchEvent(
    new CustomEvent("pixelcore:operations-created", {
      detail: {
        businessId: created.businessId,
        resource: created.action.resource,
        publicId: record?.public_id,
      },
    }),
  );
}
</script>
