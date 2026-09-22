<template>
  <section class="workspace-page space-y-5">
    <PageHeader
      title="Employees & attendance"
      description="Create employee profiles, track the workday, review attendance exceptions, and manage secure clock-in terminals."
    >
      <template #actions>
        <ButtonAnchor
          variant="outline"
          href="/attendance-terminal"
          target="_blank"
          rel="noopener"
          ><ExternalLink class="h-4 w-4" aria-hidden="true" /> Open attendance
          terminal</ButtonAnchor
        >
        <ButtonLink to="/workspace/operate/workforce/employees/new"
          ><UserPlus class="h-4 w-4" aria-hidden="true" /> Create
          employee</ButtonLink
        >
      </template>
    </PageHeader>

    <dl
      class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4"
    >
      <div
        v-for="metric in metrics"
        :key="metric.label"
        class="border-b p-4 last:border-b-0 sm:[&:nth-child(odd)]:border-r sm:[&:nth-last-child(-n+2)]:border-b-0 xl:border-b-0 xl:border-r xl:last:border-r-0"
      >
        <div class="flex items-center justify-between gap-3">
          <dt class="text-sm font-semibold text-muted-foreground">
            {{ metric.label }}
          </dt>
          <component
            :is="metric.icon"
            class="h-4 w-4 text-muted-foreground"
            aria-hidden="true"
          />
        </div>
        <dd class="mt-2 text-2xl font-extrabold tabular-nums">
          {{ metric.value }}
        </dd>
        <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
      </div>
    </dl>

    <StatePanel
      v-if="loading"
      kind="loading"
      title="Loading workforce"
      message="Retrieving employee, attendance, leave, document, and terminal records."
    />
    <StatePanel
      v-else-if="error"
      kind="error"
      title="Workforce unavailable"
      :message="error"
      ><Button variant="outline" type="button" @click="load"
        >Try again</Button
      ></StatePanel
    >

    <Tabs
      v-else
      :model-value="view"
      class="space-y-4"
      @update:model-value="setView"
    >
      <div
        class="flex flex-col justify-between gap-3 sm:flex-row sm:items-center"
      >
        <TabsList class="h-auto w-full justify-start overflow-x-auto sm:w-auto">
          <TabsTrigger
            v-for="item in tabs"
            :key="item.value"
            :value="item.value"
            >{{ item.label }}</TabsTrigger
          >
        </TabsList>
        <Button
          v-if="['leave', 'documents', 'terminals'].includes(view)"
          type="button"
          @click="formOpen = true"
          ><Plus class="h-4 w-4" aria-hidden="true" /> Add
          {{
            view === "leave"
              ? "request"
              : view === "documents"
                ? "document"
                : "terminal"
          }}</Button
        >
      </div>

      <TabsContent value="staff" class="mt-0">
        <Card class="overflow-hidden"
          ><CardHeader class="border-b"
            ><div class="flex items-start justify-between gap-4">
              <div>
                <CardTitle>Employee directory</CardTitle
                ><CardDescription
                  >Profiles, schedules, approval state, and attendance
                  credentials.</CardDescription
                >
              </div>
              <Badge variant="outline">{{ staff.length }} employees</Badge>
            </div></CardHeader
          ><CardContent class="p-0">
            <StatePanel
              v-if="!staff.length"
              title="No employees yet"
              message="Create the first employee profile to begin scheduling and attendance tracking."
            />
            <div v-else class="overflow-x-auto">
              <Table class="min-w-[52rem]"
                ><TableHeader
                  ><TableRow
                    ><TableHead>Employee</TableHead
                    ><TableHead>Employee code</TableHead
                    ><TableHead>Schedule</TableHead
                    ><TableHead>Assignments</TableHead
                    ><TableHead>Status</TableHead
                    ><TableHead class="text-right">Actions</TableHead></TableRow
                  ></TableHeader
                ><TableBody
                  ><TableRow v-for="employee in staff" :key="employee.public_id"
                    ><TableCell
                      ><div class="flex items-center gap-3">
                        <Avatar class="h-9 w-9">
                          <AvatarImage
                            v-if="employee.profile_image_url"
                            :src="employee.profile_image_url"
                            :alt="employee.display_name"
                            class="object-cover"
                          />
                          <AvatarFallback
                            class="bg-primary/10 text-xs font-bold text-primary"
                            >{{
                              initials(employee.display_name)
                            }}</AvatarFallback
                          ></Avatar
                        >
                        <div>
                          <NuxtLink
                            :to="`/workspace/operate/workforce/employees/${employee.public_id}`"
                            class="font-bold underline-offset-4 hover:underline"
                          >
                            {{ employee.display_name }}
                          </NuxtLink>
                          <p class="mt-0.5 text-xs text-muted-foreground">
                            {{
                              employee.job_title ||
                              employee.email ||
                              "No job title"
                            }}
                          </p>
                        </div>
                      </div></TableCell
                    ><TableCell class="font-mono text-xs font-bold">{{
                      employee.employee_code
                    }}</TableCell
                    ><TableCell>{{
                      employee.scheduled_start_time
                        ? `${shortTime(employee.scheduled_start_time)}–${shortTime(employee.scheduled_end_time)}`
                        : "Not set"
                    }}</TableCell
                    ><TableCell>{{
                      employee.is_bookable
                        ? "Services & bookings"
                        : "Internal operations"
                    }}</TableCell
                    ><TableCell
                      ><StatusPill
                        :value="employee.employment_status" /></TableCell
                    ><TableCell
                      ><div class="flex justify-end gap-2">
                        <Button
                          v-if="employee.employment_status === 'pending'"
                          variant="outline"
                          size="sm"
                          type="button"
                          @click="approveStaff(employee)"
                          >Approve</Button
                        ><ButtonLink
                          variant="outline"
                          size="sm"
                          :to="`/workspace/operate/workforce/employees/${employee.public_id}`"
                        >
                          View profile
                        </ButtonLink>
                      </div></TableCell
                    ></TableRow
                  ></TableBody
                ></Table
              >
            </div>
          </CardContent></Card
        >
      </TabsContent>

      <TabsContent value="attendance" class="mt-0">
        <Card class="overflow-hidden"
          ><CardHeader class="border-b"
            ><div class="flex items-start justify-between gap-4">
              <div>
                <CardTitle>Employee tracker</CardTitle
                ><CardDescription
                  >Live clock status, shift timing, and recorded lateness from
                  attendance terminals.</CardDescription
                >
              </div>
              <Badge variant="outline">{{ attendance.length }} records</Badge>
            </div></CardHeader
          ><CardContent class="p-0">
            <StatePanel
              v-if="!attendance.length"
              title="No attendance recorded"
              message="Clock-ins from a paired attendance terminal will appear here."
            />
            <div v-else class="overflow-x-auto">
              <Table class="min-w-[52rem]"
                ><TableHeader
                  ><TableRow
                    ><TableHead>Employee</TableHead
                    ><TableHead>Clock in</TableHead
                    ><TableHead>Clock out</TableHead
                    ><TableHead>Shift result</TableHead
                    ><TableHead>Notes</TableHead></TableRow
                  ></TableHeader
                ><TableBody
                  ><TableRow
                    v-for="record in attendance"
                    :key="record.public_id"
                    ><TableCell class="font-bold">{{
                      record.staff_name
                    }}</TableCell
                    ><TableCell>{{
                      record.clock_in ? formatDate(record.clock_in) : "—"
                    }}</TableCell
                    ><TableCell>{{
                      record.clock_out
                        ? formatDate(record.clock_out)
                        : "Currently working"
                    }}</TableCell
                    ><TableCell
                      ><div class="flex items-center gap-2">
                        <StatusPill :value="record.status" /><span
                          v-if="record.late_minutes"
                          class="text-xs text-muted-foreground"
                          >{{ record.late_minutes }} min late</span
                        >
                      </div></TableCell
                    ><TableCell
                      class="max-w-xs truncate text-muted-foreground"
                      >{{
                        record.late_reason ||
                        record.override_reason ||
                        record.notes ||
                        "—"
                      }}</TableCell
                    ></TableRow
                  ></TableBody
                ></Table
              >
            </div>
          </CardContent></Card
        >
      </TabsContent>

      <TabsContent value="access" class="mt-0">
        <Card class="overflow-hidden">
          <CardHeader class="border-b">
            <div
              class="flex flex-col justify-between gap-4 sm:flex-row sm:items-start"
            >
              <div>
                <CardTitle>Team access</CardTitle>
                <CardDescription>
                  Workspace memberships and employee invitations stay beside the
                  workforce records they belong to.
                </CardDescription>
              </div>
              <ButtonLink to="/workspace/operate/workforce/employees/new">
                <UserPlus class="h-4 w-4" aria-hidden="true" />
                Create & invite employee
              </ButtonLink>
            </div>
          </CardHeader>
          <CardContent class="p-0">
            <div class="overflow-x-auto">
              <Table class="min-w-[48rem]">
                <TableHeader>
                  <TableRow>
                    <TableHead>Person</TableHead>
                    <TableHead>Access</TableHead>
                    <TableHead>Workforce profile</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow
                    v-for="member in members"
                    :key="`member-${member.id}`"
                  >
                    <TableCell>
                      <div class="flex items-center gap-3">
                        <Avatar class="h-9 w-9">
                          <AvatarFallback
                            class="bg-primary/10 text-xs font-bold text-primary"
                          >
                            {{ initials(member.name) }}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p class="font-bold">{{ member.name }}</p>
                          <p class="mt-0.5 text-xs text-muted-foreground">
                            {{ member.email }}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell class="capitalize">{{ member.role }}</TableCell>
                    <TableCell>{{
                      employeeForEmail(member.email)?.job_title ||
                      "Connected member"
                    }}</TableCell>
                    <TableCell><StatusPill :value="member.status" /></TableCell>
                  </TableRow>
                  <TableRow
                    v-for="invite in pendingInvitations"
                    :key="`invite-${invite.public_id}`"
                  >
                    <TableCell>
                      <div class="flex items-center gap-3">
                        <div
                          class="grid h-9 w-9 place-items-center rounded-full bg-secondary text-primary"
                        >
                          <MailCheck class="h-4 w-4" aria-hidden="true" />
                        </div>
                        <div>
                          <p class="font-bold">
                            {{
                              employeeForEmail(invite.email)?.display_name ||
                              invite.email
                            }}
                          </p>
                          <p class="mt-0.5 text-xs text-muted-foreground">
                            {{ invite.email }}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell class="capitalize">{{ invite.role }}</TableCell>
                    <TableCell>{{
                      employeeForEmail(invite.email)?.job_title ||
                      "Pending employee"
                    }}</TableCell>
                    <TableCell>
                      <div>
                        <StatusPill value="invited" />
                        <p class="mt-1 text-xs text-muted-foreground">
                          Expires {{ formatDate(invite.expires_at) }}
                        </p>
                      </div>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
            <StatePanel
              v-if="!members.length && !pendingInvitations.length"
              title="No team access records"
              message="Create an employee to send the first secure registration invitation."
            />
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent
        v-for="section in secondarySections"
        :key="section.value"
        :value="section.value"
        class="mt-0"
      >
        <Card class="overflow-hidden"
          ><CardHeader class="border-b"
            ><div class="flex items-start justify-between gap-4">
              <div>
                <CardTitle>{{ section.title }}</CardTitle
                ><CardDescription>{{ section.description }}</CardDescription>
              </div>
              <Badge variant="outline"
                >{{ sectionItems(section.value).length }} total</Badge
              >
            </div></CardHeader
          ><CardContent class="p-0">
            <StatePanel
              v-if="!sectionItems(section.value).length"
              :title="section.emptyTitle"
              :message="section.emptyMessage"
            />
            <div v-else class="divide-y">
              <article
                v-for="item in sectionItems(section.value)"
                :key="item.public_id"
                class="resource-row sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center"
              >
                <div>
                  <p class="font-bold">{{ primary(item, section.value) }}</p>
                  <p class="mt-1 text-sm text-muted-foreground">
                    {{ secondary(item, section.value) }}
                  </p>
                </div>
                <span class="text-sm font-semibold text-muted-foreground">{{
                  detail(item)
                }}</span>
                <div class="flex items-center gap-2">
                  <StatusPill
                    :value="
                      item.status || (item.is_active ? 'active' : 'inactive')
                    "
                  /><Button
                    v-if="
                      section.value === 'leave' && item.status === 'pending'
                    "
                    variant="outline"
                    size="sm"
                    type="button"
                    @click="decideLeave(item, 'approved')"
                    >Approve</Button
                  ><Button
                    v-if="
                      section.value === 'documents' && item.status === 'pending'
                    "
                    variant="outline"
                    size="sm"
                    type="button"
                    @click="reviewDocument(item, 'approved')"
                    >Approve</Button
                  ><Button
                    v-if="section.value === 'terminals'"
                    variant="outline"
                    size="sm"
                    type="button"
                    @click="openTerminalManager(item)"
                    ><Settings2 class="h-3.5 w-3.5" aria-hidden="true" />
                    Manage</Button
                  >
                </div>
              </article>
            </div>
          </CardContent></Card
        >
      </TabsContent>
    </Tabs>

    <Dialog v-model:open="formOpen"
      ><DialogContent class="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <form v-if="view === 'leave'" @submit.prevent="createLeave">
          <DialogHeader
            ><DialogTitle>Record leave request</DialogTitle
            ><DialogDescription
              >Attach a dated leave request to the employee
              record.</DialogDescription
            ></DialogHeader
          >
          <div class="mt-6 space-y-4">
            <StaffSelect
              v-model="leaveForm.staff_public_id"
              :staff="staff"
              input-id="leave-staff"
            />
            <div>
              <label class="field-label" for="leave-type">Type</label
              ><NativeSelect id="leave-type" v-model="leaveForm.leave_type"
                ><option value="vacation">Vacation</option>
                <option value="sick">Sick leave</option>
                <option value="personal">Personal</option>
                <option value="emergency">Emergency</option>
                <option value="unpaid">Unpaid</option></NativeSelect
              >
            </div>
            <div class="grid grid-cols-2 gap-3">
              <label class="field-label"
                >Starts<Input
                  v-model="leaveForm.start_date"
                  class="mt-1"
                  type="date"
                  required /></label
              ><label class="field-label"
                >Ends<Input
                  v-model="leaveForm.end_date"
                  class="mt-1"
                  type="date"
                  required
              /></label>
            </div>
            <div>
              <label class="field-label" for="leave-reason">Reason</label
              ><Textarea
                id="leave-reason"
                v-model.trim="leaveForm.reason"
                class="min-h-24"
                required
              />
            </div>
          </div>
          <DialogFooter class="mt-6"
            ><Button variant="outline" type="button" @click="formOpen = false"
              >Cancel</Button
            ><Button :disabled="saving">Save request</Button></DialogFooter
          >
        </form>
        <form v-else-if="view === 'documents'" @submit.prevent="uploadDocument">
          <DialogHeader
            ><DialogTitle>Upload employee document</DialogTitle
            ><DialogDescription
              >PDF, JPG, and PNG files up to 10 MB are accepted for
              review.</DialogDescription
            ></DialogHeader
          >
          <div class="mt-6 space-y-4">
            <StaffSelect
              v-model="documentForm.staff_public_id"
              :staff="staff"
              input-id="document-staff"
            />
            <div>
              <label class="field-label" for="document-type"
                >Document type</label
              ><NativeSelect
                id="document-type"
                v-model="documentForm.document_type"
                ><option value="identity">Identity</option>
                <option value="contract">Contract</option>
                <option value="certification">Certification</option>
                <option value="permit">Permit</option>
                <option v-if="isRestaurant" value="food_safety">
                  Food safety
                </option>
                <option value="other">Other</option></NativeSelect
              >
            </div>
            <div>
              <label class="field-label" for="document-file">Document</label
              ><Input
                id="document-file"
                type="file"
                accept="application/pdf,image/jpeg,image/png"
                required
                @change="documentForm.file = $event.target.files?.[0]"
              />
            </div>
          </div>
          <DialogFooter class="mt-6"
            ><Button variant="outline" type="button" @click="formOpen = false"
              >Cancel</Button
            ><Button :disabled="saving">Upload for review</Button></DialogFooter
          >
        </form>
        <form v-else @submit.prevent="createTerminal">
          <DialogHeader
            ><DialogTitle>Add attendance terminal</DialogTitle
            ><DialogDescription
              >Create the device here, then open the terminal in a separate tab
              and enter its setup code.</DialogDescription
            ></DialogHeader
          >
          <div class="mt-6 space-y-4">
            <div>
              <label class="field-label" for="terminal-name"
                >Terminal name</label
              ><Input
                id="terminal-name"
                v-model.trim="terminalForm.name"
                required
              />
            </div>
            <div>
              <label class="field-label" for="terminal-location">Location</label
              ><NativeSelect
                id="terminal-location"
                v-model="terminalForm.location_public_id"
                ><option value="">No fixed location</option>
                <option
                  v-for="location in locations"
                  :key="location.public_id"
                  :value="location.public_id"
                >
                  {{ location.name }}
                </option></NativeSelect
              >
            </div>
          </div>
          <DialogFooter class="mt-6"
            ><Button variant="outline" type="button" @click="formOpen = false"
              >Cancel</Button
            ><Button :disabled="saving">Create terminal</Button></DialogFooter
          >
        </form>
      </DialogContent></Dialog
    >

    <Dialog v-model:open="terminalManagerOpen">
      <DialogContent class="sm:max-w-3xl">
        <DialogHeader>
          <div
            class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
          >
            <ContactRound class="h-5 w-5" aria-hidden="true" />
          </div>
          <DialogTitle>Manage {{ terminalTarget?.name }}</DialogTitle>
          <DialogDescription>
            Pair this dedicated attendance screen without exposing workspace
            credentials.
          </DialogDescription>
        </DialogHeader>
        <div
          class="mt-6 grid overflow-hidden rounded-xl border md:grid-cols-[minmax(0,1fr)_20rem]"
        >
          <div class="border-b p-5 md:border-b-0 md:border-r">
            <h3 class="font-extrabold">How terminal setup works</h3>
            <ol class="mt-5 space-y-5">
              <li
                v-for="(step, index) in terminalSteps"
                :key="step.title"
                class="flex gap-3"
              >
                <span
                  class="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-secondary text-sm font-extrabold text-primary tabular-nums"
                >
                  {{ index + 1 }}
                </span>
                <div>
                  <p class="text-sm font-bold">{{ step.title }}</p>
                  <p class="mt-1 text-xs leading-5 text-muted-foreground">
                    {{ step.description }}
                  </p>
                </div>
              </li>
            </ol>
          </div>
          <aside class="bg-muted/25 p-5">
            <div class="flex items-center gap-3">
              <div
                class="grid h-10 w-10 place-items-center rounded-xl bg-background text-primary"
              >
                <KeyRound class="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <h3 class="font-extrabold">Pair this terminal</h3>
                <p class="text-xs text-muted-foreground">
                  Single-use setup code
                </p>
              </div>
            </div>
            <div class="mt-5 rounded-xl border bg-background p-5">
              <p
                v-if="pairingLoading"
                class="py-5 text-center text-sm text-muted-foreground"
              >
                Checking current code…
              </p>
              <div v-else-if="pairingCode">
                <PairingCodeDisplay
                  class="justify-center"
                  :code="pairingCode"
                />
                <p
                  class="mt-4 text-center text-xs leading-5 text-muted-foreground"
                >
                  This code stays available until it is used or replaced.
                </p>
              </div>
              <div v-else class="py-4 text-center">
                <KeyRound
                  class="mx-auto h-7 w-7 text-muted-foreground/55"
                  aria-hidden="true"
                />
                <p class="mt-3 font-extrabold">No active code</p>
                <p class="mt-1 text-xs leading-5 text-muted-foreground">
                  Generate one when the terminal screen is ready.
                </p>
              </div>
            </div>
            <div class="mt-3 grid gap-2">
              <Button
                v-if="pairingCode"
                variant="outline"
                type="button"
                @click="copyPairingCode"
              >
                <Copy class="h-4 w-4" aria-hidden="true" />
                Copy code
              </Button>
              <Button
                variant="outline"
                type="button"
                :disabled="generatingCode"
                @click="generatePairingCode"
              >
                <RefreshCw class="h-4 w-4" aria-hidden="true" />
                {{
                  generatingCode
                    ? "Generating…"
                    : pairingCode
                      ? "Replace code"
                      : "Generate code"
                }}
              </Button>
              <ButtonAnchor
                href="/attendance-terminal"
                target="_blank"
                rel="noopener"
              >
                <ExternalLink class="h-4 w-4" aria-hidden="true" />
                Open attendance terminal
              </ButtonAnchor>
            </div>
          </aside>
        </div>
      </DialogContent>
    </Dialog>
  </section>
