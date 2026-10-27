<template>
  <div class="grid gap-8 xl:grid-cols-[minmax(0,1fr)_minmax(20rem,28rem)]">
    <section class="min-w-0 space-y-4">
      <h2 class="text-lg font-semibold">Business connections</h2>
      <SmokeyMascotStatus
        v-if="loading || busy"
        :state="busy ? 'generating' : 'searching'"
        :label="busyLabel || 'Loading AI connections…'"
      />
      <p
        v-if="error || localError"
        role="alert"
        class="text-sm text-destructive"
      >
        {{ localError || error }}
      </p>
      <p v-if="notice" role="status" class="text-sm">{{ notice }}</p>
      <p
        v-if="!loading && !data?.length"
        class="py-8 text-sm text-muted-foreground"
      >
        No connections yet. An owner or administrator can add a provider key.
      </p>
      <article
        v-for="item in data || []"
        :key="item.id"
        class="space-y-4 rounded-xl border bg-card p-5"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 class="font-semibold">{{ item.name }}</h3>
            <p class="mt-1 break-all text-sm text-muted-foreground">
              {{ item.provider }} · {{ item.model }}
            </p>
          </div>
          <Badge variant="secondary">{{ item.status }}</Badge>
        </div>
        <p class="text-xs text-muted-foreground">
          Key ending {{ item.secret_suffix
          }}<span v-if="config?.default_connection_id === item.id">
            · Default connection</span
          >
        </p>
        <div v-if="canEdit" class="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            :disabled="busy"
            @click="check(item)"
            >Check connection</Button
          ><Button
            variant="outline"
            size="sm"
            :disabled="busy"
            @click="catalog(item)"
            >Browse models</Button
          ><Button
            variant="ghost"
            size="sm"
            :disabled="busy"
            @click="edit(item)"
            >Edit</Button
          ><Button
            size="sm"
            :disabled="
              busy ||
              item.status !== 'ready' ||
              config?.default_connection_id === item.id
            "
            @click="makeDefault(item)"
            >Use by default</Button
          ><Button
            variant="ghost"
            size="sm"
            :disabled="busy"
            @click="toDelete = item"
            >Remove</Button
          >
        </div>
      </article>
      <div v-if="models.length" class="space-y-3 border-t pt-4">
        <h3 class="font-semibold">Available model candidates</h3>
        <p class="text-xs text-muted-foreground">
          Select a model to edit its connection. A successful connection check
          confirms structured output access.
        </p>
        <div class="max-h-72 space-y-1 overflow-auto">
          <Button
            v-for="model in models"
            :key="model.id"
            variant="ghost"
            class="h-auto w-full justify-start whitespace-normal break-all text-left"
            @click="
              form.model = model.id;
              permittedText = model.id;
            "
            >{{ model.id }}</Button
          >
        </div>
      </div>
    </section>
    <form
      novalidate
      v-if="canEdit"
      class="self-start space-y-5 rounded-xl border bg-card p-5"
      @submit.prevent="save"
    >
      <h2 class="text-lg font-semibold">
        {{ editingId ? "Edit connection" : "Add connection" }}
      </h2>
      <div class="space-y-2">
        <Label for="connection-name">Connection name</Label
        ><Input
          id="connection-name"
          v-model="form.name"
          maxlength="100"
          required
        />
      </div>
      <div class="space-y-2">
        <Label for="connection-provider">Provider</Label
        ><Select
          :model-value="form.provider"
          :disabled="busy"
          @update:model-value="selectProvider"
          ><SelectTrigger id="connection-provider"
            ><SelectValue /></SelectTrigger
          ><SelectContent
            ><SelectItem
              v-for="provider in providers"
              :key="provider.value"
              :value="provider.value"
              >{{ provider.label }}</SelectItem
            ></SelectContent
          ></Select
        >
      </div>
      <div class="space-y-2">
        <Label for="connection-key">{{
          editingId ? "Replacement API key (optional)" : "Provider API key"
        }}</Label
        ><Input
          id="connection-key"
          v-model="form.secret"
          type="password"
          autocomplete="new-password"
          :required="!editingId"
          maxlength="1000"
        />
        <p class="text-xs leading-5 text-muted-foreground">
          Encrypted on the server. Saved keys are never returned to this
          browser.
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          :disabled="busy || !form.secret.trim()"
          @click="discover"
          >Load provider models</Button
        >
      </div>
      <div class="space-y-2">
        <Label for="connection-model">Model identifier</Label
        ><Input
          id="connection-model"
          v-model="form.model"
          placeholder="Exact provider model ID"
          required
          maxlength="180"
        />
      </div>
      <div class="space-y-2">
        <Label for="permitted-models">Permitted models, one per line</Label
        ><Textarea
          id="permitted-models"
          class="resize-none"
          v-model="permittedText"
          rows="3"
          placeholder="Include the selected model"
        />
      </div>
      <p class="text-xs leading-5 text-muted-foreground">
        Saving creates an untested connection. Running a connection check makes
        a small provider request and can consume tokens.
      </p>
      <div class="flex gap-2">
        <Button type="submit" :disabled="busy">{{
          busy ? "Working…" : "Save connection"
        }}</Button
        ><Button v-if="editingId" type="button" variant="ghost" @click="reset"
          >Cancel edit</Button
        >
      </div>
    </form>
    <Dialog
      :open="Boolean(toDelete)"
      @update:open="
        (value) => {
          if (!value) toDelete = null;
        }
      "
      ><DialogContent
        ><DialogHeader
          ><DialogTitle>Remove this AI connection?</DialogTitle
          ><DialogDescription
            >Reports already saved remain available. Queued requests using this
            connection will stop, and a removed default must be
            replaced.</DialogDescription
          ></DialogHeader
        ><DialogFooter
          ><Button variant="outline" @click="toDelete = null"
            >Keep connection</Button
          ><Button variant="destructive" :disabled="busy" @click="remove"
            >Remove connection</Button
          ></DialogFooter
        ></DialogContent
      ></Dialog
    >
  </div>
