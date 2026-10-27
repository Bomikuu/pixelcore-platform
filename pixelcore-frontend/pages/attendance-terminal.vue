<template>
  <main class="attendance-terminal min-h-dvh w-full min-w-0 bg-slate-50 text-foreground dark:bg-background">
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
      illustration="attendance"
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
      class="flex min-h-dvh w-full min-w-0 items-center justify-center px-3 py-4 sm:px-6 sm:py-10"
    >
      <div
        class="terminal-shell grid w-full min-w-0 max-w-[1232px] overflow-hidden rounded-2xl bg-card md:min-h-[780px] md:grid-cols-[minmax(0,0.39fr)_minmax(0,0.61fr)]"
      >
        <aside class="relative flex min-w-0 flex-col border-b bg-secondary/20 p-5 sm:p-8 md:border-b-0 md:border-r md:pb-0 lg:px-10">
          <div class="flex items-center gap-3">
            <Avatar class="h-14 w-14 shrink-0 border border-primary/10">
              <AvatarImage
                v-if="session.business.logo_url"
                :src="session.business.logo_url"
                :alt="`${session.business.display_name} logo`"
              />
              <AvatarFallback class="bg-secondary/60 font-bold text-primary">
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

          <div class="my-5 border-y py-5 md:my-6 md:py-7">
            <p class="whitespace-nowrap text-3xl font-extrabold tracking-tight tabular-nums lg:text-[2.65rem] lg:leading-tight">
              {{ currentTime }}
            </p>
            <p class="mt-2 text-sm leading-6 text-muted-foreground">
              {{ currentDate }}
            </p>
            <p
              class="mt-4 inline-flex max-w-full items-center gap-3 rounded-full bg-secondary/65 px-4 py-2.5 text-xs font-semibold"
              :title="session.device.name"
            >
              <span class="h-2 w-2 shrink-0 rounded-full bg-primary" aria-hidden="true" />
              <span>Terminal connected</span>
              <Wifi class="ml-3 h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
            </p>
          </div>

          <div class="hidden md:block">
            <h2 class="flex items-center gap-3 text-sm font-bold lg:text-base">
              <CircleHelp class="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
              How to record your attendance
            </h2>
            <ol class="mt-4 space-y-4">
              <li v-for="(step, index) in steps" :key="step" class="flex items-start gap-3">
                <span class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-secondary/65 text-sm font-bold">
                  {{ index + 1 }}
                </span>
                <p class="text-sm leading-6 text-muted-foreground">{{ step }}</p>
              </li>
            </ol>
          </div>

          <div class="relative mt-4 md:-mx-8 md:mt-auto md:min-h-[245px] md:flex-1 lg:-mx-10">
            <img
              src="/images/attendance/terminal-illustration.png"
              alt=""
              width="1586"
              height="992"
              class="pointer-events-none absolute bottom-0 hidden h-auto w-full select-none md:block"
              decoding="async"
            />
            <div class="relative flex flex-wrap items-center gap-2 md:absolute md:inset-x-0 md:bottom-0 md:bg-gradient-to-t md:from-card md:to-transparent md:px-8 md:pb-6 md:pt-12 lg:px-10">
              <Button
                variant="outline"
                class="h-11 max-w-full gap-2 whitespace-normal bg-card/95 text-xs text-muted-foreground"
                type="button"
                :disabled="working"
                @click="unpair"
              >
                <Unplug class="h-4 w-4 shrink-0" aria-hidden="true" />
                Disconnect terminal
              </Button>
              <Button
                variant="ghost"
                size="icon"
                class="h-11 w-11 shrink-0 bg-card/95 text-muted-foreground"
                type="button"
                :aria-label="soundEnabled ? 'Mute attendance sound' : 'Enable attendance sound'"
                :aria-pressed="soundEnabled"
                :title="soundEnabled ? 'Mute attendance sound' : 'Enable attendance sound'"
                @click="toggleSound"
              >
                <Volume2 v-if="soundEnabled" class="h-4 w-4" aria-hidden="true" />
                <VolumeX v-else class="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
        </aside>

        <div class="terminal-workspace relative flex min-w-0 items-center justify-center overflow-hidden px-5 py-8 sm:p-8 lg:px-14 lg:py-12">
          <section
            v-if="confirmation"
            class="relative z-10 flex min-h-[580px] w-full min-w-0 max-w-lg flex-col items-center justify-center text-center"
            aria-label="Attendance confirmation"
          >
            <div role="status" aria-live="polite" aria-atomic="true" class="w-full">
              <div class="terminal-success-mark mx-auto mb-7 grid h-14 w-14 place-items-center rounded-full bg-secondary text-primary">
                <CheckCircle2 class="terminal-success-icon h-7 w-7" aria-hidden="true" />
              </div>
              <Avatar class="mx-auto h-28 w-28 shrink-0 border-4 border-card shadow-sm sm:h-36 sm:w-36">
                <AvatarImage v-if="confirmation.imageUrl" :src="confirmation.imageUrl" alt="" />
                <AvatarFallback class="bg-secondary text-3xl font-bold text-primary sm:text-4xl">
                  {{ confirmation.initials }}
                </AvatarFallback>
              </Avatar>
              <h1
                ref="confirmationHeading"
                tabindex="-1"
                class="mt-7 break-words text-2xl font-bold leading-snug tracking-tight outline-none sm:text-3xl"
              >
                {{ confirmation.message }}
              </h1>
              <p v-if="confirmation.jobTitle" class="mt-3 break-words text-base text-muted-foreground">
                {{ confirmation.jobTitle }}
              </p>
              <p class="mt-6 flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-sm font-semibold text-primary">
                <span>{{ confirmation.actionLabel }}</span>
                <time v-if="confirmation.time" :datetime="confirmation.timestamp">
                  at {{ confirmation.time }}
                </time>
              </p>
            </div>
            <div class="mt-12 w-full max-w-xs" aria-hidden="true">
              <p class="text-sm text-muted-foreground">
                Returning to terminal in {{ secondsRemaining }} {{ secondsRemaining === 1 ? 'second' : 'seconds' }}…
              </p>
              <div class="mt-4 h-1 overflow-hidden rounded-full bg-secondary">
                <div class="h-full rounded-full bg-primary" :style="{ width: `${secondsRemaining / 5 * 100}%` }" />
              </div>
            </div>
            <p class="sr-only">This profile will close automatically after five seconds.</p>
          </section>

          <form
            v-else
            class="relative z-10 w-full min-w-0 max-w-lg space-y-6"
            novalidate
            :aria-busy="working"
            @submit.prevent="submitCode"
          >
            <div class="text-center">
              <div class="mx-auto mb-6 grid h-14 w-14 place-items-center rounded-xl bg-secondary/70 text-primary">
                <ScanLine class="h-6 w-6" aria-hidden="true" />
              </div>
              <h1 class="text-2xl font-bold tracking-tight lg:text-[1.75rem]">Record your attendance</h1>
              <p class="mt-2 text-sm leading-6 text-muted-foreground">
                Enter the clock-in or clock-out code from your employee portal.
              </p>
            </div>

            <div class="space-y-3">
              <CodeInput
                ref="codeInput"
                v-model="attendanceCode"
                class="min-w-0"
                input-class="h-12 w-0 min-w-0 rounded-xl bg-muted/15 font-sans text-xl font-semibold sm:h-16 lg:h-[68px]"
                :length="6"
                numeric-only
                label="One-use attendance code"
                :aria-invalid="messageTone === 'error' && !!message"
                :aria-describedby="message ? 'attendance-code-help attendance-code-error' : 'attendance-code-help'"
                :disabled="working"
              />
              <p id="attendance-code-help" class="flex items-center justify-center gap-2 text-xs text-muted-foreground">
                <ShieldCheck class="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                Single use · Valid for five minutes
              </p>
            </div>

            <div class="grid grid-cols-3 gap-2.5" role="group" aria-label="Attendance code keypad">
              <Button
                v-for="key in keypad"
                :key="key"
                variant="outline"
                class="terminal-key h-14 min-w-0 rounded-xl bg-muted/15 text-xl font-semibold tabular-nums sm:h-16"
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
              id="attendance-code-error"
              class="break-words"
              variant="destructive"
            >
              <AlertCircle class="h-4 w-4" aria-hidden="true" />
              <AlertTitle>Attendance not recorded</AlertTitle>
              <AlertDescription>{{ message }}</AlertDescription>
            </Alert>

            <Button
              class="h-14 w-full gap-3 rounded-xl text-base font-semibold sm:h-16"
              type="submit"
              :disabled="working || attendanceCode.length !== 6"
            >
              <LoaderCircle
                v-if="working"
                class="h-5 w-5 shrink-0 animate-spin motion-reduce:animate-none"
                aria-hidden="true"
              />
              <CircleArrowRight v-else class="h-5 w-5 shrink-0" aria-hidden="true" />
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
  CircleArrowRight,
  CircleHelp,
  Delete,
  LoaderCircle,
  RefreshCw,
  ScanLine,
  ShieldCheck,
  Unplug,
  Volume2,
  VolumeX,
  Wifi,
} from "lucide-vue-next";
import { useAttendanceConfirmation } from "@/composables/useAttendanceConfirmation";

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
const codeInput = ref(null);
const confirmationHeading = ref(null);
const soundEnabled = ref(true);
const {
  confirmation,
  secondsRemaining,
  showConfirmation,
  clearConfirmation,
} = useAttendanceConfirmation(focusCode);
let clockTimer;
let attendanceRequest;
let successAudio;
let disposed = false;

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
  "Sign in to your employee portal on your device.",
  "Choose Clock In or Clock Out and generate the code.",
  "Enter the code here to record your attendance.",
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
  soundEnabled.value = localStorage.getItem("pixelcore_attendance_sound") !== "off";
  updateClock();
  clockTimer = window.setInterval(updateClock, 1000);
  if (deviceToken.value) loadSession();
  else state.value = "unpaired";
});

