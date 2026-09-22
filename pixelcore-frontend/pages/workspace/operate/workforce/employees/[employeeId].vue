<template>
  <section class="workspace-page space-y-5">
    <div class="flex items-center justify-between gap-3">
      <ButtonLink variant="ghost" to="/workspace/operate/workforce">
        <ArrowLeft class="h-4 w-4" aria-hidden="true" />
        Back to workforce
      </ButtonLink>
      <Button variant="outline" size="sm" type="button" :disabled="loading" @click="load">
        <RefreshCw class="h-4 w-4" :class="loading ? 'animate-spin' : ''" aria-hidden="true" />
        Refresh
      </Button>
    </div>

    <StatePanel
      v-if="loading"
      kind="loading"
      title="Loading employee profile"
      message="Retrieving the employee summary and workforce history."
    />
    <StatePanel
      v-else-if="error"
      kind="error"
      title="Employee profile unavailable"
      :message="error"
    >
      <Button variant="outline" type="button" @click="load">Try again</Button>
    </StatePanel>

    <template v-else-if="record.employee">
      <section class="overflow-hidden rounded-xl border bg-card p-5 sm:p-6">
        <div class="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div class="flex min-w-0 items-center gap-4">
            <Avatar class="h-16 w-16 border sm:h-20 sm:w-20">
              <AvatarImage
                v-if="record.employee.profile_image_url"
                :src="record.employee.profile_image_url"
                :alt="record.employee.display_name"
                class="object-cover"
              />
              <AvatarFallback class="bg-secondary text-lg font-black text-primary">
                {{ initials(record.employee.display_name) }}
              </AvatarFallback>
            </Avatar>
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <StatusPill :value="record.employee.employment_status" />
                <Badge variant="outline">{{ record.employee.employee_code }}</Badge>
              </div>
              <h1 class="mt-3 truncate text-2xl font-black tracking-tight sm:text-3xl">
                {{ record.employee.display_name }}
              </h1>
              <p class="mt-1 text-sm text-muted-foreground">
                {{ record.employee.job_title || "Team member" }} · {{ record.employee.email }}
              </p>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <Button v-if="canEdit" class="gap-2" type="button" @click="editOpen = true">
              <Pencil class="h-4 w-4 shrink-0" aria-hidden="true" />
              Edit employee
            </Button>
            <ButtonAnchor v-if="record.employee.email" variant="outline" :href="`mailto:${record.employee.email}`">
              <Mail class="h-4 w-4" aria-hidden="true" />
              Email employee
            </ButtonAnchor>
            <Button
              v-if="canEdit && record.employee.employment_status === 'pending'"
              type="button"
              :disabled="saving"
              @click="approveEmployee"
            >
              <UserCheck class="h-4 w-4" aria-hidden="true" />
              Approve employee
            </Button>
          </div>
        </div>
      </section>

      <dl class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4">
        <div v-for="metric in metrics" :key="metric.label" class="border-b p-4 last:border-b-0 sm:[&:nth-child(odd)]:border-r sm:[&:nth-last-child(-n+2)]:border-b-0 xl:border-b-0 xl:border-r xl:last:border-r-0">
          <div class="flex items-center justify-between gap-3">
            <dt class="text-sm font-semibold text-muted-foreground">{{ metric.label }}</dt>
            <component :is="metric.icon" class="h-4 w-4 text-primary" aria-hidden="true" />
          </div>
          <dd class="mt-2 text-2xl font-black tabular-nums">{{ metric.value }}</dd>
          <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
        </div>
      </dl>

      <Tabs v-model="activeTab" class="space-y-4">
        <TabsList class="grid h-auto w-full grid-cols-2 gap-1 sm:inline-flex sm:w-auto" aria-label="Employee profile sections">
          <TabsTrigger class="min-h-11" value="overview">
            <UserRound class="h-4 w-4" aria-hidden="true" />
            Overview
          </TabsTrigger>
          <TabsTrigger class="min-h-11" value="attendance">
            <Clock3 class="h-4 w-4" aria-hidden="true" />
            Attendance
          </TabsTrigger>
          <TabsTrigger class="min-h-11" value="leave">
            <CalendarDays class="h-4 w-4" aria-hidden="true" />
            Leave
          </TabsTrigger>
          <TabsTrigger class="min-h-11" value="documents">
            <Files class="h-4 w-4" aria-hidden="true" />
            Documents
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" class="mt-0 grid gap-5 xl:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Employee details</CardTitle>
              <CardDescription>Identity, contact, assignment, and employment information.</CardDescription>
            </CardHeader>
            <CardContent class="grid gap-4 sm:grid-cols-2">
              <WorkforceInfoRow label="Email" :value="record.employee.email || 'Not provided'" :icon="Mail" />
              <WorkforceInfoRow label="Job title" :value="record.employee.job_title || 'Not assigned'" :icon="BriefcaseBusiness" />
              <WorkforceInfoRow label="Hire date" :value="formatDate(record.employee.hired_at)" :icon="CalendarDays" />
              <WorkforceInfoRow label="Employee code" :value="record.employee.employee_code" :icon="BadgeCheck" />
              <WorkforceInfoRow label="Emergency contact" :value="record.employee.emergency_contact_name || 'Not provided'" :icon="ShieldCheck" />
              <WorkforceInfoRow label="Emergency phone" :value="record.employee.emergency_contact_phone || 'Not provided'" :icon="Phone" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Schedule & attendance access</CardTitle>
              <CardDescription>The employee generates attendance codes from their portal.</CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="grid gap-3 sm:grid-cols-2">
                <div class="rounded-lg border bg-muted/25 p-4">
                  <p class="text-xs text-muted-foreground">Regular shift</p>
                  <p class="mt-1 font-bold">{{ scheduleLabel }}</p>
                </div>
                <div class="rounded-lg border bg-muted/25 p-4">
                  <p class="text-xs text-muted-foreground">Grace period</p>
                  <p class="mt-1 font-bold">{{ record.employee.late_grace_minutes }} minutes</p>
                </div>
              </div>
              <Alert>
                <KeyRound class="h-4 w-4" aria-hidden="true" />
                <AlertTitle>{{ record.summary.is_clocked_in ? "Currently clocked in" : "Currently clocked out" }}</AlertTitle>
                <AlertDescription>
                  Employees generate separate, single-use clock-in and clock-out codes after signing in. Codes expire after five minutes.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="attendance" class="mt-0">
          <WorkforceAttendanceTable :items="record.attendance" />
        </TabsContent>

        <TabsContent value="leave" class="mt-0">
          <Card>
            <CardHeader>
              <CardTitle>Leave requests</CardTitle>
              <CardDescription>Review pending requests without losing the employee history.</CardDescription>
            </CardHeader>
            <CardContent>
              <StatePanel v-if="!record.leave_requests.length" title="No leave requests" message="This employee has not requested time off." />
              <div v-else class="divide-y rounded-lg border">
                <article v-for="item in record.leave_requests" :key="item.public_id" class="flex flex-col justify-between gap-4 p-4 lg:flex-row lg:items-center">
                  <div>
                    <div class="flex flex-wrap items-center gap-2">
                      <p class="text-sm font-bold capitalize">{{ item.leave_type.replaceAll('_', ' ') }}</p>
                      <StatusPill :value="item.status" />
                    </div>
                    <p class="mt-1 text-sm text-muted-foreground">{{ formatDate(item.start_date) }}–{{ formatDate(item.end_date) }}</p>
                    <p class="mt-2 text-sm">{{ item.reason }}</p>
                  </div>
                  <div v-if="item.status === 'pending'" class="flex gap-2">
                    <Button variant="outline" size="sm" type="button" @click="reviewLeave(item, 'rejected')">
                      <X class="h-4 w-4" aria-hidden="true" />Reject
                    </Button>
                    <Button size="sm" type="button" @click="reviewLeave(item, 'approved')">
                      <Check class="h-4 w-4" aria-hidden="true" />Approve
                    </Button>
                  </div>
                </article>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents" class="mt-0">
          <Card>
            <CardHeader>
              <CardTitle>Employee documents</CardTitle>
              <CardDescription>Review retained identity, contract, certification, permit, and other files.</CardDescription>
            </CardHeader>
            <CardContent>
              <StatePanel v-if="!record.documents.length" title="No employee documents" message="No documents are attached to this profile." />
              <div v-else class="divide-y rounded-lg border">
                <div v-for="item in record.documents" :key="item.public_id" class="flex flex-col justify-between gap-4 p-4 sm:flex-row sm:items-center">
                  <div class="flex min-w-0 items-center gap-3">
                    <FileText class="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                    <div class="min-w-0">
                      <p class="truncate text-sm font-bold">{{ item.original_name }}</p>
                      <p class="mt-1 text-xs capitalize text-muted-foreground">{{ item.document_type.replaceAll('_', ' ') }}</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <StatusPill :value="item.status" />
                    <template v-if="item.status === 'pending'">
                      <Button variant="outline" size="sm" type="button" @click="reviewDocument(item, 'rejected')">Reject</Button>
                      <Button size="sm" type="button" @click="reviewDocument(item, 'approved')">Approve</Button>
                    </template>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      <EmployeeEditDialog
        v-if="canEdit"
        v-model:open="editOpen"
        :employee="record.employee"
        :business-id="business.activeBusiness.public_id"
        @saved="Object.assign(record.employee, $event)"
      />
    </template>
  </section>