</template>

<script setup>
import {
  AlertTriangle,
  Clock3,
  ContactRound,
  Copy,
  ExternalLink,
  KeyRound,
  MailCheck,
  Plus,
  RefreshCw,
  Settings2,
  UserCheck,
  UserPlus,
  UsersRound,
} from "lucide-vue-next";
import { toast } from "@/components/ui/toast";

const route = useRoute();
const router = useRouter();
const business = useBusinessStore();
const { apiFetch } = useApiClient();
const tabs = [
  { label: "Employees", value: "staff" },
  { label: "Team access", value: "access" },
  { label: "Employee tracker", value: "attendance" },
  { label: "Leave", value: "leave" },
  { label: "Documents", value: "documents" },
  { label: "Attendance flags", value: "flags" },
  { label: "Terminals", value: "terminals" },
];
const secondarySections = [
  {
    value: "leave",
    title: "Leave requests",
    description: "Requested dates and manager decisions.",
    emptyTitle: "No leave requests",
    emptyMessage:
      "New requests will remain attached to the employee audit trail.",
  },
  {
    value: "documents",
    title: "Employee documents",
    description: "Identity, contract, certification, permit, and other files.",
    emptyTitle: "No employee documents",
    emptyMessage:
      "Upload a document when one needs review or secure retention.",
  },
  {
    value: "flags",
    title: "Attendance flags",
    description: "Repeated lateness and other exceptions requiring review.",
    emptyTitle: "No attendance flags",
    emptyMessage:
      "No tracked attendance pattern currently needs manager attention.",
  },
  {
    value: "terminals",
    title: "Attendance terminals",
    description: "Location-scoped devices for employee code and PIN clocking.",
    emptyTitle: "No attendance terminals",
    emptyMessage:
      "Create a terminal and open the dedicated screen on the clock-in device.",
  },
];
const view = computed(() =>
  tabs.some((tab) => tab.value === route.query.view)
    ? String(route.query.view)
    : "staff",
);
const isRestaurant = computed(
  () => business.activeBusiness?.industry_preset === "restaurant",
);
const staff = ref([]);
const members = ref([]);
const invitations = ref([]);
const attendance = ref([]);
const leaveRequests = ref([]);
const documents = ref([]);
const flags = ref([]);
const terminals = ref([]);
const locations = ref([]);
const loading = ref(true);
const error = ref("");
const saving = ref(false);
const formOpen = ref(false);
const terminalManagerOpen = ref(false);
const terminalTarget = ref(null);
const pairingCode = ref("");
const pairingLoading = ref(false);
const generatingCode = ref(false);
const leaveForm = reactive({
  staff_public_id: "",
  leave_type: "vacation",
  start_date: "",
  end_date: "",
  reason: "",
  status: "pending",
});
const documentForm = reactive({
  staff_public_id: "",
  document_type: "identity",
  file: null,
});
const terminalForm = reactive({
  name: "",
  location_public_id: "",
  device_type: "attendance",
  configuration: {},
  is_active: true,
});
const terminalSteps = [
  {
    title: "Create the terminal",
    description:
      "Give the shared screen a recognizable name and optional location.",
  },
  {
    title: "Generate one code",
    description:
      "The current code remains visible here until it is used or deliberately replaced.",
  },
  {
    title: "Open and pair",
    description:
      "Open the dedicated terminal on the target device and enter all eight characters.",
  },
];
const pendingInvitations = computed(() =>
  invitations.value.filter((item) => item.status === "pending"),
);
const today = () => new Date().toISOString().slice(0, 10);
const metrics = computed(() => [
  {
    label: "Active employees",
    value: staff.value.filter((item) => item.employment_status === "active")
      .length,
    detail: `${staff.value.filter((item) => item.is_bookable).length} bookable`,
    icon: UsersRound,
  },
  {
    label: "Clocked in now",
    value: attendance.value.filter((item) => item.clock_in && !item.clock_out)
      .length,
    detail: "Open attendance records",
    icon: Clock3,
  },
  {
    label: "Late today",
    value: attendance.value.filter(
      (item) =>
        item.clock_in?.slice(0, 10) === today() && item.late_minutes > 0,
    ).length,
    detail: "Recorded late arrivals",
    icon: AlertTriangle,
  },
  {
    label: "Pending approvals",
    value:
      staff.value.filter((item) => item.employment_status === "pending")
        .length +
      leaveRequests.value.filter((item) => item.status === "pending").length +
      pendingInvitations.value.length,
    detail: "Employees, access, and leave",
    icon: UserCheck,
  },
]);