onBeforeUnmount(() => {
  disposed = true;
  window.clearInterval(clockTimer);
  attendanceRequest?.abort();
  closeSuccessAudio();
});

function prepareSuccessAudio() {
  if (!soundEnabled.value || disposed) return;
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    if (!successAudio || successAudio.state === "closed") successAudio = new AudioContext();
    // Unlock audio during the submit gesture, before waiting for the attendance API.
    if (successAudio.state === "suspended") void successAudio.resume().catch(() => {});
  } catch {
    // Audio availability must never prevent an attendance action.
  }
}

function playSuccessSound() {
  if (!soundEnabled.value || disposed || successAudio?.state !== "running") return;
  try {
    const context = successAudio;
    const start = context.currentTime;
    for (const [frequency, delay] of [[740, 0], [988, 0.12]]) {
      const oscillator = context.createOscillator();
      const envelope = context.createGain();
      const noteStart = start + delay;
      oscillator.type = "sine";
      oscillator.frequency.value = frequency;
      envelope.gain.setValueAtTime(0, noteStart);
      envelope.gain.linearRampToValueAtTime(0.065, noteStart + 0.015);
      envelope.gain.exponentialRampToValueAtTime(0.001, noteStart + 0.24);
      oscillator.connect(envelope);
      envelope.connect(context.destination);
      oscillator.onended = () => {
        oscillator.disconnect();
        envelope.disconnect();
      };
      oscillator.start(noteStart);
      oscillator.stop(noteStart + 0.26);
    }
  } catch {
    // The recorded confirmation remains successful when sound cannot play.
  }
}

