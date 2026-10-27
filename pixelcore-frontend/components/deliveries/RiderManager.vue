<template>
  <Dialog v-model:open="open">
    <DialogTrigger as-child
      ><Button class="gap-2" type="button" variant="outline"
        ><UsersRound class="h-4 w-4" aria-hidden="true" /> Manage riders</Button
      ></DialogTrigger
    >
    <DialogContent
      class="max-h-[90dvh] max-w-xl overflow-y-auto"
      :style="style"
      @interact-outside="busy && $event.preventDefault()"
      @escape-key-down="busy && $event.preventDefault()"
    >
      <DialogHeader
        ><DialogTitle>Delivery riders</DialogTitle
        ><DialogDescription
          >Add an employee account or invite an independent rider with
          delivery-only access.</DialogDescription
        ></DialogHeader
      >
      <form class="space-y-4" novalidate @submit.prevent="addRider">
        <div>
          <Label for="rider-name">Rider name</Label
          ><Input
            id="rider-name"
            ref="nameInput"
            v-model.trim="form.display_name"
            class="mt-2"
            :aria-invalid="Boolean(error)"
            maxlength="160"
            autocomplete="name"
          />
        </div>
        <div>
          <Label for="rider-email">Account email</Label
          ><Input
            id="rider-email"
            v-model.trim="form.email"
            class="mt-2"
            :aria-invalid="Boolean(error)"
            type="email"
            autocomplete="email"
          />
        </div>
        <div>
          <Label for="rider-kind">Access type</Label
          ><Select v-model="form.kind"
            ><SelectTrigger id="rider-kind" class="mt-2"
              ><SelectValue /></SelectTrigger
            ><SelectContent
              ><SelectItem value="employee">Employee account</SelectItem
              ><SelectItem value="independent"
                >Independent rider</SelectItem
              ></SelectContent
            ></Select
          >
        </div>
        <p class="text-xs leading-5 text-muted-foreground">
          Employees need an active account in this business. Independent riders
          sign in or register with the invited email, verify it, then accept in
          the rider portal.
        </p>
        <p v-if="error" role="alert" class="text-sm text-destructive">
          {{ error }}
        </p>
        <p v-if="notice" role="status" class="text-sm text-primary">
          {{ notice }}
        </p>
        <Button class="gap-2" type="submit" :disabled="busy">{{
          busy
            ? "Saving…"
            : form.kind === "employee"
              ? "Add employee rider"
              : "Create rider invitation"
        }}</Button>
      </form>
      <div
        class="flex flex-wrap items-center justify-between gap-3 border-y py-4 text-sm"
      >
        <span>Share the rider portal after inviting them.</span
        ><Button
          class="gap-2"
          type="button"
          variant="outline"
          size="sm"
          @click="copyLink"
          ><Copy class="h-4 w-4" aria-hidden="true" />{{
            copied ? "Link copied" : "Copy portal link"
          }}</Button
        >
      </div>
      <ul v-if="riders.length" class="divide-y">
        <li
          v-for="rider in riders"
          :key="rider.public_id"
          class="flex items-center justify-between gap-3 py-3"
        >
          <div class="min-w-0">
            <p class="break-words text-sm font-semibold">
              {{ rider.display_name }}
            </p>
            <p class="mt-1 break-all text-xs text-muted-foreground">
              {{ rider.email }}
            </p>
            <p class="mt-1 text-xs capitalize text-muted-foreground">
              {{ rider.kind }} · {{ rider.status
              }}{{
                rider.status === "active" && !rider.available
                  ? " · Account inactive"
                  : ""
              }}
            </p>
          </div>
          <Button
            v-if="rider.status !== 'revoked'"
            type="button"
            variant="ghost"
            size="sm"
            class="gap-2 shrink-0 text-destructive"
            :disabled="busy"
            @click="revokeTarget = rider"
            >Revoke</Button
          >
        </li>
      </ul>
      <p v-else class="py-4 text-sm text-muted-foreground">
        No riders added yet.
      </p>
    </DialogContent>
  </Dialog>
  <Dialog
    :open="Boolean(revokeTarget)"
    @update:open="!$event && (revokeTarget = null)"
  >
    <DialogContent :style="style"
      ><DialogHeader
        ><DialogTitle>Revoke rider access?</DialogTitle
        ><DialogDescription
          >{{ revokeTarget?.display_name }} will lose assigned deliveries. Their
          current location will be cleared and active deliveries will return to
          ready for pickup.</DialogDescription
        ></DialogHeader
      >
      <p v-if="revokeError" role="alert" class="text-sm text-destructive">
        {{ revokeError }}
      </p>
      <DialogFooter
        ><Button
          class="gap-2"
          type="button"
          variant="outline"
          :disabled="busy"
          @click="revokeTarget = null"
          >Keep access</Button
        ><Button
          class="gap-2"
          type="button"
          variant="destructive"
          :disabled="busy"
          @click="revoke"
          >{{ busy ? "Revoking…" : "Revoke access" }}</Button
        ></DialogFooter
      ></DialogContent
    >
  </Dialog>
</template>
<script setup>
import { Copy, UsersRound } from "lucide-vue-next";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "~/components/ui/dialog";
import { deliveryError } from "~/utils/deliveryTracking";
const props = defineProps({
  businessId: { type: String, required: true },
  riders: { type: Array, default: () => [] },
});
const emit = defineEmits(["changed"]);
const { apiFetch } = useApiClient();
const { style } = useWorkspaceTheme();
const open = ref(false),
  busy = ref(false),
  error = ref(""),
  notice = ref(""),
  copied = ref(false),
  revokeTarget = ref(null),
  revokeError = ref("");
const form = reactive({ display_name: "", email: "", kind: "employee" });
const nameInput = ref(null);
async function addRider() {
  if (busy.value) return;
  error.value = "";
  notice.value = "";
  if (!form.display_name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    error.value = "Enter the rider's name and a valid account email.";
    nameInput.value?.$el?.focus();
    return;
  }
  busy.value = true;
  const businessId = props.businessId;
  try {
    const rider = await apiFetch(`businesses/${businessId}/delivery-riders/`, {
      method: "POST",
      body: { ...form },
    });
    if (businessId !== props.businessId) return;
    notice.value =
      rider.status === "invited"
        ? "Invitation created. Share the portal link with this rider; they must accept before assignment."
        : "Employee rider added.";
    form.display_name = form.email = "";
    emit("changed");
  } catch (failure) {
    error.value = deliveryError(failure);
  } finally {
    busy.value = false;
  }
}
async function revoke() {
  if (busy.value || !revokeTarget.value) return;
  busy.value = true;
  revokeError.value = "";
  try {
    await apiFetch(
      `businesses/${props.businessId}/delivery-riders/${revokeTarget.value.public_id}/`,
      { method: "DELETE" },
    );
    revokeTarget.value = null;
    emit("changed");
  } catch (failure) {
    revokeError.value = deliveryError(failure);
  } finally {
    busy.value = false;
  }
}
async function copyLink() {
  try {
    await navigator.clipboard.writeText(
      `${window.location.origin}/rider/deliveries`,
    );
    copied.value = true;
  } catch {
    error.value =
      "The link could not be copied. Share /rider/deliveries on this site.";
  }
}
watch(
  () => props.businessId,
  () => {
    open.value = false;
    revokeTarget.value = null;
    form.display_name = form.email = "";
    error.value = notice.value = "";
  },
);
</script>
