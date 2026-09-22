<template>
  <section class="workspace-page space-y-5">
    <PageHeader
      title="Add an employee"
      description="Create the complete workforce profile now, or let the employee finish it from a secure invitation."
    >
      <template #actions>
        <Button class="gap-2" variant="outline" type="button" @click="inviteOpen = true">
          <MailPlus class="h-4 w-4 shrink-0" aria-hidden="true" />
          Send email invite
        </Button>
        <ButtonLink variant="outline" to="/workspace/operate/workforce">
          <ArrowLeft class="h-4 w-4" aria-hidden="true" />
          Back to workforce
        </ButtonLink>
      </template>
    </PageHeader>

    <form
      class="grid min-w-0 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]"
      @submit.prevent="submitManual"
    >
      <div class="min-w-0 space-y-5">
        <Card>
          <CardHeader>
            <div class="flex items-start gap-3">
              <div class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-secondary text-primary">
                <UserRound class="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle>Employee identity</CardTitle>
                <CardDescription>
                  Add the workforce details you already know. The employee
                  will still receive a link to create their login.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent class="grid gap-4 sm:grid-cols-2">
            <div class="sm:col-span-2">
              <Label for="employee-name">Display name</Label>
              <Input
                id="employee-name"
                v-model.trim="manualForm.display_name"
                class="mt-2"
                maxlength="160"
                autocomplete="name"
                required
              />
            </div>
            <div>
              <Label for="employee-email">Work email</Label>
              <Input
                id="employee-email"
                v-model.trim="manualForm.email"
                class="mt-2"
                type="email"
                autocomplete="email"
                required
              />
            </div>
            <div>
              <Label for="employee-title">Job title</Label>
              <Input
                id="employee-title"
                v-model.trim="manualForm.job_title"
                class="mt-2"
                maxlength="120"
                placeholder="e.g. Store associate"
              />
            </div>
            <div>
              <Label for="employee-role">Workspace access</Label>
              <NativeSelect id="employee-role" v-model="manualForm.role" class="mt-2">
                <option value="staff">Staff</option>
                <option value="manager">Manager</option>
                <option value="admin">Administrator</option>
              </NativeSelect>
            </div>
            <div>
              <Label for="employee-hired">Hire date</Label>
              <Input id="employee-hired" v-model="manualForm.hired_at" class="mt-2" type="date" />
            </div>
            <div>
              <Label for="emergency-name">Emergency contact</Label>
              <Input
                id="emergency-name"
                v-model.trim="manualForm.emergency_contact_name"
                class="mt-2"
                autocomplete="name"
              />
            </div>
            <div>
              <Label for="emergency-phone">Emergency phone</Label>
              <Input
                id="emergency-phone"
                v-model.trim="manualForm.emergency_contact_phone"
                class="mt-2"
                type="tel"
                autocomplete="tel"
              />
            </div>
            <div class="sm:col-span-2">
              <Label for="employee-bio">Internal notes</Label>
              <Textarea
                id="employee-bio"
                v-model.trim="manualForm.bio"
                class="mt-2 min-h-28"
                maxlength="2000"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div class="flex items-start gap-3">
              <div class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-secondary text-primary">
                <CalendarClock class="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle>Schedule and attendance</CardTitle>
                <CardDescription>
                  Set the defaults used for attendance and lateness tracking.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent class="grid gap-4 sm:grid-cols-2">
            <div>
              <Label for="employee-start">Scheduled start</Label>
              <Input
                id="employee-start"
                v-model="manualForm.scheduled_start_time"
                class="mt-2"
                type="time"
              />
            </div>
            <div>
              <Label for="employee-end">Scheduled end</Label>
              <Input id="employee-end" v-model="manualForm.scheduled_end_time" class="mt-2" type="time" />
            </div>
            <div>
              <Label for="late-grace">Arrival grace</Label>
              <Input
                id="late-grace"
                v-model.number="manualForm.late_grace_minutes"
                class="mt-2"
                type="number"
                min="0"
                max="120"
              />
            </div>
            <div>
              <Label for="late-threshold">Flag after late shifts</Label>
              <Input
                id="late-threshold"
                v-model.number="manualForm.consecutive_late_threshold"
                class="mt-2"
                type="number"
                min="1"
                max="30"
              />
            </div>
            <div class="sm:col-span-2">
              <Label for="employee-timezone">Timezone</Label>
              <Input id="employee-timezone" v-model.trim="manualForm.timezone" class="mt-2" required />
            </div>
            <Label class="sm:col-span-2 flex items-start gap-3 rounded-lg border p-4">
              <NativeCheckbox v-model="manualForm.is_bookable" class="mt-0.5" />
              <span>
                <strong class="block text-sm">Bookable employee</strong>
                <span class="mt-1 block text-xs leading-5 text-muted-foreground">
                  Allow assignment to services and customer bookings.
                </span>
              </span>
            </Label>
          </CardContent>
        </Card>
      </div>

      <aside class="min-w-0 space-y-4 xl:sticky xl:top-16">
        <Alert>
          <MailPlus class="h-4 w-4" aria-hidden="true" />
          <AlertTitle>Invite included</AlertTitle>
          <AlertDescription>
            Creating this profile emails a registration link to the employee.
            They choose their password and review their details before approval.
          </AlertDescription>
        </Alert>
        <Button class="h-11 w-full gap-2" type="submit" :disabled="saving">
          <UserRoundPlus class="h-4 w-4 shrink-0" aria-hidden="true" />
          {{ saving ? "Creating employee…" : "Create employee and invite" }}
        </Button>
        <ButtonLink class="w-full" variant="outline" to="/workspace/operate/workforce">
          Cancel
        </ButtonLink>
      </aside>
    </form>

    <Dialog v-model:open="inviteOpen">
      <DialogContent class="max-h-[90dvh] overflow-y-auto sm:max-w-lg">
        <form class="space-y-6" @submit.prevent="submitInvite">
          <DialogHeader>
            <div class="mb-2 grid h-11 w-11 place-items-center rounded-lg bg-secondary text-primary">
              <MailPlus class="h-5 w-5" aria-hidden="true" />
            </div>
            <DialogTitle>Send email invitation</DialogTitle>
            <DialogDescription>
              The employee receives a secure link to create their account and
              complete their profile. You can review it before approving access.
            </DialogDescription>
          </DialogHeader>
          <div class="space-y-4">
            <div class="space-y-2">
              <Label for="invite-email">Work email</Label>
              <Input
                id="invite-email"
                v-model.trim="inviteForm.email"
                type="email"
                autocomplete="email"
                placeholder="alex@company.com"
                required
              />
            </div>
            <div class="space-y-2">
              <Label for="invite-role">Workspace access</Label>
              <Select v-model="inviteForm.role">
                <SelectTrigger id="invite-role">
                  <SelectValue placeholder="Select access" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="staff">Staff</SelectItem>
                  <SelectItem value="manager">Manager</SelectItem>
                  <SelectItem value="admin">Administrator</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <p class="text-xs leading-5 text-muted-foreground">
              This invitation expires in 7 days.
            </p>
          </div>
          <DialogFooter class="gap-2">
            <Button variant="outline" type="button" :disabled="saving" @click="inviteOpen = false">
              Cancel
            </Button>
            <Button class="gap-2" type="submit" :disabled="saving">
              <Send class="h-4 w-4 shrink-0" aria-hidden="true" />
              {{ saving ? "Sending invitation…" : "Send invitation" }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </section>
</template>

<script setup>
import {
  ArrowLeft,
  CalendarClock,
  MailPlus,
  Send,
  UserRound,
  UserRoundPlus,
} from "lucide-vue-next";
import { toast } from "@/components/ui/toast";

const business = useBusinessStore();
const { apiFetch } = useApiClient();
const inviteOpen = ref(false);
const saving = ref(false);

const inviteForm = reactive({
  email: "",
  role: "staff",
});

const manualForm = reactive({
  display_name: "",
  email: "",
  role: "staff",
  job_title: "",
  hired_at: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  scheduled_start_time: "",
  scheduled_end_time: "",
  late_grace_minutes: 10,
  consecutive_late_threshold: 3,
  bio: "",
  timezone: "Asia/Manila",
  is_bookable: false,
});

onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses();
  manualForm.timezone = business.activeBusiness?.timezone || "Asia/Manila";
});

