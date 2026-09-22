<template>
  <StatePanel
    class="mx-auto mt-16 max-w-xl border bg-card"
    kind="loading"
    title="Opening Workforce"
    message="Team access now lives with employee records and attendance."
  />
</template>

<script setup>
definePageMeta({
  middleware: [
    function redirectTeamAccess() {
      return navigateTo("/workspace/operate/workforce?view=access", {
        replace: true,
      });
    },
  ],
});
</script>
