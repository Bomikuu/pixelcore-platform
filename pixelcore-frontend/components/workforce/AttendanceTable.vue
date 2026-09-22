<template>
  <Card class="overflow-hidden">
    <CardHeader class="border-b">
      <div class="flex items-start justify-between gap-4">
        <div>
          <CardTitle>Attendance history</CardTitle>
          <CardDescription>Clock-ins, worked time, and recorded exceptions.</CardDescription>
        </div>
        <Badge variant="outline">{{ items.length }} shifts</Badge>
      </div>
    </CardHeader>
    <CardContent class="p-0">
      <StatePanel
        v-if="!items.length"
        title="No attendance yet"
        message="Your shifts will appear after you use a paired attendance terminal."
      />
      <div v-else class="overflow-x-auto">
        <Table class="min-w-[44rem]">
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Clock in</TableHead>
              <TableHead>Clock out</TableHead>
              <TableHead>Worked</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Context</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="item in items" :key="item.public_id">
              <TableCell class="font-semibold">{{ formatDay(item.clock_in || item.created_at) }}</TableCell>
              <TableCell>{{ formatTime(item.clock_in) }}</TableCell>
              <TableCell>{{ item.clock_out ? formatTime(item.clock_out) : "In progress" }}</TableCell>
              <TableCell>{{ formatMinutes(item.worked_minutes) }}</TableCell>
              <TableCell><StatusPill :value="item.status" /></TableCell>
              <TableCell class="max-w-xs text-sm text-muted-foreground">
                {{ item.late_reason || item.override_reason || item.notes || "—" }}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </CardContent>
  </Card>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
});

function formatDay(value) {
  return value
    ? new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value))
    : "—";
}

function formatTime(value) {
  return value
    ? new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(value))
    : "—";
}

function formatMinutes(value = 0) {
  const minutes = Number(value || 0);
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
}
</script>
