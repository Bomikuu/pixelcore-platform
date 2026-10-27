<template>
  <main class="min-h-dvh bg-muted/30">
    <header class="border-b bg-background">
      <div
        class="mx-auto flex min-h-16 max-w-screen-2xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8"
      >
        <div class="flex min-w-0 items-center gap-3">
          <Avatar class="h-10 w-10 border">
            <AvatarImage
              v-if="business.activeBusiness?.logo"
              :src="business.activeBusiness.logo"
              :alt="`${business.activeBusiness.display_name} logo`"
            />
            <AvatarFallback class="bg-primary/10 font-bold text-primary">
              {{ businessInitials }}
            </AvatarFallback>
          </Avatar>
          <div class="min-w-0">
            <p class="truncate text-sm font-extrabold">
              {{ business.activeBusiness?.display_name || "Employee portal" }}
            </p>
            <p class="text-xs text-muted-foreground">My workday</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <ButtonLink variant="outline" to="/rider/deliveries">My deliveries</ButtonLink>
          <ButtonAnchor
            variant="outline"
            href="/attendance-terminal"
            target="_blank"
            rel="noopener"
          >
            <MonitorSmartphone class="h-4 w-4" aria-hidden="true" />
            <span class="hidden sm:inline">Attendance terminal</span>
          </ButtonAnchor>
          <Button variant="ghost" type="button" @click="signOut">
            <LogOut class="h-4 w-4" aria-hidden="true" />
            <span class="hidden sm:inline">Sign out</span>
          </Button>
        </div>
      </div>
    </header>

    <div class="mx-auto max-w-screen-2xl space-y-5 px-4 py-6 sm:px-6 lg:px-8">
      <StatePanel
        v-if="loading"
        kind="loading"
        title="Loading your employee portal"
        message="Retrieving your schedule, attendance, leave, and documents."
      />

      <StatePanel
        v-else-if="error"
        kind="error"
        title="Employee portal unavailable"
        :message="error"
      >
        <Button variant="outline" type="button" @click="loadPortal">
          <RefreshCw class="h-4 w-4" aria-hidden="true" />
          Try again
        </Button>
      </StatePanel>

      <template v-else-if="portal.employee">
        <section
          class="overflow-hidden rounded-xl border bg-card p-5 sm:p-6 lg:flex lg:items-end lg:justify-between lg:gap-8"
        >
          <div class="flex min-w-0 items-center gap-4">
            <Avatar class="h-16 w-16 border sm:h-20 sm:w-20">
              <AvatarImage
                v-if="portal.employee.profile_image_url"
                :src="portal.employee.profile_image_url"
                :alt="portal.employee.display_name"
                class="object-cover"
              />
              <AvatarFallback class="bg-secondary text-lg font-black text-primary">
                {{ employeeInitials }}
              </AvatarFallback>
            </Avatar>
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <Badge :variant="statusVariant(portal.employee.employment_status)">
                  {{ statusLabel(portal.employee.employment_status) }}
                </Badge>
                <Badge variant="outline">
                  {{ portal.employee.job_title || "Team member" }}
                </Badge>
              </div>
              <h1 class="mt-3 truncate text-2xl font-black tracking-tight sm:text-3xl">
                {{ portal.employee.display_name }}
              </h1>
              <p class="mt-1 text-sm text-muted-foreground">
                {{ portal.employee.email }}
              </p>
            </div>
          </div>
          <div class="mt-5 border-t pt-4 lg:mt-0 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0">
            <p class="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground">
              Regular schedule
            </p>
            <p class="mt-2 text-base font-extrabold">{{ scheduleLabel }}</p>
            <p class="mt-1 text-xs text-muted-foreground">
              {{ portal.employee.late_grace_minutes }} minute arrival grace period
            </p>
          </div>
        </section>

        <Alert
          v-if="portal.employee.employment_status !== 'active'"
          class="border-amber-300 bg-amber-50 text-amber-950"
        >
          <ShieldAlert class="h-4 w-4" aria-hidden="true" />
          <AlertTitle>Manager approval is still pending</AlertTitle>
          <AlertDescription>
            You can review your profile now. Attendance codes and leave requests unlock when a manager activates your employee record.
          </AlertDescription>
        </Alert>

        <dl class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4">
          <div
            v-for="metric in metrics"
            :key="metric.label"
            class="border-b p-4 last:border-b-0 sm:[&:nth-child(odd)]:border-r sm:[&:nth-last-child(-n+2)]:border-b-0 xl:border-b-0 xl:border-r xl:last:border-r-0"
          >
            <div class="flex items-center justify-between gap-3">
              <dt class="text-sm font-semibold text-muted-foreground">{{ metric.label }}</dt>
              <component :is="metric.icon" class="h-4 w-4 text-primary" aria-hidden="true" />
            </div>
            <dd class="mt-2 text-2xl font-black tabular-nums">{{ metric.value }}</dd>
            <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
          </div>
        </dl>

        <Tabs v-model="activeTab" class="space-y-4">
          <div class="overflow-x-auto pb-1">
            <TabsList class="h-auto min-w-max justify-start">
              <TabsTrigger value="overview">
                <LayoutDashboard class="h-4 w-4" aria-hidden="true" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="attendance">
                <Clock3 class="h-4 w-4" aria-hidden="true" />
                Attendance
              </TabsTrigger>
              <TabsTrigger value="leave">
                <CalendarDays class="h-4 w-4" aria-hidden="true" />
                Leave & vacation
              </TabsTrigger>
              <TabsTrigger value="documents">
                <Files class="h-4 w-4" aria-hidden="true" />
                Documents
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="overview" class="mt-0 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
            <Card id="attendance-credentials">
              <CardHeader>
                <div class="flex items-start gap-3">
                  <div class="grid h-10 w-10 place-items-center rounded-lg bg-secondary text-primary">
                    <KeyRound class="h-5 w-5" aria-hidden="true" />
                  </div>
                  <div>
                    <CardTitle>Attendance code</CardTitle>
                    <CardDescription>
                      Generate a one-use code, then enter it on a paired terminal.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent class="space-y-4">
                <div class="flex items-center justify-between gap-4 rounded-lg border bg-muted/25 p-4">
                  <div class="flex items-center gap-3">
                    <span
                      class="h-2.5 w-2.5 rounded-full"
                      :class="portal.summary.is_clocked_in ? 'bg-emerald-500' : 'bg-muted-foreground/40'"
                      aria-hidden="true"
                    />
                    <div>
                      <p class="text-sm font-bold">
                        {{ portal.summary.is_clocked_in ? "Currently clocked in" : "Ready to clock in" }}
                      </p>
                      <p class="mt-1 text-xs text-muted-foreground">
                        The terminal identifies you and the action from the code.
                      </p>
                    </div>
                  </div>
                </div>

                <Alert v-if="issuedCode">
                  <BadgeCheck class="h-4 w-4" aria-hidden="true" />
                  <AlertTitle>Your {{ actionLabel(issuedCode.action).toLowerCase() }} code</AlertTitle>
                  <AlertDescription>
                    <div class="mt-3 flex items-center justify-between gap-3 rounded-md bg-background p-3">
                      <code class="font-mono text-2xl font-black tracking-[0.3em]">{{ issuedCode.code }}</code>
                      <Button variant="outline" size="sm" type="button" @click="copyText(issuedCode.code, 'Attendance code copied')">
                        <Copy class="h-4 w-4" aria-hidden="true" />
                        Copy
                      </Button>
                    </div>
                    <p class="mt-3">
                      Use it once within {{ codeRemainingLabel }}. Generating another code invalidates this one.
                    </p>
                  </AlertDescription>
                </Alert>

                <div class="grid gap-3 sm:grid-cols-2">
                  <Button
                    class="h-11"
                    type="button"
                    :disabled="codeBusy || portal.employee.employment_status !== 'active' || portal.summary.is_clocked_in"
                    @click="openCodeDialog('clock_in')"
                  >
                    <LogIn class="h-4 w-4" aria-hidden="true" />
                    Get clock-in code
                  </Button>
                  <Button
                    class="h-11"
                    variant="outline"
                    type="button"
                    :disabled="codeBusy || portal.employee.employment_status !== 'active' || !portal.summary.is_clocked_in"
                    @click="openCodeDialog('clock_out')"
                  >
                    <LogOut class="h-4 w-4" aria-hidden="true" />
                    Get clock-out code
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader class="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle>Leave & vacation</CardTitle>
                  <CardDescription>Your latest requests and manager decisions.</CardDescription>
                </div>
                <Button
                  size="sm"
                  type="button"
                  :disabled="portal.employee.employment_status !== 'active'"
                  @click="leaveDialogOpen = true"
                >
                  <Plus class="h-4 w-4" aria-hidden="true" />
                  Request leave
                </Button>
              </CardHeader>
              <CardContent>
                <WorkforceLeaveList :items="portal.leave_requests.slice(0, 4)" @cancel="cancelLeave" />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="attendance" class="mt-0">
            <WorkforceAttendanceTable :items="portal.attendance" />
          </TabsContent>

          <TabsContent value="leave" class="mt-0">
            <Card>
              <CardHeader class="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle>Leave history</CardTitle>
                  <CardDescription>Submitted requests remain visible with their current decision.</CardDescription>
                </div>
                <Button type="button" :disabled="portal.employee.employment_status !== 'active'" @click="leaveDialogOpen = true">
                  <Plus class="h-4 w-4" aria-hidden="true" />
                  Request leave
                </Button>
              </CardHeader>
              <CardContent>
                <WorkforceLeaveList :items="portal.leave_requests" @cancel="cancelLeave" />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents" class="mt-0">
            <Card>
              <CardHeader>
                <CardTitle>My documents</CardTitle>
                <CardDescription>Documents retained by the business and their review status.</CardDescription>
              </CardHeader>
              <CardContent>
                <StatePanel
                  v-if="!portal.documents.length"
                  title="No documents on file"
                  message="Documents uploaded by you or a manager will appear here."
                />
                <div v-else class="divide-y rounded-lg border">
                  <div v-for="document in portal.documents" :key="document.public_id" class="flex items-center justify-between gap-4 p-4">
                    <div class="flex min-w-0 items-center gap-3">
                      <FileText class="h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                      <div class="min-w-0">
                        <p class="truncate text-sm font-bold">{{ document.original_name }}</p>
                        <p class="mt-1 text-xs capitalize text-muted-foreground">{{ document.document_type.replaceAll('_', ' ') }}</p>
                      </div>
                    </div>
                    <StatusPill :value="document.status" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </template>
    </div>

    <Dialog v-model:open="codeDialogOpen">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <div class="mb-2 grid h-11 w-11 place-items-center rounded-lg bg-secondary text-primary">
            <KeyRound class="h-5 w-5" aria-hidden="true" />
          </div>
          <DialogTitle>Generate {{ actionLabel(pendingAction).toLowerCase() }} code?</DialogTitle>
          <DialogDescription>
            This creates a six-digit code that works once and expires after five minutes. Any earlier unused code is invalidated.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" type="button" @click="codeDialogOpen = false">Cancel</Button>
          <Button type="button" :disabled="codeBusy" @click="issueAttendanceCode">
            <KeyRound class="h-4 w-4" aria-hidden="true" />
            {{ codeBusy ? "Generating…" : "Generate code" }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="leaveDialogOpen">
      <DialogContent class="sm:max-w-lg">
        <form @submit.prevent="submitLeave">
          <DialogHeader>
            <div class="mb-2 grid h-11 w-11 place-items-center rounded-lg bg-secondary text-primary">
              <CalendarPlus class="h-5 w-5" aria-hidden="true" />
            </div>
            <DialogTitle>Request leave or vacation</DialogTitle>
            <DialogDescription>Your manager will review the dates and reason before the request is approved.</DialogDescription>
          </DialogHeader>
          <div class="mt-6 space-y-4">
            <div>
              <Label for="employee-leave-type">Leave type</Label>
              <NativeSelect id="employee-leave-type" v-model="leaveForm.leave_type" class="mt-2">
                <option value="vacation">Vacation</option>
                <option value="sick">Sick leave</option>
                <option value="personal">Personal leave</option>
                <option value="emergency">Emergency leave</option>
                <option value="unpaid">Unpaid leave</option>
              </NativeSelect>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <div>
                <Label for="employee-leave-start">Start date</Label>
                <Input id="employee-leave-start" v-model="leaveForm.start_date" class="mt-2" type="date" required />
              </div>
              <div>
                <Label for="employee-leave-end">End date</Label>
                <Input id="employee-leave-end" v-model="leaveForm.end_date" class="mt-2" type="date" required />
              </div>
            </div>
            <Label class="flex items-center gap-3 rounded-lg border p-3">
              <NativeCheckbox v-model="leaveForm.partial_day" />
              <span class="text-sm font-semibold">This is a partial day</span>
            </Label>
            <div>
              <Label for="employee-leave-reason">Reason</Label>
              <Textarea id="employee-leave-reason" v-model.trim="leaveForm.reason" class="mt-2 min-h-28" maxlength="2000" required />
            </div>
          </div>
          <DialogFooter class="mt-6">
            <Button variant="outline" type="button" @click="leaveDialogOpen = false">Cancel</Button>
            <Button :disabled="leaveBusy">
              <Send class="h-4 w-4" aria-hidden="true" />
              {{ leaveBusy ? "Submitting…" : "Submit request" }}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </main>
</template>

<script setup>
import {
  BadgeCheck,
  CalendarDays,
  CalendarPlus,
  Clock3,
  Copy,
  FileText,
  Files,
  KeyRound,
  LayoutDashboard,
  LogIn,
  LogOut,
  MonitorSmartphone,
  Plus,
  RefreshCw,
  Send,
  ShieldAlert,
  TimerReset,
  Umbrella,
} from "lucide-vue-next";
import WorkforceAttendanceTable from "@/components/workforce/AttendanceTable.vue";
import WorkforceLeaveList from "@/components/workforce/LeaveList.vue";
import { toast } from "@/components/ui/toast";

definePageMeta({ layout: "storefront" });
useHead({ title: "Employee portal | PixelCore" });

const auth = useAuthStore();
const business = useBusinessStore();
const { apiFetch } = useApiClient();
const loading = ref(true);
const error = ref("");
const activeTab = ref("overview");
const codeBusy = ref(false);
const leaveBusy = ref(false);
const codeDialogOpen = ref(false);
const leaveDialogOpen = ref(false);
const issuedCode = ref(null);
const pendingAction = ref("clock_in");
const clockNow = ref(Date.now());
let clockTimer;
const portal = reactive({
  employee: null,
  summary: {},
  attendance: [],
  leave_requests: [],
  documents: [],
  attendance_flags: [],
});
const leaveForm = reactive({
  leave_type: "vacation",
  start_date: "",
  end_date: "",
  partial_day: false,
  reason: "",
});

const businessInitials = computed(() => initials(business.activeBusiness?.display_name || "PC"));
const employeeInitials = computed(() => initials(portal.employee?.display_name || "Employee"));
const scheduleLabel = computed(() => {
  if (!portal.employee?.scheduled_start_time || !portal.employee?.scheduled_end_time) return "Not scheduled";
  return `${shortTime(portal.employee.scheduled_start_time)}–${shortTime(portal.employee.scheduled_end_time)}`;
});
const codeRemainingSeconds = computed(() => {
  if (!issuedCode.value?.expires_at) return 0;
  return Math.max(
    0,
    Math.ceil((new Date(issuedCode.value.expires_at).getTime() - clockNow.value) / 1000),
  );
});
const codeRemainingLabel = computed(() => {
  const minutes = Math.floor(codeRemainingSeconds.value / 60);
  const seconds = String(codeRemainingSeconds.value % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
});
const metrics = computed(() => [
  {
    label: "Hours worked",
    value: formatMinutes(portal.summary.worked_minutes_30d),
    detail: `${portal.summary.shifts_30d || 0} shifts in the last 30 days`,
    icon: TimerReset,
  },
  {
    label: "Approved leave",
    value: formatDays(portal.summary.approved_leave_days),
    detail: "Approved days this year",
    icon: CalendarDays,
  },
  {
    label: "Vacation used",
    value: formatDays(portal.summary.vacation_days),
    detail: `${portal.summary.pending_leave_requests || 0} pending requests`,
    icon: Umbrella,
  },
  {
    label: "Late shifts",
    value: portal.summary.late_shifts_30d || 0,
    detail: "Recorded in the last 30 days",
    icon: Clock3,
  },
]);

onMounted(() => {
  loadPortal();
  clockTimer = window.setInterval(() => {
    clockNow.value = Date.now();
    if (issuedCode.value && codeRemainingSeconds.value === 0) {
      issuedCode.value = null;
    }
  }, 1000);
});

onBeforeUnmount(() => window.clearInterval(clockTimer));

async function loadPortal() {
  loading.value = true;
  error.value = "";
  try {
    await auth.restoreSession();
    if (!auth.isAuthenticated) {
      await navigateTo("/login?next=/employee");
      return;
    }
    if (!business.businesses.length) await business.loadBusinesses();
    const candidates = [
      business.activeBusiness,
      ...business.businesses.filter((item) => item.public_id !== business.activeBusiness?.public_id),
    ].filter(Boolean);
    let response = null;
    for (const candidate of candidates) {
      try {
        response = await apiFetch(`businesses/${candidate.public_id}/workforce/me/`);
        business.setActiveBusiness(candidate);
        break;
      } catch (requestError) {
        if (requestError?.status !== 404 && requestError?.statusCode !== 404) throw requestError;
      }
    }
    if (!response) throw new Error("No employee profile is connected to this account.");
    Object.assign(portal, response);
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || requestError?.message || "Your employee profile could not be loaded.";
  } finally {
    loading.value = false;
  }
}

function openCodeDialog(action) {
  pendingAction.value = action;
  codeDialogOpen.value = true;
}

async function issueAttendanceCode() {
  codeBusy.value = true;
  try {
    const response = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/workforce/me/attendance-code/`,
      {
        method: "POST",
        body: { action: pendingAction.value },
      },
    );
    issuedCode.value = response;
    clockNow.value = Date.now();
    codeDialogOpen.value = false;
    toast({
      title: `${actionLabel(response.action)} code ready`,
      description: "Enter it on the attendance terminal within five minutes.",
    });
  } catch (requestError) {
    failedToast(requestError, "Attendance code not created");
  } finally {
    codeBusy.value = false;
  }
}

async function submitLeave() {
  leaveBusy.value = true;
  try {
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/workforce/me/leave-requests/`, {
      method: "POST",
      body: leaveForm,
    });
    portal.leave_requests.unshift(response);
    portal.summary.pending_leave_requests = Number(portal.summary.pending_leave_requests || 0) + 1;
    Object.assign(leaveForm, { leave_type: "vacation", start_date: "", end_date: "", partial_day: false, reason: "" });
    leaveDialogOpen.value = false;
    toast({ title: "Leave request submitted", description: "Your manager can now review the request." });
  } catch (requestError) {
    failedToast(requestError, "Leave request not submitted");
  } finally {
    leaveBusy.value = false;
  }
}

async function cancelLeave(item) {
  try {
    const updated = await apiFetch(`businesses/${business.activeBusiness.public_id}/workforce/me/leave-requests/${item.public_id}/cancel/`, { method: "POST" });
    Object.assign(item, updated);
    portal.summary.pending_leave_requests = Math.max(0, Number(portal.summary.pending_leave_requests || 0) - 1);
    toast({ title: "Leave request cancelled" });
  } catch (requestError) {
    failedToast(requestError, "Request not cancelled");
  }
}

async function copyText(value, title) {
  await navigator.clipboard.writeText(value);
  toast({ title });
}

async function signOut() {
  await auth.logout();
  business.$reset();
  await navigateTo("/login");
}

function failedToast(requestError, title) {
  toast({ title, description: requestError?.data?.error?.message || "Please try again.", variant: "destructive" });
}

function initials(value) {
  return String(value).split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
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

function statusVariant(value) {
  return value === "active" ? "secondary" : value === "suspended" ? "destructive" : "outline";
}

function statusLabel(value) {
  return value === "active" ? "Active employee" : value === "pending" ? "Pending approval" : value;
}

function actionLabel(action) {
  return action === "clock_out" ? "Clock-out" : "Clock-in";
}
</script>