async function submitInvite() {
  await createEmployee({
    creation_mode: "invite",
    email: inviteForm.email,
    role: inviteForm.role,
  });
}

async function submitManual() {
  await createEmployee({
    creation_mode: "manual",
    ...compactEmployeePayload(manualForm),
  });
}

async function createEmployee(payload) {
  if (!business.activeBusiness || saving.value) return;
  saving.value = true;

  try {
    const response = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/workforce/employees/`,
      { method: "POST", body: payload },
    );
    toast({
      title: payload.creation_mode === "invite" ? "Invitation sent" : "Employee created",
      description: `A secure registration link was sent to ${response.invitation.email}.`,
    });
    await navigateTo("/workspace/operate/workforce?view=access");
  } catch (error) {
    toast({
      title: payload.creation_mode === "invite" ? "Invitation not sent" : "Employee not created",
      description: error?.data?.error?.message || "Review the details and try again.",
      variant: "destructive",
    });
  } finally {
    saving.value = false;
  }
}

function compactEmployeePayload(value) {
  const payload = { ...value };
  for (const field of [
    "job_title",
    "hired_at",
    "emergency_contact_name",
    "emergency_contact_phone",
    "bio",
  ]) {
    if (!payload[field]) delete payload[field];
  }
  if (!payload.scheduled_start_time || !payload.scheduled_end_time) {
    delete payload.scheduled_start_time;
    delete payload.scheduled_end_time;
  }
  return payload;
}
</script>
