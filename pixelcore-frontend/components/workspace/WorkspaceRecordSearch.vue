<template>
  <div
    v-if="scopes.length"
    class="flex shrink-0 flex-wrap gap-1 border-b px-4 py-3"
    role="group"
    aria-label="Search categories"
  >
    <Button
      v-for="kind in [{ id: 'all', label: 'All' }, ...scopes]"
      :key="kind.id"
      type="button"
      :variant="scope === kind.id ? 'secondary' : 'ghost'"
      size="sm"
      class="h-8 px-2.5 text-xs"
      :class="
        scope === kind.id ? 'font-bold text-primary' : 'text-muted-foreground'
      "
      :aria-pressed="scope === kind.id"
      :disabled="!active"
      @click="scope = kind.id"
      >{{ kind.label }}</Button
    >
  </div>
  <CommandList
    ref="resultList"
    :aria-busy="loading"
    class="max-h-[min(55dvh,28rem)] min-h-0 px-3 pb-3"
  >
    <div class="border-b pb-3">
      <div class="flex items-center justify-between gap-3 px-3 pb-1 pt-2">
        <h3 class="text-xs font-semibold text-muted-foreground">
          {{
            search.trim() ? "Search results" : "Suggestions · recently updated"
          }}
        </h3>
        <span
          v-if="!loading && count"
          class="text-xs text-muted-foreground"
          role="status"
        >
          {{ count }} {{ count === 1 ? "result" : "results" }}
        </span>
      </div>
      <div
        v-if="loading"
        class="flex items-center gap-2 px-3 py-6 text-sm text-muted-foreground"
        role="status"
      >
        <LoaderCircle
          class="h-4 w-4 animate-spin motion-reduce:animate-none"
          aria-hidden="true"
        />
        {{
          search.trim() ? "Searching this business…" : "Loading suggestions…"
        }}
      </div>
      <div v-else-if="error" class="space-y-2 px-3 py-4" role="alert">
        <p class="text-sm font-medium">Search unavailable</p>
        <p class="text-xs leading-5 text-muted-foreground">{{ error }}</p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          :disabled="!active"
          @click="load"
          >Try again</Button
        >
      </div>
      <div
        v-else-if="!scopes.length"
        class="px-3 py-4 text-sm text-muted-foreground"
      >
        Search is unavailable for your role or this business’s enabled modules.
      </div>
      <div v-else-if="!count" class="px-3 py-5" role="status">
        <p class="text-sm font-semibold">
          {{ search.trim() ? "No matching records" : "No suggestions yet" }}
        </p>
        <p class="mt-1 text-xs leading-5 text-muted-foreground">
          {{
            search.trim()
              ? "Try a name, product SKU, barcode, promotion code, or employee code."
              : "Records will appear here after they are added to this business."
          }}
        </p>
      </div>
      <template v-else>
        <CommandGroup
          v-for="group in visibleGroups"
          :key="group.id"
          :heading="group.label"
          class="pt-2"
        >
          <CommandItem
            v-for="record in group.items"
            :key="record.id"
            :value="record.id"
            :disabled="!active"
            class="min-h-14 cursor-pointer gap-3 rounded-md px-2 py-2.5 hover:bg-secondary/60 data-[highlighted]:bg-secondary data-[highlighted]:text-foreground"
            @select="emit('choose', record)"
          >
            <Avatar
              :shape="group.id === 'employees' ? 'circle' : 'square'"
              class="h-12 w-12 shrink-0"
              aria-hidden="true"
            >
              <AvatarImage
                v-if="record.image_url"
                :key="record.image_url"
                :src="record.image_url"
                alt=""
              />
              <AvatarFallback
                class="bg-secondary text-primary"
                :class="
                  group.id === 'employees' ? 'rounded-full' : 'rounded-md'
                "
              >
                <span
                  v-if="group.id === 'employees'"
                  class="text-xs font-bold"
                  >{{ initials(record.name) }}</span
                >
                <component v-else :is="icons[group.icon]" class="h-5 w-5" />
              </AvatarFallback>
            </Avatar>
            <span class="min-w-0 flex-1">
              <span class="block break-words text-sm font-semibold">{{
                record.name
              }}</span>
              <span
                class="mt-0.5 block break-words text-xs leading-4 text-muted-foreground"
              >
                {{ record.detail
                }}<span v-if="record.status" class="capitalize">
                  · {{ record.status }}</span
                >
              </span>
            </span>
            <ArrowUpRight
              class="h-3.5 w-3.5 shrink-0 text-muted-foreground"
              aria-hidden="true"
            />
          </CommandItem>
        </CommandGroup>
        <p class="px-3 pt-2 text-[0.6875rem] text-muted-foreground">
          Up to {{ search.trim() ? "5 matches" : "3 suggestions" }} per
          category.
        </p>
      </template>
    </div>
  </CommandList>
