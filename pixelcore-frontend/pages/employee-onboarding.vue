<template>
  <main class="min-h-dvh bg-muted/35">
    <section
      v-if="state === 'loading'"
      class="mx-auto flex min-h-dvh max-w-2xl items-center px-5 py-12"
    >
      <StatePanel
        class="w-full border bg-card shadow-sm"
        kind="loading"
        title="Opening your invitation"
        message="Checking the secure employee invitation before showing account details."
      />
    </section>

    <section
      v-else-if="state === 'error'"
      class="mx-auto flex min-h-dvh max-w-2xl items-center px-5 py-12"
    >
      <StatePanel
        class="w-full border bg-card shadow-sm"
        kind="error"
        title="Invitation unavailable"
        :message="message"
      >
        <ButtonLink class="mt-5" variant="outline" to="/login">
          <LogIn class="h-4 w-4" aria-hidden="true" />
          Sign in to PixelCore
        </ButtonLink>
      </StatePanel>
    </section>

    <section
      v-else-if="invitation.account_exists"
      class="mx-auto flex min-h-dvh max-w-2xl items-center px-5 py-12"
    >
      <Card class="w-full overflow-hidden">
        <CardHeader class="border-b bg-secondary/35">
          <div
            class="grid h-11 w-11 place-items-center rounded-xl bg-background text-primary"
          >
            <UserCheck class="h-5 w-5" aria-hidden="true" />
          </div>
          <CardTitle class="mt-4 text-2xl">Your account is ready</CardTitle>
          <CardDescription>
            Sign in as {{ invitation.email }} to accept the invitation from
            {{ invitation.business.display_name }}.
          </CardDescription>
        </CardHeader>
        <CardContent class="pt-6">
          <ButtonLink class="w-full" :to="signInPath">
            <LogIn class="h-4 w-4" aria-hidden="true" />
            Sign in and accept invitation
          </ButtonLink>
        </CardContent>
      </Card>
    </section>

    <section
      v-else
      class="grid min-h-dvh lg:grid-cols-[minmax(22rem,.8fr)_minmax(0,1.2fr)]"
    >
      <aside
        class="relative isolate flex min-h-[24rem] flex-col overflow-hidden bg-[var(--brand-secondary)] px-6 py-8 text-white sm:px-10 lg:min-h-dvh lg:px-14 lg:py-12"
      >
        <div
          class="absolute right-10 top-10 -z-10 grid grid-cols-2 gap-2 opacity-20"
          aria-hidden="true"
        >
          <span class="h-16 w-16 rounded-lg bg-[var(--brand-accent)]" />
          <span class="h-16 w-16 rounded-lg bg-white" />
          <span class="h-16 w-16 rounded-lg bg-white" />
          <span class="h-16 w-16 rounded-lg bg-[var(--brand-accent)]" />
        </div>

        <PixelCoreMark />

        <div class="my-auto max-w-xl py-12">
          <div class="flex items-center gap-4">
            <Avatar class="h-14 w-14 border border-white/20">
              <AvatarImage
                v-if="invitation.business.logo_url"
                :src="invitation.business.logo_url"
                :alt="`${invitation.business.display_name} logo`"
              />
              <AvatarFallback class="bg-white text-foreground">
                {{ businessInitials }}
              </AvatarFallback>
            </Avatar>
            <div>
              <p class="text-sm font-semibold text-white/65">
                Employee invitation
              </p>
              <p class="mt-1 text-xl font-extrabold">
                {{ invitation.business.display_name }}
              </p>
            </div>
          </div>

          <h1
            class="mt-8 text-4xl font-extrabold leading-tight tracking-[-0.03em] sm:text-5xl"
          >
            Set up your employee account.
          </h1>
          <p class="mt-4 max-w-lg text-base leading-7 text-white/70">
            This account connects your workspace access, employee record,
            schedule, and attendance history without exposing administrative
            settings.
          </p>

          <dl class="mt-8 divide-y divide-white/10 border-y border-white/10">
            <div class="flex items-center justify-between gap-4 py-4">
              <dt class="text-sm text-white/60">Invited as</dt>
              <dd class="text-sm font-bold capitalize">
                {{ invitation.role }}
              </dd>
            </div>
            <div
              v-if="invitation.job_title"
              class="flex items-center justify-between gap-4 py-4"
            >
              <dt class="text-sm text-white/60">Role at work</dt>
              <dd class="text-sm font-bold">{{ invitation.job_title }}</dd>
            </div>
            <div class="flex items-center justify-between gap-4 py-4">
              <dt class="text-sm text-white/60">Account email</dt>
              <dd class="max-w-[16rem] truncate text-sm font-bold">
                {{ invitation.email }}
              </dd>
            </div>
          </dl>
        </div>

        <p class="text-xs leading-5 text-white/50">
          Secure invitation · Approval remains controlled by the business
          manager.
        </p>
      </aside>

      <div class="flex items-center px-5 py-12 sm:px-10 lg:px-14 lg:py-16">
        <form
          class="mx-auto w-full max-w-2xl"
          novalidate
          @submit.prevent="submit"
        >
          <div class="flex items-start gap-3">
            <div
              class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-secondary text-primary"
            >
              <BadgeCheck class="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h2 class="text-3xl font-extrabold tracking-[-0.025em]">
                Complete your employee profile
              </h2>
              <p class="mt-2 text-sm leading-6 text-muted-foreground">
                Your invitation confirms the work email. Add your account and
                work details before joining the team.
              </p>
            </div>
          </div>

          <ol class="mt-8 grid grid-cols-2 border-y" aria-label="Onboarding progress">
            <li class="flex items-center gap-3 border-r px-3 py-4">
              <span class="grid h-7 w-7 place-items-center rounded-full bg-primary text-xs font-black text-primary-foreground">1</span>
              <span class="text-sm font-bold">Account</span>
            </li>
            <li class="flex items-center gap-3 px-3 py-4">
              <span class="grid h-7 w-7 place-items-center rounded-full bg-primary text-xs font-black text-primary-foreground">2</span>
              <span class="text-sm font-bold">Work profile</span>
            </li>
          </ol>

          <div class="mt-8 grid gap-5 sm:grid-cols-2">
            <div>
              <Label for="employee-first-name">First name</Label>
              <Input
                id="employee-first-name"
                v-model.trim="form.first_name"
                class="mt-2"
                autocomplete="given-name"
                required
              />
            </div>
            <div>
              <Label for="employee-last-name">Last name</Label>
              <Input
                id="employee-last-name"
                v-model.trim="form.last_name"
                class="mt-2"
                autocomplete="family-name"
                required
              />
            </div>
            <div class="sm:col-span-2">
              <Label for="employee-email">Work email</Label>
              <Input
                id="employee-email"
                :model-value="invitation.email"
                class="mt-2"
                type="email"
                disabled
              />
            </div>
            <div>
              <Label for="employee-phone">Phone</Label>
              <Input
                id="employee-phone"
                v-model.trim="form.phone"
                class="mt-2"
                type="tel"
                autocomplete="tel"
                placeholder="+63 917 123 4567"
                required
              />
            </div>
            <div>
              <Label for="employee-username">Username</Label>
              <Input
                id="employee-username"
                v-model.trim="form.username"
                class="mt-2"
                autocomplete="username"
                placeholder="Optional"
              />
            </div>
            <div>
              <Label for="employee-password">Password</Label>
              <Input
                id="employee-password"
                v-model="form.password"
                class="mt-2"
                type="password"
                autocomplete="new-password"
                required
              />
            </div>
            <div>
              <Label for="employee-password-confirm">Confirm password</Label>
              <Input
                id="employee-password-confirm"
                v-model="form.password_confirm"
                class="mt-2"
                type="password"
                autocomplete="new-password"
                required
              />
            </div>
          </div>

          <div
            v-if="form.password"
            class="mt-6 border-y py-4"
            aria-live="polite"
          >
            <div class="flex items-center justify-between gap-4 text-sm">
              <span class="font-semibold">Password strength</span>
              <span>{{ strengthLabel }}</span>
            </div>
            <Progress class="mt-3 h-1.5" :model-value="strengthPercent" />
            <ul
              class="mt-4 grid gap-2 text-xs text-muted-foreground sm:grid-cols-2"
            >
              <li
                v-for="rule in passwordRules"
                :key="rule.label"
                class="flex items-center gap-2"
                :class="rule.met ? 'text-foreground' : ''"
              >
                <Check
                  v-if="rule.met"
                  class="h-3.5 w-3.5 text-primary"
                  aria-hidden="true"
                />
                <Circle v-else class="h-3.5 w-3.5" aria-hidden="true" />
                {{ rule.label }}
              </li>
            </ul>
          </div>

          <Separator class="my-8" />

          <div class="flex items-start gap-3">
            <div class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-secondary text-primary">
              <BriefcaseBusiness class="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h3 class="text-lg font-extrabold">Work profile</h3>
              <p class="mt-1 text-sm leading-6 text-muted-foreground">
                Review any details your manager entered and complete the rest.
              </p>
            </div>
          </div>

          <div class="mt-5 grid gap-5 sm:grid-cols-2">
            <div class="sm:col-span-2">
              <Label for="employee-job-title">Job title</Label>
              <Input
                id="employee-job-title"
                v-model.trim="form.job_title"
                class="mt-2"
                maxlength="120"
                placeholder="e.g. Store associate"
              />
            </div>
            <div>
              <Label for="employee-emergency-name">Emergency contact</Label>
              <Input
                id="employee-emergency-name"
                v-model.trim="form.emergency_contact_name"
                class="mt-2"
                maxlength="160"
                autocomplete="name"
              />
            </div>
            <div>
              <Label for="employee-emergency-phone">Emergency phone</Label>
              <Input
                id="employee-emergency-phone"
                v-model.trim="form.emergency_contact_phone"
                class="mt-2"
                maxlength="32"
                type="tel"
                autocomplete="tel"
              />
            </div>
          </div>

          <Alert v-if="message" class="mt-6" variant="destructive">
            <AlertCircle class="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Account not created</AlertTitle>
            <AlertDescription>{{ message }}</AlertDescription>
          </Alert>

          <Button
            class="mt-6 h-12 w-full"
            type="submit"
            :disabled="submitting || !canSubmit"
          >
            <UserCheck class="h-4 w-4" aria-hidden="true" />
            {{
              submitting
                ? "Creating employee account…"
                : "Create account and join team"
            }}
          </Button>
        </form>
      </div>
    </section>
  </main>
