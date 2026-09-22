<template>
  <main class="mx-auto flex min-h-[80vh] max-w-xl items-center px-6 py-16">
    <section class="w-full border-y py-10">
      <p class="text-xs font-extrabold uppercase tracking-[0.16em] text-primary">
        Team invitation
      </p>
      <h1 class="display-face mt-3 text-4xl font-semibold">
        Join the business workspace
      </h1>
      <p class="mt-4 leading-7 text-muted-foreground">
        Your account will become an active team member and a linked workforce
        profile will be prepared for approval and scheduling.
      </p>

      <StatePanel
        v-if="state === 'working'"
        class="mt-7"
        kind="loading"
        title="Accepting invitation"
        message="Confirming the secure invitation link."
      />
      <StatePanel
        v-else-if="state === 'success'"
        class="mt-7"
        title="Invitation accepted"
        message="Your employee portal is ready. A manager may still need to approve attendance and leave access."
      >
        <ButtonLink class="mt-5" to="/employee">
          <BriefcaseBusiness class="h-4 w-4" aria-hidden="true" />
          Open employee portal
        </ButtonLink>
      </StatePanel>
      <StatePanel
        v-else
        class="mt-7"
        kind="error"
        title="Invitation unavailable"
        :message="message"
      >
        <ButtonLink variant="outline" class="mt-5" to="/login">
          Sign in with another account
        </ButtonLink>
      </StatePanel>
    </section>
  </main>
</template>

<script setup>
import { BriefcaseBusiness } from "lucide-vue-next";

const route = useRoute();
const auth = useAuthStore();
const { apiFetch } = useApiClient();
const state = ref("working");
const message = ref("This invitation link is invalid or has expired.");

onMounted(async () => {
  await auth.restoreSession();
  const token = String(route.query.token || "");
  if (!token) {
    state.value = "error";
    return;
  }

  try {
    await apiFetch("team/invitations/accept/", {
      method: "POST",
      body: { token },
    });
    await auth.loadUser();
    state.value = "success";
  } catch (error) {
    message.value = error?.data?.error?.message || message.value;
    state.value = "error";
  }
});
</script>
