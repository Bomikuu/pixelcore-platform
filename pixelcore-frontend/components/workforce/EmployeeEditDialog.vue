<template>
  <Dialog :open="open" @update:open="setOpen">
    <DialogContent class="max-h-[90dvh] overflow-y-auto sm:max-w-2xl">
      <form class="space-y-6" @submit.prevent="save">
        <DialogHeader>
          <DialogTitle>Edit employee</DialogTitle>
          <DialogDescription>
            Update their profile, work details, and regular schedule.
          </DialogDescription>
        </DialogHeader>

        <fieldset :disabled="saving" class="min-w-0 space-y-6">
          <div class="flex flex-col gap-4 rounded-lg border p-4 sm:flex-row sm:items-center">
            <Avatar class="h-20 w-20 shrink-0 border">
              <AvatarImage v-if="photoPreview" :src="photoPreview" alt="Employee photo preview" class="object-cover" />
              <AvatarFallback class="bg-secondary text-primary">
                <UserRound class="h-8 w-8" aria-hidden="true" />
              </AvatarFallback>
            </Avatar>
            <div class="min-w-0 flex-1 space-y-2">
              <Label for="edit-employee-photo">Profile photo</Label>
              <Input
                :key="photoInputKey"
                id="edit-employee-photo"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                class="h-auto text-xs file:mr-3"
                @change="selectPhoto"
              />
              <p class="text-xs text-muted-foreground">JPG, PNG, or WebP. Up to 5 MB and 4096 pixels per side.</p>
              <Button v-if="photoPreview" class="h-auto gap-2 px-0 py-1" variant="ghost" size="sm" type="button" @click="removePhoto">
                <Trash2 class="h-3.5 w-3.5" aria-hidden="true" />
                Remove photo
              </Button>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div v-for="field in identityFields" :key="field.key" class="space-y-2">
              <Label :for="`edit-employee-${field.key}`">{{ field.label }}</Label>
              <Input
                :id="`edit-employee-${field.key}`"
                v-model="form[field.key]"
                :type="field.type || 'text'"
                :maxlength="field.maxlength"
                :required="field.required || false"
              />
            </div>
          </div>
          <p class="text-xs leading-5 text-muted-foreground">
            Contact email is part of the workforce record. It does not change the employee’s sign-in email.
          </p>

          <div class="space-y-4 border-t pt-5">
            <h3 class="flex items-center gap-2 text-sm font-semibold">
              <CalendarClock class="h-4 w-4 text-primary" aria-hidden="true" />
              Employment and attendance
            </h3>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="space-y-2">
                <Label for="edit-employment-status">Employment status</Label>
                <Select v-model="form.employment_status">
                  <SelectTrigger id="edit-employment-status"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending approval</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-2">
                <Label for="edit-hire-date">Hire date</Label>
                <Input id="edit-hire-date" v-model="form.hired_at" type="date" />
              </div>
              <div v-for="field in scheduleFields" :key="field.key" class="space-y-2">
                <Label :for="`edit-${field.key}`">{{ field.label }}</Label>
                <Input
                  :id="`edit-${field.key}`"
                  v-model="form[field.key]"
                  :type="field.type"
                  :min="field.min"
                  :max="field.max"
                  :required="field.type === 'number'"
                />
              </div>
              <div class="space-y-2 sm:col-span-2">
                <Label for="edit-timezone">Timezone</Label>
                <Input id="edit-timezone" v-model.trim="form.timezone" required />
              </div>
            </div>
            <div class="flex items-center gap-3">
              <Checkbox id="edit-bookable" :checked="form.is_bookable" @update:checked="form.is_bookable = Boolean($event)" />
              <Label for="edit-bookable">Available for service assignments</Label>
            </div>
            <div class="space-y-2">
              <Label for="edit-employee-notes">Internal notes</Label>
              <Textarea id="edit-employee-notes" v-model="form.bio" maxlength="2000" class="min-h-24" />
            </div>
          </div>
        </fieldset>

        <Alert v-if="error" variant="destructive">
          <AlertCircle class="h-4 w-4" aria-hidden="true" />
          <AlertTitle>Changes not saved</AlertTitle>
          <AlertDescription>{{ error }}</AlertDescription>
        </Alert>

        <DialogFooter class="gap-2 border-t pt-4">
          <Button variant="outline" type="button" :disabled="saving" @click="setOpen(false)">Cancel</Button>
          <Button class="gap-2" type="submit" :disabled="saving">
            <Save class="h-4 w-4" aria-hidden="true" />
            {{ saving ? "Saving changes…" : "Save changes" }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { AlertCircle, CalendarClock, Save, Trash2, UserRound } from "lucide-vue-next";
import { toast } from "@/components/ui/toast";

const props = defineProps({
  open: { type: Boolean, default: false },
  employee: { type: Object, required: true },
  businessId: { type: String, required: true },
});
const emit = defineEmits(["update:open", "saved"]);
const { apiFetch } = useApiClient();
const form = reactive({});
const saving = ref(false);
const error = ref("");
const photoFile = shallowRef(null);
const photoPreview = ref("");
const photoRemoved = ref(false);
const photoInputKey = ref(0);
let objectUrl = "";

const identityFields = [
  { key: "display_name", label: "Display name", maxlength: 160, required: true },
  { key: "email", label: "Contact email", type: "email" },
  { key: "job_title", label: "Job title", maxlength: 120 },
  { key: "emergency_contact_name", label: "Emergency contact", maxlength: 160 },
  { key: "emergency_contact_phone", label: "Emergency phone", type: "tel", maxlength: 32 },
];
const scheduleFields = [
  { key: "scheduled_start_time", label: "Shift starts", type: "time" },
  { key: "scheduled_end_time", label: "Shift ends", type: "time" },
  { key: "late_grace_minutes", label: "Arrival grace (minutes)", type: "number", min: 0, max: 120 },
  { key: "consecutive_late_threshold", label: "Flag after late shifts", type: "number", min: 1, max: 30 },
];

watch(() => props.open, (open) => {
  if (!open) return;
  releasePreview();
  const employee = props.employee;
  for (const field of [...identityFields, ...scheduleFields]) {
    form[field.key] = employee[field.key] ?? "";
  }
  Object.assign(form, {
    employment_status: employee.employment_status,
    hired_at: employee.hired_at || "",
    timezone: employee.timezone,
    is_bookable: employee.is_bookable,
    bio: employee.bio || "",
  });
  photoFile.value = null;
  photoRemoved.value = false;
  photoPreview.value = employee.profile_image_url || "";
  photoInputKey.value += 1;
  error.value = "";
});

onBeforeUnmount(releasePreview);

function setOpen(open) {
  if (!saving.value) emit("update:open", open);
}

function releasePreview() {
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = "";
}

function selectPhoto(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
    error.value = "Choose a JPG, PNG, or WebP photo up to 5 MB.";
    event.target.value = "";
    return;
  }
  releasePreview();
  objectUrl = URL.createObjectURL(file);
  photoFile.value = file;
  photoPreview.value = objectUrl;
  photoRemoved.value = false;
  error.value = "";
}