function closeSuccessAudio() {
  if (successAudio && successAudio.state !== "closed") void successAudio.close().catch(() => {});
  successAudio = undefined;
}

function toggleSound() {
  soundEnabled.value = !soundEnabled.value;
  if (soundEnabled.value) prepareSuccessAudio();
  else closeSuccessAudio();
  try {
    localStorage.setItem("pixelcore_attendance_sound", soundEnabled.value ? "on" : "off");
  } catch {
    // Retain the preference for this session if browser storage is unavailable.
  }
}

async function focusCode() {
  await nextTick();
  if (!disposed && state.value === "ready" && !confirmation.value) {
    codeInput.value?.focus();
  }
}

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
  clearConfirmation();
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
    await focusCode();
  }
}

async function submitCode() {
  if (attendanceCode.value.length !== 6 || working.value || confirmation.value) return;
  prepareSuccessAudio();
  working.value = true;
  message.value = "";
  const request = new AbortController();
  attendanceRequest = request;
  try {
    const response = await $fetch("devices/attendance/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      signal: request.signal,
      headers: deviceHeaders(),
      body: { code: attendanceCode.value },
    });
    if (request.signal.aborted) return;
    attendanceCode.value = "";
    showConfirmation(response, session.value.business?.timezone || undefined);
    playSuccessSound();
    await nextTick();
    confirmationHeading.value?.focus();
  } catch (error) {
    if (request.signal.aborted) return;
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
    if (!confirmation.value) await focusCode();
  }
}

function pressKey(key) {
  if (working.value || confirmation.value) return;
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
  attendanceRequest?.abort();
  closeSuccessAudio();
  clearConfirmation();
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
</script>

<style scoped>
.terminal-shell {
  box-shadow: 0 14px 48px -20px hsl(var(--foreground) / 0.2), 0 2px 8px -4px hsl(var(--foreground) / 0.08);
}

.terminal-workspace::before {
  position: absolute;
  right: -19rem;
  bottom: -5rem;
  width: 35rem;
  height: 43rem;
  border: 4rem solid hsl(var(--secondary) / 0.25);
  border-radius: 50%;
  transform: rotate(35deg);
  content: "";
  pointer-events: none;
}

.terminal-key {
  box-shadow: 0 3px 4px -2px hsl(var(--foreground) / 0.16);
}

.terminal-key:active {
  box-shadow: none;
}

@media (prefers-reduced-motion: no-preference) {
  .terminal-success-mark {
    animation: terminal-success-pulse 560ms cubic-bezier(0.16, 1, 0.3, 1) both;
  }

  .terminal-success-icon :deep(circle) {
    --terminal-stroke-length: 64;
    stroke-dasharray: 64;
    animation: terminal-success-draw 340ms cubic-bezier(0.16, 1, 0.3, 1) both;
  }

  .terminal-success-icon :deep(path) {
    --terminal-stroke-length: 16;
    stroke-dasharray: 16;
    animation: terminal-success-draw 280ms 140ms cubic-bezier(0.16, 1, 0.3, 1) both;
  }
}

@keyframes terminal-success-draw {
  from { stroke-dashoffset: var(--terminal-stroke-length); }
  to { stroke-dashoffset: 0; }
}

@keyframes terminal-success-pulse {
  from { transform: scale(0.88); }
  55% { transform: scale(1.06); }
  to { transform: scale(1); }
}
</style>