watch(() => business.activeBusiness?.public_id, load);
onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses();
  await load();
});
async function setView(value) {
  formOpen.value = false;
  await router.push({ query: value === "staff" ? {} : { view: value } });
}
async function load() {
  if (!business.activeBusiness) return;
  loading.value = true;
  error.value = "";
  try {
    const id = business.activeBusiness.public_id;
    const [
      staffResponse,
      memberResponse,
      invitationResponse,
      attendanceResponse,
      leaveResponse,
      documentResponse,
      flagResponse,
      deviceResponse,
      locationResponse,
    ] = await Promise.all([
      apiFetch(`businesses/${id}/staff/`),
      apiFetch(`businesses/${id}/members/`),
      apiFetch(`businesses/${id}/team/invitations/`),
      apiFetch(`businesses/${id}/workforce/attendance/`),
      apiFetch(`businesses/${id}/workforce/leave-requests/`),
      apiFetch(`businesses/${id}/workforce/documents/`),
      apiFetch(`businesses/${id}/workforce/attendance-flags/`),
      apiFetch(`businesses/${id}/devices/`),
      apiFetch(`businesses/${id}/locations/`),
    ]);
    staff.value = staffResponse.results || [];
    members.value = memberResponse || [];
    invitations.value = invitationResponse.results || [];
    attendance.value = attendanceResponse.results || [];
    leaveRequests.value = leaveResponse.results || [];
    documents.value = documentResponse.results || [];
    flags.value = flagResponse.results || [];
    terminals.value = (deviceResponse.results || []).filter(
      (item) => item.device_type === "attendance",
    );
    locations.value = locationResponse.results || [];
    leaveForm.staff_public_id ||= staff.value[0]?.public_id || "";
    documentForm.staff_public_id ||= staff.value[0]?.public_id || "";
  } catch (requestError) {
    error.value =
      requestError?.data?.error?.message || "Could not load workforce records.";
  } finally {
    loading.value = false;
  }
}
function sectionItems(value) {
  return (
    {
      leave: leaveRequests.value,
      documents: documents.value,
      flags: flags.value,
      terminals: terminals.value,
    }[value] || []
  );
}
async function createLeave() {
  await createResource(
    "workforce/leave-requests",
    leaveForm,
    leaveRequests,
    "Leave request saved",
  );
}
async function uploadDocument() {
  saving.value = true;
  try {
    const body = new FormData();
    body.append("staff_public_id", documentForm.staff_public_id);
    body.append("document_type", documentForm.document_type);
    body.append("file", documentForm.file);
    documents.value.unshift(
      await apiFetch(
        `businesses/${business.activeBusiness.public_id}/workforce/documents/`,
        { method: "POST", body },
      ),
    );
    formOpen.value = false;
    toast({
      title: "Document uploaded",
      description: "The employee document is ready for review.",
    });
  } catch (requestError) {
    failedToast(requestError);
  } finally {
    saving.value = false;
  }
}
async function createTerminal() {
  saving.value = true;
  try {
    const terminal = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/`,
      { method: "POST", body: terminalForm },
    );
    terminals.value.unshift(terminal);
    formOpen.value = false;
    toast({
      title: "Attendance terminal created",
      description: `${terminal.name} is ready to configure and pair.`,
    });
    await openTerminalManager(terminal);
  } catch (requestError) {
    failedToast(requestError);
  } finally {
    saving.value = false;
  }
}
async function createResource(path, body, target, title) {
  saving.value = true;
  try {
    target.value.unshift(
      await apiFetch(
        `businesses/${business.activeBusiness.public_id}/${path}/`,
        { method: "POST", body },
      ),
    );
    formOpen.value = false;
    toast({
      title,
      description: "The workforce record was updated successfully.",
    });
  } catch (requestError) {
    failedToast(requestError);
  } finally {
    saving.value = false;
  }
}
async function approveStaff(item) {
  try {
    Object.assign(
      item,
      await apiFetch(
        `businesses/${business.activeBusiness.public_id}/staff/${item.public_id}/`,
        {
          method: "PATCH",
          body: { employment_status: "active", is_active: true },
        },
      ),
    );
    toast({
      title: "Employee approved",
      description: `${item.display_name} is now active.`,
    });
  } catch (requestError) {
    failedToast(requestError);
  }
}
async function openTerminalManager(item) {
  terminalTarget.value = item;
  pairingCode.value = "";
  pairingLoading.value = true;
  terminalManagerOpen.value = true;
  try {
    const response = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/${item.public_id}/pairing-code/`,
    );
    pairingCode.value = response.pairing_code || "";
  } catch (requestError) {
    failedToast(requestError);
  } finally {
    pairingLoading.value = false;
  }
}
async function generatePairingCode() {
  if (!terminalTarget.value || generatingCode.value) return;
  generatingCode.value = true;
  try {
    const response = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/${terminalTarget.value.public_id}/pairing-code/`,
      { method: "POST" },
    );
    pairingCode.value = response.pairing_code;
    toast({
      title: "Setup code generated",
      description: `Enter it on ${terminalTarget.value.name}.`,
    });
  } catch (requestError) {
    failedToast(requestError);
  } finally {
    generatingCode.value = false;
  }
}
async function copyPairingCode() {
  await navigator.clipboard.writeText(pairingCode.value);
  toast({
    title: "Setup code copied",
    description: `Paste it into ${terminalTarget.value?.name}.`,
  });
}
async function decideLeave(item, status) {
  try {
    Object.assign(
      item,
      await apiFetch(
        `businesses/${business.activeBusiness.public_id}/workforce/leave-requests/${item.public_id}/`,
        { method: "PATCH", body: { status } },
      ),
    );
    toast({
      title: "Leave request approved",
      description: `${item.staff_name}'s request was updated.`,
    });
  } catch (requestError) {
    failedToast(requestError);
  }
}
async function reviewDocument(item, status) {
  try {
    Object.assign(
      item,
      await apiFetch(
        `businesses/${business.activeBusiness.public_id}/workforce/documents/${item.public_id}/review/`,
        { method: "POST", body: { status } },
      ),
    );
    toast({
      title: "Document approved",
      description: `${item.original_name} passed review.`,
    });
  } catch (requestError) {
    failedToast(requestError);
  }
}
function failedToast(requestError) {
  toast({
    title: "Workforce update failed",
    description:
      requestError?.data?.error?.message || "Check the details and try again.",
    variant: "destructive",
  });
}
function primary(item, section) {
  if (section === "terminals") return item.name;
  return (
    item.staff_name || item.original_name || item.summary || "Workforce record"
  );
}
function secondary(item, section) {
  if (section === "leave")
    return `${item.leave_type.replaceAll("_", " ")} · ${item.start_date} to ${item.end_date}`;
  if (section === "documents") return item.document_type.replaceAll("_", " ");
  if (section === "terminals")
    return item.last_seen_at
      ? `Last seen ${formatDate(item.last_seen_at)}`
      : "Not paired yet";
  return item.flag_type?.replaceAll("_", " ") || "";
}
function detail(item) {
  if (item.occurrence_count) return `${item.occurrence_count} occurrences`;
  if (item.updated_at) return formatDate(item.updated_at);
  if (item.uploaded_at) return formatDate(item.uploaded_at);
  return "";
}
function employeeForEmail(email) {
  return staff.value.find(
    (item) => item.email?.toLowerCase() === email?.toLowerCase(),
  );
}
function initials(name = "") {
  return (
    name
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0])
      .join("")
      .toUpperCase() || "PC"
  );
}
function shortTime(value) {
  return new Intl.DateTimeFormat("en-PH", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(`2000-01-01T${value}`));
}
function formatDate(value) {
  return new Intl.DateTimeFormat("en-PH", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
</script>