function removePhoto() {
  releasePreview();
  photoFile.value = null;
  photoPreview.value = "";
  photoRemoved.value = true;
  photoInputKey.value += 1;
}

async function save() {
  if (saving.value) return;
  if (Boolean(form.scheduled_start_time) !== Boolean(form.scheduled_end_time)) {
    error.value = "Provide both shift start and end, or clear both fields.";
    return;
  }
  saving.value = true;
  error.value = "";
  try {
    const payload = {
      ...form,
      hired_at: form.hired_at || null,
      scheduled_start_time: form.scheduled_start_time || null,
      scheduled_end_time: form.scheduled_end_time || null,
      late_grace_minutes: Number(form.late_grace_minutes),
      consecutive_late_threshold: Number(form.consecutive_late_threshold),
    };
    let body = payload;
    if (photoFile.value) {
      body = new FormData();
      for (const [key, value] of Object.entries(payload)) {
        body.append(key, value === null ? "" : String(value));
      }
      body.append("profile_image", photoFile.value);
    } else if (photoRemoved.value) {
      payload.profile_image = null;
    }
    const updated = await apiFetch(
      `businesses/${props.businessId}/staff/${props.employee.public_id}/`,
      { method: "PATCH", body },
    );
    emit("saved", updated);
    emit("update:open", false);
    toast({ title: "Employee updated", description: "Profile and work details saved." });
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || "Review the details and try again.";
  } finally {
    saving.value = false;
  }
}
</script>
