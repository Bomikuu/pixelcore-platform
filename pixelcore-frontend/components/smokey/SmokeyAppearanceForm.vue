<template>
  <div class="grid gap-8 lg:grid-cols-[minmax(0,1fr)_22rem]">
    <form novalidate class="max-w-2xl space-y-6" @submit.prevent="save">
      <p v-if="error" role="alert" class="text-sm text-destructive">
        {{ error }}
      </p>
      <p v-if="notice" role="status" class="text-sm">{{ notice }}</p>
      <div class="space-y-2">
        <Label for="mascot-mode">Mascot</Label
        ><Select v-model="form.mode" :disabled="!canEdit"
          ><SelectTrigger id="mascot-mode"><SelectValue /></SelectTrigger
          ><SelectContent
            ><SelectItem value="smokey">Smokey</SelectItem
            ><SelectItem value="custom">Custom mascot</SelectItem
            ><SelectItem value="standard"
              >Standard chat icon</SelectItem
            ></SelectContent
          ></Select
        >
      </div>
      <div class="space-y-2">
        <Label for="assistant-presentation">Open assistant as</Label
        ><Select v-model="presentation" :disabled="!canEdit"
          ><SelectTrigger id="assistant-presentation"
            ><SelectValue /></SelectTrigger
          ><SelectContent
            ><SelectItem value="drawer">Right drawer</SelectItem
            ><SelectItem value="modal">Modal</SelectItem></SelectContent
          ></Select
        >
        <p class="text-xs text-muted-foreground">
          Both use the same conversation. On small screens, Smokey fills the
          available height.
        </p>
      </div>
      <template v-if="form.mode === 'custom'"
        ><div class="space-y-2">
          <Label for="mascot-file">PNG or WebP mascot</Label
          ><Input
            id="mascot-file"
            type="file"
            accept="image/png,image/webp"
            :disabled="!canEdit || busy"
            @change="file = $event.target.files?.[0] || null"
          />
          <p class="text-xs text-muted-foreground">
            Up to 5 MB and 4096 pixels. Saved assets are served through business
            authorization.
          </p>
        </div>
        <div class="space-y-2">
          <Label for="mascot-type">Image type</Label
          ><Select v-model="form.asset_type" :disabled="!canEdit"
            ><SelectTrigger id="mascot-type"><SelectValue /></SelectTrigger
            ><SelectContent
              ><SelectItem value="static">Static image</SelectItem
              ><SelectItem value="sprite"
                >Sprite sheet</SelectItem
              ></SelectContent
            ></Select
          >
        </div>
        <div v-if="form.asset_type === 'sprite'" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="sprite-columns">Columns</Label
              ><Input
                id="sprite-columns"
                v-model.number="form.columns"
                type="number"
                min="1"
                max="32"
                :disabled="!canEdit"
              />
            </div>
            <div class="space-y-2">
              <Label for="sprite-rows">Rows</Label
              ><Input
                id="sprite-rows"
                v-model.number="form.rows"
                type="number"
                min="1"
                max="32"
                :disabled="!canEdit"
              />
            </div>
          </div>
          <p class="text-xs text-muted-foreground">
            Frame coordinates start at zero. Unspecified states use the idle
            frame.
          </p>
          <div
            v-for="state in frameStates"
            :key="state"
            class="grid grid-cols-[minmax(0,1fr)_5rem_5rem] items-end gap-3"
          >
            <span class="pb-2 text-sm capitalize">{{ state }}</span>
            <div>
              <Label :for="`frame-${state}-x`" class="text-xs">Column</Label
              ><Input
                :id="`frame-${state}-x`"
                v-model.number="frames[state][0]"
                type="number"
                min="0"
                :max="form.columns - 1"
                :disabled="!canEdit"
              />
            </div>
            <div>
              <Label :for="`frame-${state}-y`" class="text-xs">Row</Label
              ><Input
                :id="`frame-${state}-y`"
                v-model.number="frames[state][1]"
                type="number"
                min="0"
                :max="form.rows - 1"
                :disabled="!canEdit"
              />
            </div>
          </div></div></template
      ><Button v-if="canEdit" type="submit" :disabled="busy">{{
        busy ? "Saving appearance…" : "Save appearance"
      }}</Button>
      <p v-else class="text-sm text-muted-foreground">
        Only owners and administrators can change appearance.
      </p>
    </form>
    <aside class="self-start rounded-xl border bg-card p-5">
      <h2 class="mb-5 font-semibold">Saved mascot preview</h2>
      <SmokeyMascotStatus :state="previewState" />
      <div class="mt-5 space-y-2">
        <Label for="preview-state">Preview feedback</Label
        ><Select id="preview-state" v-model="previewState"
          ><SelectTrigger aria-label="Preview mascot state"
            ><SelectValue /></SelectTrigger
          ><SelectContent
            ><SelectItem
              v-for="state in previewStates"
              :key="state"
              :value="state"
              >{{ state }}</SelectItem
            ></SelectContent
          ></Select
        >
      </div>
      <p class="mt-4 text-xs leading-6 text-muted-foreground">
        Status text stays visible with a static mascot or reduced motion.
        Previews are demonstrations; live progress follows actual server work.
      </p>
    </aside>
  </div>