</template>

<script setup>
import {
  AlertCircle,
  BadgeCheck,
  BriefcaseBusiness,
  Check,
  Circle,
  LogIn,
  UserCheck,
} from "lucide-vue-next";

definePageMeta({ layout: "storefront" });

const config = useRuntimeConfig();
const route = useRoute();
const auth = useAuthStore();
const { accessToken } = useApiClient();

const state = ref("loading");
const submitting = ref(false);
const message = ref("");
const invitation = ref({
  account_exists: false,
  business: {},
  email: "",
  employee_name: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
  job_title: "",
  role: "staff",
});
const form = reactive({
  first_name: "",
  last_name: "",
  phone: "",
  username: "",
  password: "",
  password_confirm: "",
  job_title: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
});

const token = computed(() => String(route.query.token || ""));
const signInPath = computed(() => {
  const next = `/accept-invitation?token=${encodeURIComponent(token.value)}`;
  return `/login?next=${encodeURIComponent(next)}`;
});
const businessInitials = computed(() => {
  return String(invitation.value.business?.display_name || "PC")
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
});
const passwordRules = computed(() => [
  { label: "At least 10 characters", met: form.password.length >= 10 },
  { label: "One uppercase letter", met: /[A-Z]/.test(form.password) },
  { label: "One number", met: /\d/.test(form.password) },
  { label: "One symbol", met: /[^A-Za-z0-9]/.test(form.password) },
]);
const strength = computed(
  () => passwordRules.value.filter((rule) => rule.met).length,
);
const strengthPercent = computed(() => strength.value * 25);
const strengthLabel = computed(
  () => ["Too weak", "Weak", "Fair", "Good", "Strong"][strength.value],
);
const canSubmit = computed(() => {
  return Boolean(
    form.first_name &&
      form.last_name &&
      form.phone &&
      strength.value >= 3 &&
      form.password === form.password_confirm,
  );
});

onMounted(loadInvitation);

async function loadInvitation() {
  if (!token.value) {
    state.value = "error";
    message.value = "The invitation link is missing its secure token.";
    return;
  }
  try {
    invitation.value = await $fetch("team/invitations/validate/", {
      baseURL: config.public.apiBaseUrl,
      query: { token: token.value },
    });
    form.job_title = invitation.value.job_title || "";
    form.emergency_contact_name = invitation.value.emergency_contact_name || "";
    form.emergency_contact_phone = invitation.value.emergency_contact_phone || "";
    state.value = "ready";
  } catch (error) {
    message.value =
      error?.data?.error?.message || "This invitation is no longer available.";
    state.value = "error";
  }
}

async function submit() {
  if (!canSubmit.value || submitting.value) return;
  submitting.value = true;
  message.value = "";
  try {
    const response = await $fetch("team/invitations/register/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      body: { token: token.value, ...form },
      credentials: "include",
    });
    accessToken.value = response.access;
    await auth.loadUser();
    await navigateTo("/employee");
  } catch (error) {
    message.value =
      error?.data?.error?.message ||
      "Review the account details and try again.";
  } finally {
    submitting.value = false;
  }
}
</script>