</template>

<script setup>
import {
  ArrowLeft,
  BadgeCheck,
  BriefcaseBusiness,
  CalendarDays,
  Check,
  Clock3,
  FileText,
  Files,
  KeyRound,
  Mail,
  Phone,
  Pencil,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  UserRound,
  X,
} from "lucide-vue-next";
import WorkforceAttendanceTable from "@/components/workforce/AttendanceTable.vue";
import WorkforceInfoRow from "@/components/workforce/InfoRow.vue";
import EmployeeEditDialog from "@/components/workforce/EmployeeEditDialog.vue";
import { toast } from "@/components/ui/toast";

const route = useRoute();
const business = useBusinessStore();
const auth = useAuthStore();
const { apiFetch } = useApiClient();
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const activeTab = ref("overview");
const editOpen = ref(false);
const canEdit = computed(() => {
  const membership = auth.user?.businesses?.find(
    (item) => item.public_id === business.activeBusiness?.public_id,
  );
  return ["owner", "admin"].includes(membership?.role);
});
const record = reactive({ employee: null, summary: {}, attendance: [], leave_requests: [], documents: [], attendance_flags: [] });

const scheduleLabel = computed(() => {
  if (!record.employee?.scheduled_start_time || !record.employee?.scheduled_end_time) return "Not scheduled";
  return `${shortTime(record.employee.scheduled_start_time)}–${shortTime(record.employee.scheduled_end_time)}`;
});
const metrics = computed(() => [
  { label: "Hours worked", value: formatMinutes(record.summary.worked_minutes_30d), detail: `${record.summary.shifts_30d || 0} shifts in 30 days`, icon: Clock3 },
  { label: "Approved leave", value: formatDays(record.summary.approved_leave_days), detail: `${record.summary.vacation_days || 0} vacation days`, icon: CalendarDays },
  { label: "Late shifts", value: record.summary.late_shifts_30d || 0, detail: "Recorded in 30 days", icon: BadgeCheck },
  { label: "Document readiness", value: `${record.summary.approved_documents || 0}/${record.summary.document_count || 0}`, detail: `${record.summary.open_attendance_flags || 0} open attendance flags`, icon: Files },
]);

