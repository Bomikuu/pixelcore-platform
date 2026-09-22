<template>
  <aside class="space-y-4 xl:sticky xl:top-16">
    <Card>
      <CardHeader>
        <div class="flex items-center gap-3">
          <div class="grid h-10 w-10 place-items-center rounded-lg bg-secondary text-primary">
            <Send class="h-4 w-4" aria-hidden="true" />
          </div>
          <div>
            <CardTitle class="text-base">{{ title }}</CardTitle>
            <CardDescription>Secure link expires in 7 days</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent class="space-y-4">
        <div v-for="item in steps" :key="item.title" class="flex items-start gap-3">
          <component
            :is="item.icon"
            class="mt-0.5 h-4 w-4 shrink-0 text-primary"
            aria-hidden="true"
          />
          <div>
            <p class="text-sm font-bold">{{ item.title }}</p>
            <p class="mt-1 text-xs leading-5 text-muted-foreground">
              {{ item.detail }}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>

    <div class="flex flex-col gap-2">
      <Button class="h-11" type="submit" :disabled="saving">
        <Send class="h-4 w-4" aria-hidden="true" />
        {{ saving ? "Sending…" : actionLabel }}
      </Button>
      <Button variant="outline" type="button" @click="$emit('cancel')">
        Cancel
      </Button>
    </div>
  </aside>
</template>

<script setup>
import {
  BadgeCheck,
  ClipboardPenLine,
  Send,
  UserCheck,
} from "lucide-vue-next";

const props = defineProps({
  mode: {
    type: String,
    required: true,
  },
  saving: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["cancel"]);

const title = computed(() =>
  props.mode === "invite"
    ? "Employee completes the profile"
    : "Profile is prepared for review",
);

const actionLabel = computed(() =>
  props.mode === "invite"
    ? "Send email invitation"
    : "Create employee and invite",
);

const steps = computed(() => [
  {
    title: "Secure registration",
    detail: "The employee creates their own password from the emailed link.",
    icon: BadgeCheck,
  },
  {
    title: props.mode === "invite" ? "Employee profile" : "Profile review",
    detail:
      props.mode === "invite"
        ? "They provide their personal and work details in the public form."
        : "They can review the details you entered while creating their account.",
    icon: ClipboardPenLine,
  },
  {
    title: "Manager approval",
    detail: "Attendance and leave actions unlock after the profile is approved.",
    icon: UserCheck,
  },
]);
</script>