</template>
<script setup>
import { canConfigureSmokey } from "~/utils/smokeySettings";
import { createSmokeyClient } from "~/utils/smokeyAssistant";
import SmokeyMascotStatus from "./SmokeyMascotStatus.vue";
const { config, refresh } = useSmokeyAssistant();
const { apiFetch } = useApiClient(),
  business = useBusinessStore();
const canEdit = computed(() => canConfigureSmokey(config.value));
const form = reactive({
    mode: "smokey",
    asset_type: "static",
    columns: 1,
    rows: 1,
  }),
  presentation = ref("drawer"),
  file = ref(null),
  busy = ref(false),
  error = ref(""),
  notice = ref(""),
  previewState = ref("idle");
const frameStates = [
  "idle",
  "searching",
  "generating",
  "success",
  "empty",
  "error",
  "cancelled",
];
const previewStates = [
  "idle",
  "searching",
  "generating",
  "succeeded",
  "empty",
  "failed",
  "cancelled",
];
const frames = reactive(
  Object.fromEntries(frameStates.map((state) => [state, [0, 0]])),
);
watch(
  config,
  (value) => {
    Object.assign(
      form,
      { mode: "smokey", asset_type: "static", columns: 1, rows: 1 },
      value?.mascot || {},
    );
    presentation.value = value?.presentation || "drawer";
    for (const state of frameStates)
      frames[state] = [...(value?.mascot?.frames?.[state] || [0, 0])];
  },
  { immediate: true },
);
async function save() {
  if (
    form.mode === "custom" &&
    !file.value &&
    !config.value?.has_mascot_asset
  ) {
    error.value = "Upload a mascot image before selecting Custom mascot.";
    return;
  }
  if (
    form.asset_type === "sprite" &&
    (!Number.isInteger(form.columns) ||
      !Number.isInteger(form.rows) ||
      form.columns < 1 ||
      form.columns > 32 ||
      form.rows < 1 ||
      form.rows > 32)
  ) {
    error.value = "Use whole sprite dimensions from 1 to 32.";
    return;
  }
  const id = business.activeBusiness?.public_id;
  const client = createSmokeyClient(apiFetch, id);
  busy.value = true;
  error.value = "";
  notice.value = "";
  try {
    if (file.value) {
      const body = new FormData();
      body.append("file", file.value);
      await client.request("asset/", { method: "POST", body });
    }
    await client.request("settings/", {
      method: "PATCH",
      body: { presentation: presentation.value, mascot: { ...form, frames } },
    });
    if (id === business.activeBusiness?.public_id) {
      file.value = null;
      await refresh();
      notice.value = "Appearance saved.";
    }
  } catch (issue) {
    if (id === business.activeBusiness?.public_id)
      error.value = issue?.data?.error?.message || "Could not save appearance.";
  } finally {
    busy.value = false;
  }
}
watch(
  () => business.activeBusiness?.public_id,
  () => {
    file.value = null;
    error.value = "";
    notice.value = "";
  },
);
</script>