</template>
<script setup>
import { validateConnection, canConfigureSmokey } from "~/utils/smokeySettings";
import SmokeyMascotStatus from "./SmokeyMascotStatus.vue";
const { data, error, loading, refresh, request } =
  useSmokeyResource("connections/");
const { config, refresh: refreshConfig } = useSmokeyAssistant();
const canEdit = computed(() => canConfigureSmokey(config.value));
const busy = ref(false),
  localError = ref(""),
  notice = ref(""),
  busyLabel = ref(""),
  editingId = ref(null),
  toDelete = ref(null),
  models = ref([]),
  permittedText = ref("");
const form = reactive({ name: "", provider: "openai", model: "", secret: "" });
const providers = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "gemini", label: "Google Gemini" },
  { value: "openrouter", label: "OpenRouter" },
];
function reset() {
  Object.assign(form, { name: "", provider: "openai", model: "", secret: "" });
  permittedText.value = "";
  editingId.value = null;
  models.value = [];
}
function selectProvider(value) {
  form.provider = value;
  form.model = "";
  permittedText.value = "";
  models.value = [];
}
function edit(item) {
  Object.assign(form, {
    name: item.name,
    provider: item.provider,
    model: item.model,
    secret: "",
  });
  permittedText.value = item.permitted_models.join("\n");
  editingId.value = item.id;
}
async function act(label, task) {
  busy.value = true;
  busyLabel.value = label;
  localError.value = "";
  notice.value = "";
  try {
    await task();
  } catch (issue) {
    localError.value =
      issue?.data?.error?.message ||
      "This action could not complete. Please try again.";
  } finally {
    await Promise.allSettled([refresh(), refreshConfig()]);
    busy.value = false;
    busyLabel.value = "";
  }
}
async function save() {
  const payload = {
    ...form,
    model: form.model.trim(),
    permitted_models: [
      ...new Set(
        permittedText.value
          .split("\n")
          .map((value) => value.trim())
          .filter(Boolean),
      ),
    ],
  };
  if (!payload.secret) delete payload.secret;
  localError.value = validateConnection(payload, Boolean(editingId.value));
  if (localError.value) return;
  await act("Saving your AI connection…", async () => {
    await request(
      editingId.value ? `connections/${editingId.value}/` : "connections/",
      { method: editingId.value ? "PATCH" : "POST", body: payload },
    );
    reset();
    notice.value = "Connection saved. Run a connection check before using it.";
  });
}
const check = (item) =>
  act("Checking your AI connection…", async () => {
    await request(`connections/${item.id}/check/`, { method: "POST" });
    notice.value = "Connection verified. It is ready to use.";
  });
const catalog = (item) =>
  act("Loading the provider’s model catalog…", async () => {
    edit(item);
    models.value = (await request(`connections/${item.id}/models/`)).models;
  });
const discover = () =>
  act("Loading the provider’s model catalog…", async () => {
    models.value = (
      await request("models/", {
        method: "POST",
        body: { provider: form.provider, secret: form.secret },
      })
    ).models;
    notice.value =
      "Choose a model from the catalog, then save your connection.";
  });
const makeDefault = (item) =>
  act("Saving your default connection…", () =>
    request("settings/", {
      method: "PATCH",
      body: { default_connection_id: item.id },
    }),
  );
const remove = () =>
  act("Removing your connection…", async () => {
    await request(`connections/${toDelete.value.id}/`, { method: "DELETE" });
    toDelete.value = null;
  });
watch(
  () => useBusinessStore().activeBusiness?.public_id,
  () => {
    reset();
    localError.value = "";
    notice.value = "";
    toDelete.value = null;
  },
);
</script>
