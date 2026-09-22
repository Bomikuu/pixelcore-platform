<template>
  <main class="min-h-dvh w-full min-w-0 bg-muted/35 text-foreground">
    <DevicePairingPanel
      v-if="state === 'unpaired'"
      v-model="pairingCode"
      title="Employee attendance"
      description="A focused clock-in screen for any business with a tracked workforce."
      :details="[
        'Employees generate an action code from their own portal.',
        'Each code works once for either clock-in or clock-out.',
        'Attendance records update Workforce immediately.',
      ]"
      audience="Employees at this location"
      action-label="Pair attendance terminal"
      setup-source="Operate → Workforce → Terminals"
      :working="working"
      :message="message"
      :icon="ContactRound"
      @submit="pair"
    />

    <section
      v-else-if="state === 'loading'"
      class="mx-auto flex min-h-dvh max-w-2xl items-center px-5 py-12"
    >
      <StatePanel
        class="w-full border bg-card shadow-sm"
        kind="loading"
        title="Opening attendance terminal"
        message="Validating the saved device session and business location."
      />
    </section>

    <section
      v-else-if="state === 'error'"
      class="fixed inset-0 z-50 grid min-h-dvh place-items-center bg-background px-5 py-10"
    >
      <StatePanel
        class="w-full max-w-2xl border bg-card shadow-xl"
        kind="error"
        title="Attendance terminal needs attention"
        :message="message"
      >
        <div class="mt-5 flex flex-wrap gap-2">
          <Button type="button" :disabled="working" @click="loadSession">
            <RefreshCw class="h-4 w-4" aria-hidden="true" />
            Reconnect
          </Button>
          <Button variant="outline" type="button" @click="unpair">
            <Unplug class="h-4 w-4" aria-hidden="true" />
            Use another setup code
          </Button>
        </div>
      </StatePanel>
    </section>

    <section
      v-else
      class="flex min-h-dvh w-full min-w-0 items-center justify-center px-4 py-6 sm:px-6 sm:py-10"
    >
      <div class="w-full min-w-0 max-w-5xl overflow-hidden rounded-xl border bg-card md:flex">
        <aside class="min-w-0 border-b bg-secondary/40 p-5 sm:p-8 md:w-2/5 md:shrink-0 md:border-b-0 md:border-r">
          <div class="flex items-center gap-3">
            <Avatar class="h-12 w-12 shrink-0 border">
              <AvatarImage
                v-if="session.business.logo_url"
                :src="session.business.logo_url"
                :alt="`${session.business.display_name} logo`"
              />
              <AvatarFallback class="bg-background font-bold text-primary">
                {{ businessInitials }}
              </AvatarFallback>
            </Avatar>
            <div class="min-w-0">
              <p class="break-words font-bold">{{ session.business.display_name }}</p>
              <p class="mt-1 text-sm text-muted-foreground">
                {{ session.device.location_name }}
              </p>
            </div>
          </div>

          <div class="my-6 border-y py-6 sm:my-8 sm:py-8">
            <p class="text-3xl font-bold tracking-tight tabular-nums sm:text-4xl">
              {{ currentTime }}
            </p>
            <p class="mt-2 text-sm leading-6 text-muted-foreground">
              {{ currentDate }}
            </p>
            <p class="mt-4 flex items-start gap-2 text-xs font-semibold text-primary">
              <span class="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" aria-hidden="true" />
              <span class="break-words">{{ session.device.name }} · Connected</span>
            </p>
          </div>

          <div class="hidden md:block">
            <h2 class="flex items-center gap-2 text-sm font-bold">
              <CircleHelp class="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
              From your portal to your workday
            </h2>
            <ol class="mt-5 space-y-4">
              <li v-for="(step, index) in steps" :key="step" class="flex items-start gap-3">
                <span class="grid h-6 w-6 shrink-0 place-items-center rounded-full border bg-background text-xs font-bold text-primary">
                  {{ index + 1 }}
                </span>
                <p class="text-sm leading-6 text-muted-foreground">{{ step }}</p>
              </li>
            </ol>
          </div>

          <Button
            variant="ghost"
            class="mt-4 h-auto max-w-full justify-start gap-2 whitespace-normal px-0 text-xs text-muted-foreground md:mt-8"
            type="button"
            @click="unpair"
          >
            <Unplug class="h-4 w-4 shrink-0" aria-hidden="true" />
            Disconnect terminal
          </Button>
        </aside>

        <div class="flex min-w-0 flex-1 items-center justify-center p-5 sm:p-8 lg:p-10">
          <form class="w-full min-w-0 max-w-sm space-y-6" @submit.prevent="submitCode">
            <div class="text-center">
              <div class="mx-auto mb-4 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary">
                <ScanLine class="h-5 w-5" aria-hidden="true" />
              </div>
              <h1 class="text-2xl font-bold tracking-tight">Record your attendance</h1>
              <p class="mt-2 text-sm leading-6 text-muted-foreground">
                Enter the clock-in or clock-out code from your employee portal.
              </p>
            </div>

            <div class="space-y-3">
              <CodeInput
                v-model="attendanceCode"
                class="min-w-0"
                input-class="h-12 w-0 min-w-0 text-xl sm:h-14"
                :length="6"
                numeric-only
                label="One-use attendance code"
                :disabled="working"
              />
              <p class="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <ShieldCheck class="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                Single use · Valid for five minutes
              </p>
            </div>

            <div class="grid grid-cols-3 gap-2" aria-label="Attendance code keypad">
              <Button
                v-for="key in keypad"
                :key="key"
                variant="outline"
                class="h-12 min-w-0 text-lg font-semibold tabular-nums sm:h-14"
                type="button"
                :aria-label="keyLabel(key)"
                :disabled="working"
                @click="pressKey(key)"
              >
                <Delete v-if="key === 'backspace'" class="h-5 w-5" aria-hidden="true" />
                <span v-else :class="key === 'clear' ? 'text-xs font-semibold' : ''">
                  {{ key === "clear" ? "Clear" : key }}
                </span>
              </Button>
            </div>

            <Alert
              v-if="message"
              class="break-words"
              :variant="messageTone === 'error' ? 'destructive' : 'default'"
            >
              <AlertCircle v-if="messageTone === 'error'" class="h-4 w-4" aria-hidden="true" />
              <CheckCircle2 v-else class="h-4 w-4" aria-hidden="true" />
              <AlertTitle>
                {{ messageTone === "error" ? "Attendance not recorded" : "Attendance recorded" }}
              </AlertTitle>
              <AlertDescription>{{ message }}</AlertDescription>
            </Alert>

            <Button
              class="h-12 w-full gap-2"
              type="submit"
              :disabled="working || attendanceCode.length !== 6"
            >
              <CheckCircle2 class="h-4 w-4 shrink-0" aria-hidden="true" />
              {{ working ? "Checking code…" : "Confirm attendance" }}
            </Button>
          </form>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import {
  AlertCircle,
  CheckCircle2,
  CircleHelp,
  ContactRound,
  Delete,
  RefreshCw,
  ScanLine,
  ShieldCheck,
  Unplug,
} from "lucide-vue-next";

