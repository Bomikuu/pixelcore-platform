<template>
  <div class="flex items-center gap-2">
    <Label for="smokey-theme" class="text-xs text-muted-foreground">Theme</Label
    ><Select v-model="preference"
      ><SelectTrigger id="smokey-theme" class="w-28"
        ><SelectValue /></SelectTrigger
      ><SelectContent
        ><SelectItem value="light">Light</SelectItem
        ><SelectItem value="dark">Dark</SelectItem
        ><SelectItem value="system">System</SelectItem></SelectContent
      ></Select
    >
  </div>
</template>
<script setup>
import { initialSmokeyTheme } from "~/utils/smokeySettings";
const { preference } = useWorkspaceTheme();
const initialized = useState("smokey-theme-initialized", () => false);
if (import.meta.client && !initialized.value) {
  let saved;
  try {
    saved = localStorage.getItem("pixelcore-workspace-theme");
  } catch {
    /* Retain an in-memory preference after this first mount. */
  }
  preference.value = initialSmokeyTheme(
    preference.value,
    saved,
    initialized.value,
  );
  initialized.value = true;
}
</script>