</template>

<script setup>
import {
  ArrowUpRight,
  LoaderCircle,
  Package,
  Shapes,
  Tags,
  Users,
} from "lucide-vue-next";
import {
  workspaceRecordGroups,
  workspaceSearchScopes,
} from "~/utils/workspaceSearch";

const props = defineProps({
  search: { type: String, default: "" },
  active: { type: Boolean, default: true },
  composing: { type: Boolean, default: false },
});
const emit = defineEmits(["choose", "busy"]);
const business = useBusinessStore();
const auth = useAuthStore();
const { apiFetch } = useApiClient();
const icons = { Package, Shapes, Tags, Users };
const initials = (name) =>
  String(name || "")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
const scopes = computed(() =>
  workspaceSearchScopes(auth.user, business.activeBusiness),
);
const scope = ref("all");
const resultList = ref(null);
const groups = ref([]);
const loading = ref(false);
const error = ref("");
const visibleGroups = computed(() =>
  groups.value.filter((group) => group.items.length),
);
const count = computed(() =>
  groups.value.reduce((sum, group) => sum + group.items.length, 0),
);
let timer;
let controller;
let version = 0;

function cancel() {
  clearTimeout(timer);
  timer = undefined;
  controller?.abort();
  version += 1;
}
function submitSearch() {
  if (timer) load();
}
defineExpose({ submitSearch });
watch(loading, (busy) => emit("busy", busy), { immediate: true });
async function load() {
  cancel();
  groups.value = [];
  error.value = "";
  if (!props.active || props.composing || !scopes.value.length) {
    loading.value = false;
    return;
  }
  if (props.search.length > 120) {
    loading.value = false;
    error.value = "Use 120 characters or fewer.";
    return;
  }
  const request = version;
  const businessId = business.activeBusiness.public_id;
  controller = new AbortController();
  loading.value = true;
  try {
    const response = await apiFetch(
      `businesses/${businessId}/workspace-search/`,
      {
        query: { search: props.search.trim(), scope: scope.value },
        signal: controller.signal,
      },
    );
    if (request !== version) return;
    groups.value = workspaceRecordGroups(response, scopes.value);
  } catch (exception) {
    if (request === version)
      error.value =
        exception?.data?.error?.message ||
        "Records could not be loaded. Try again.";
  } finally {
    if (request === version) loading.value = false;
  }
}
watch(
  () => [
    props.search,
    props.active,
    props.composing,
    scope.value,
    business.activeBusiness?.public_id,
    JSON.stringify(scopes.value),
  ],
  () => {
    cancel();
    nextTick(() => {
      if (resultList.value?.$el) resultList.value.$el.scrollTop = 0;
    });
    groups.value = [];
    error.value = "";
    loading.value = props.active && scopes.value.length > 0;
    if (!props.active || props.composing) {
      loading.value = false;
      return;
    }
    if (!scopes.value.some((kind) => kind.id === scope.value))
      scope.value = "all";
    if (!props.search.trim()) load();
    else timer = setTimeout(load, 300);
  },
  { immediate: true },
);
onBeforeUnmount(cancel);
</script>