definePageMeta({ layout: "storefront" });

const config = useRuntimeConfig();
const state = ref("loading");
const working = ref(false);
const deviceToken = ref("");
const pairingCode = ref("");
const attendanceCode = ref("");
const message = ref("");
const messageTone = ref("info");
const session = ref({ business: {}, device: {} });
const currentTime = ref("");
const currentDate = ref("");
let clockTimer;

const keypad = [
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "clear",
  "0",
  "backspace",
];

const steps = [
  "Sign in to your employee portal on your own device.",
  "Choose clock in or clock out and generate the code.",
  "Enter that code here to record the attendance action.",
];

const businessInitials = computed(() => {
  return String(session.value.business?.display_name || "PC")
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
});

onMounted(() => {
  deviceToken.value = localStorage.getItem("pixelcore_attendance_token") || "";
  updateClock();
  clockTimer = window.setInterval(updateClock, 1000);
  if (deviceToken.value) loadSession();
  else state.value = "unpaired";
});

onBeforeUnmount(() => window.clearInterval(clockTimer));

async function pair() {
  if (working.value || pairingCode.value.length !== 8) return;
  working.value = true;
  message.value = "";
  try {
    const response = await $fetch("devices/pair/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      body: {
        pairing_code: pairingCode.value,
        device_type: "attendance",
      },
    });
    deviceToken.value = response.device_token;
    localStorage.setItem("pixelcore_attendance_token", response.device_token);
    await loadSession();
  } catch (error) {
    message.value = error?.data?.error?.message || "This setup code could not pair the terminal.";
  } finally {
    working.value = false;
  }
}