watch(() => business.activeBusiness?.public_id, load);
onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses();
  await load();
});

async function load() {
  if (!business.activeBusiness) return;
  loading.value = true;
  error.value = "";
  try {
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/workforce/employees/${route.params.employeeId}/summary/`);
    Object.assign(record, response);
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || "This employee record could not be loaded.";
  } finally {
    loading.value = false;
  }
}

async function approveEmployee() {
  saving.value = true;
  try {
    const updated = await apiFetch(`businesses/${business.activeBusiness.public_id}/staff/${record.employee.public_id}/`, {
      method: "PATCH",
      body: { employment_status: "active", is_active: true },
    });
    Object.assign(record.employee, updated);
    toast({ title: "Employee approved", description: `${record.employee.display_name} can now generate attendance codes and request leave.` });
  } catch (requestError) {
    failedToast(requestError, "Employee not approved");
  } finally {
    saving.value = false;
  }
}

async function reviewLeave(item, status) {
  try {
    Object.assign(item, await apiFetch(`businesses/${business.activeBusiness.public_id}/workforce/leave-requests/${item.public_id}/`, { method: "PATCH", body: { status } }));
    toast({ title: `Leave request ${status}` });
    await load();
  } catch (requestError) {
    failedToast(requestError, "Leave decision not saved");
  }
}

async function reviewDocument(item, status) {
  try {
    Object.assign(item, await apiFetch(`businesses/${business.activeBusiness.public_id}/workforce/documents/${item.public_id}/review/`, { method: "POST", body: { status } }));
    toast({ title: `Document ${status}` });
    await load();
  } catch (requestError) {
    failedToast(requestError, "Document decision not saved");
  }
}

function failedToast(requestError, title) {
  toast({ title, description: requestError?.data?.error?.message || "Please try again.", variant: "destructive" });
}

function initials(value) {
  return String(value).split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function formatDate(value) {
  if (!value) return "Not recorded";
  const normalized = String(value).length === 10 ? `${value}T00:00:00Z` : value;
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric", timeZone: String(value).length === 10 ? "UTC" : undefined }).format(new Date(normalized));
}

function shortTime(value) {
  const [hourText, minute = "00"] = String(value).split(":");
  const hour = Number(hourText);
  return `${hour % 12 || 12}:${minute} ${hour >= 12 ? "PM" : "AM"}`;
}

function formatMinutes(value = 0) {
  const minutes = Number(value || 0);
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
}

function formatDays(value = 0) {
  return `${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })} days`;
}
</script>
