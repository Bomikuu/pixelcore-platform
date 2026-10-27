<template>
  <Button
    type="button"
    variant="ghost"
    size="icon"
    class="h-9 w-9 shrink-0"
    :aria-label="isDark ? 'Switch to light theme' : 'Switch to dark theme'"
    :title="isDark ? 'Switch to light theme' : 'Switch to dark theme'"
    :aria-pressed="isDark"
    @click="toggle"
  >
    <Sun v-if="isDark" class="h-[1.125rem] w-[1.125rem]" aria-hidden="true" />
    <Moon v-else class="h-[1.125rem] w-[1.125rem]" aria-hidden="true" />
  </Button>
</template>

<script setup>
import { Moon, Sun } from "lucide-vue-next";
const { isDark, toggle } = useWorkspaceTheme();
</script>