async function loadSession() {
  if (!deviceToken.value) {
    state.value = "unpaired";
    return;
  }
  state.value = "loading";
  working.value = true;
  message.value = "";
  try {
    session.value = await $fetch("devices/attendance/", {
      baseURL: config.public.apiBaseUrl,
      headers: deviceHeaders(),
    });
    updateClock();
    state.value = "ready";
  } catch (error) {
    message.value = error?.data?.error?.message || "PixelCore could not reconnect this terminal.";
    state.value = "error";
  } finally {
    working.value = false;
  }
}

async function submitCode() {
  if (attendanceCode.value.length !== 6 || working.value) return;
  working.value = true;
  message.value = "";
  try {
    const response = await $fetch("devices/attendance/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      headers: deviceHeaders(),
      body: { code: attendanceCode.value },
    });
    message.value = actionMessage(response);
    messageTone.value = "success";
    attendanceCode.value = "";
  } catch (error) {
    if (error?.response?.status === 403 && error?.data?.error?.code === "DEVICE_ACCESS_DENIED") {
      message.value = error.data.error.message;
      state.value = "error";
    } else {
      message.value = error?.data?.error?.message || "Attendance could not be recorded.";
      messageTone.value = "error";
      attendanceCode.value = "";
    }
  } finally {
    working.value = false;
  }
}

function pressKey(key) {
  if (key === "clear") {
    attendanceCode.value = "";
    return;
  }
  if (key === "backspace") {
    attendanceCode.value = attendanceCode.value.slice(0, -1);
    return;
  }
  if (attendanceCode.value.length < 6) attendanceCode.value += key;
}

function keyLabel(key) {
  if (key === "backspace") return "Delete last code digit";
  if (key === "clear") return "Clear attendance code";
  return `Enter ${key}`;
}

function unpair() {
  localStorage.removeItem("pixelcore_attendance_token");
  deviceToken.value = "";
  pairingCode.value = "";
  attendanceCode.value = "";
  message.value = "";
  state.value = "unpaired";
}

function deviceHeaders() {
  return { "X-Device-Token": deviceToken.value };
}

function updateClock() {
  const now = new Date();
  const timeZone = session.value.business?.timezone || undefined;
  currentTime.value = new Intl.DateTimeFormat("en-PH", {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
    timeZone,
  }).format(now);
  currentDate.value = new Intl.DateTimeFormat("en-PH", {
    dateStyle: "full",
    timeZone,
  }).format(now);
}

function actionMessage(response) {
  const timestamp = response.action === "clock_out"
    ? response.record.clock_out
    : response.record.clock_in;
  const action = response.action === "clock_out" ? "Clock-out" : "Clock-in";
  const time = new Date(timestamp).toLocaleTimeString("en-PH", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${action} recorded for ${response.employee_name} at ${time}.`;
}
</script>
