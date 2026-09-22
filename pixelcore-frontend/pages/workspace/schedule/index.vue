<template>
  <div class="w-full max-w-none space-y-4 px-4 pb-10 pt-4 sm:px-5 sm:pt-5 lg:px-6">
    <section class="relative overflow-hidden rounded-xl border border-emerald-900/20 bg-[#0d2f2a] text-white shadow-sm">
      <div class="pointer-events-none absolute inset-0 opacity-40 [background-image:radial-gradient(circle_at_20%_0%,rgba(190,224,179,.22),transparent_38%),linear-gradient(115deg,transparent_45%,rgba(255,255,255,.05)_45%,rgba(255,255,255,.05)_46%,transparent_46%)]" />
      <div class="relative grid gap-0 lg:grid-cols-[minmax(0,1fr)_21rem]">
        <div class="p-5 sm:p-6">
          <div class="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-emerald-200">
            <WandSparkles class="h-4 w-4" aria-hidden="true" />
            Venue schedule
          </div>
          <h1 class="mt-2 max-w-3xl text-2xl font-black tracking-[-0.03em] sm:text-3xl">
            One calendar for every table, room, and occasion.
          </h1>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-emerald-50/75">
            Run daily {{ bookingPlural.toLowerCase() }}, map a restaurant floor, or compose a wedding venue with stages, dining zones, and service areas.
          </p>
        </div>

        <div class="border-t border-white/10 bg-black/10 p-5 lg:border-l lg:border-t-0">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.18em] text-emerald-200">Public booking</p>
              <p class="mt-2 text-lg font-bold">{{ scheduleSettings.public_booking_enabled ? 'Open for requests' : 'Private for now' }}</p>
            </div>
            <Switch
              :checked="scheduleSettings.public_booking_enabled"
              aria-label="Enable public booking form"
              :disabled="savingSettings"
              @update:checked="togglePublicBooking"
            />
          </div>
          <p class="mt-2 text-xs leading-5 text-emerald-50/70">
            {{ scheduleSettings.public_booking_enabled
              ? 'Customers can view live availability and submit a request from your public page.'
              : 'Enable the form when your services, staff hours, and venue resources are ready.' }}
          </p>
          <div class="mt-4 grid grid-cols-2 gap-2">
            <ButtonAnchor
              v-if="scheduleSettings.public_booking_enabled && publicBookingUrl"
              :href="publicBookingUrl"
              target="_blank"
              rel="noopener"
              size="sm"
              class="h-9 w-full bg-emerald-200 text-emerald-950 hover:bg-emerald-100"
            >
              <ExternalLink class="h-4 w-4" aria-hidden="true" />
              Open public form
            </ButtonAnchor>
            <Button v-else size="sm" class="h-9 w-full" type="button" :disabled="savingSettings" @click="togglePublicBooking(true)">
              <Globe2 class="h-4 w-4" aria-hidden="true" />
              Enable public form
            </Button>
            <Button size="sm" variant="ghost" class="h-9 w-full text-white hover:bg-white/10 hover:text-white" type="button" :disabled="!publicBookingUrl" @click="openBookingShare">
              <QrCode class="h-4 w-4" aria-hidden="true" />
              Share link and QR
            </Button>
          </div>
        </div>
      </div>
    </section>

    <StatePanel
      v-if="loading"
      kind="loading"
      title="Loading the schedule"
      message="Retrieving bookings, tasks, staff, resources, availability, and Calendar status."
    />
    <StatePanel v-else-if="error" kind="error" title="Schedule unavailable" :message="error">
      <Button variant="outline" type="button" @click="load">Try again</Button>
    </StatePanel>

    <template v-else>
      <Tabs v-model="activeWorkspaceTab" class="space-y-4">
        <TabsList class="grid h-auto w-full grid-cols-2 rounded-xl border bg-card p-1 sm:w-fit sm:min-w-[46rem] sm:grid-cols-4">
          <TabsTrigger value="calendar" class="gap-2 py-2.5">
            <CalendarDays class="h-4 w-4" aria-hidden="true" />
            Calendar
          </TabsTrigger>
          <TabsTrigger value="layouts" class="gap-2 py-2.5">
            <LayoutGrid class="h-4 w-4" aria-hidden="true" />
            <span class="hidden sm:inline">Venue layouts</span>
            <span class="sm:hidden">Layouts</span>
          </TabsTrigger>
          <TabsTrigger value="setup" class="gap-2 py-2.5">
            <SlidersHorizontal class="h-4 w-4" aria-hidden="true" />
            <span class="hidden sm:inline">Scheduling setup</span>
            <span class="sm:hidden">Setup</span>
          </TabsTrigger>
          <TabsTrigger value="events" class="gap-2 py-2.5">
            <CalendarHeart class="h-4 w-4" aria-hidden="true" />
            <span class="hidden sm:inline">Events &amp; RSVP</span>
            <span class="sm:hidden">Events</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="calendar" class="mt-0 space-y-5">
      <section class="flex flex-col justify-between gap-4 rounded-2xl border border-blue-200/70 bg-gradient-to-r from-blue-50/80 via-background to-background p-4 shadow-sm sm:flex-row sm:items-center sm:p-5">
        <div class="flex items-start gap-3">
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-700">
            <Cloud v-if="calendar?.connected" class="h-5 w-5" aria-hidden="true" />
            <CloudOff v-else class="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="font-bold">Google Calendar</h2>
              <Badge :variant="calendar?.connected ? 'secondary' : 'outline'">{{ calendar?.connected ? 'Connected' : 'Not connected' }}</Badge>
            </div>
            <p class="mt-1 text-sm text-muted-foreground">
              {{ calendar?.connected
                ? `Confirmed ${bookingPlural.toLowerCase()} and tasks project to ${calendar.google_email || 'your Google account'}.`
                : `Connect once to project confirmed ${bookingPlural.toLowerCase()} and tasks through PixelCore's Calendar bridge.` }}
            </p>
            <p v-if="calendar?.last_synced_at" class="mt-1 text-xs text-muted-foreground">Last synced {{ formatDateTime(calendar.last_synced_at) }}</p>
            <p v-if="calendar?.configuration_error" class="mt-1 text-xs font-medium text-destructive">{{ calendar.configuration_error }}</p>
          </div>
        </div>
        <div class="flex shrink-0 flex-wrap gap-2">
          <ButtonAnchor v-if="!calendar?.connected && calendar?.authorize_url" :href="calendar.authorize_url"><ExternalLink class="h-4 w-4" aria-hidden="true" />Connect Google Calendar</ButtonAnchor>
          <Button v-else-if="calendar?.connected" type="button" :disabled="saving" @click="syncCalendar"><RefreshCw class="h-4 w-4" aria-hidden="true" />Sync now</Button>
          <ButtonLink v-else to="/settings/integrations" variant="outline">Review integration</ButtonLink>
        </div>
      </section>

      <Alert v-if="!serviceOfferings.length" class="border-amber-300 bg-amber-50 text-amber-950">
        <CalendarCheck2 class="h-4 w-4 text-amber-700" aria-hidden="true" />
        <AlertTitle>No published service is available</AlertTitle>
        <AlertDescription class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>
            The public form cannot offer dates until you publish a bookable service, then assign it to an employee under Scheduling setup.
          </span>
          <ButtonLink
            to="/workspace/sell/products/new"
            size="sm"
            variant="outline"
            class="shrink-0 border-amber-400 bg-white text-amber-950 hover:bg-amber-100"
          >
            <Plus class="h-4 w-4" aria-hidden="true" />
            Add service
          </ButtonLink>
        </AlertDescription>
      </Alert>

      <dl class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4">
        <div
          v-for="metric in metrics"
          :key="metric.label"
          class="border-b p-4 last:border-b-0 sm:[&:nth-child(odd)]:border-r sm:[&:nth-last-child(-n+2)]:border-b-0 xl:border-b-0 xl:border-r xl:last:border-r-0"
        >
          <div class="flex items-center justify-between gap-3">
            <dt class="text-sm font-semibold text-muted-foreground">{{ metric.label }}</dt>
            <component :is="metric.icon" class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </div>
          <dd class="mt-2 text-2xl font-extrabold tabular-nums">{{ metric.value }}</dd>
          <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
        </div>
      </dl>

      <Tabs v-model="calendarView" class="space-y-4">
        <div class="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <p class="text-sm font-bold">Calendar view</p>
            <p class="mt-1 text-xs text-muted-foreground">Scan the month or focus on one operating day.</p>
          </div>
          <TabsList class="grid h-auto w-full grid-cols-2 sm:w-64">
            <TabsTrigger value="month" class="gap-2"><CalendarRange class="h-4 w-4" aria-hidden="true" />Month</TabsTrigger>
            <TabsTrigger value="day" class="gap-2"><CalendarClock class="h-4 w-4" aria-hidden="true" />Day</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="month" class="mt-0">

      <Card class="overflow-hidden">
        <CardHeader class="border-b bg-muted/20 py-4">
          <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
            <div class="flex items-center gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <CalendarRange class="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle class="text-xl sm:text-2xl">{{ monthLabel }}</CardTitle>
                <CardDescription>Click a date to review its tasks, {{ bookingPlural.toLowerCase() }}, and resource availability.</CardDescription>
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <Button variant="outline" size="icon" type="button" aria-label="Previous month" @click="moveMonth(-1)">
                <ChevronLeft class="h-4 w-4" aria-hidden="true" />
              </Button>
              <Button variant="outline" size="sm" type="button" @click="goToday">Today</Button>
              <Button variant="outline" size="icon" type="button" aria-label="Next month" @click="moveMonth(1)">
                <ChevronRight class="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent class="p-0">
          <div class="overflow-x-auto">
            <div class="min-w-[860px]">
              <div class="grid grid-cols-7 gap-2 bg-muted/20 px-3 pt-3">
                <div
                  v-for="weekday in weekdays"
                  :key="weekday"
                  class="px-3 py-2.5 text-center text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground"
                >
                  {{ weekday }}
                </div>
              </div>
              <div class="grid min-h-[720px] grid-cols-7 grid-rows-6 gap-2 bg-muted/20 p-3">
                <Button
                  v-for="day in monthCells"
                  :key="day.iso"
                  type="button"
                  variant="ghost"
                  class="group relative h-auto min-h-[112px] items-start justify-start rounded-xl border p-2.5 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:bg-card hover:shadow-md"
                  :class="dayCellClass(day)"
                  @click="selectDay(day.iso)"
                >
                  <span class="w-full">
                    <span class="flex items-start justify-between gap-2">
                      <span
                        class="flex h-7 min-w-7 items-center justify-center rounded-full px-1 text-xs font-semibold"
                        :class="day.iso === todayIso ? 'bg-primary text-primary-foreground' : day.current ? 'text-foreground' : 'text-muted-foreground/60'"
                      >
                        {{ day.day }}
                      </span>
                      <span v-if="entriesFor(day.iso).length" class="text-[10px] font-medium text-muted-foreground">
                        {{ entriesFor(day.iso).length }}
                      </span>
                    </span>
                    <span class="mt-2 block space-y-1">
                      <span
                        v-for="entry in entriesFor(day.iso).slice(0, 3)"
                        :key="entry.key"
                        class="flex items-center gap-1.5 truncate rounded-md px-1.5 py-1 text-[10px] font-medium"
                        :class="entryClass(entry)"
                      >
                        <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-70" />
                        <span class="shrink-0 font-semibold">{{ formatTime(entry.starts_at) }}</span>
                        <span class="truncate">{{ entry.title }}</span>
                      </span>
                      <span v-if="entriesFor(day.iso).length > 3" class="block px-1.5 text-[10px] font-semibold text-muted-foreground">
                        +{{ entriesFor(day.iso).length - 3 }} more
                      </span>
                    </span>
                  </span>
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
        </TabsContent>

        <TabsContent value="day" class="mt-0 space-y-5">
      <section class="rounded-2xl border bg-card p-4 shadow-sm sm:p-5">
        <div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div class="flex items-center gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <CalendarClock class="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Selected day</p>
              <h2 class="font-bold">{{ selectedLabel }}</h2>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <Button variant="outline" size="icon" type="button" aria-label="Previous day" @click="moveSelectedDay(-1)"><ChevronLeft class="h-4 w-4" aria-hidden="true" /></Button>
            <ScheduleDatePicker
              v-model="selectedDay"
              class="w-full sm:w-48"
              label="Selected schedule date"
              @change="refreshSelectedDay"
            />
            <Button variant="outline" size="icon" type="button" aria-label="Next day" @click="moveSelectedDay(1)"><ChevronRight class="h-4 w-4" aria-hidden="true" /></Button>
            <Badge class="border-amber-200 bg-amber-100 text-amber-800 hover:bg-amber-100">{{ selectedEvents.length }} task{{ selectedEvents.length === 1 ? '' : 's' }}</Badge>
            <Badge class="border-sky-200 bg-sky-100 text-sky-800 hover:bg-sky-100">{{ selectedBookings.length }} {{ bookingSingular.toLowerCase() }}{{ selectedBookings.length === 1 ? '' : 's' }}</Badge>
            <Badge class="border-emerald-200 bg-emerald-100 text-emerald-800 hover:bg-emerald-100">{{ availableResources }} {{ resourceWord.toLowerCase() }}{{ availableResources === 1 ? '' : 's' }} free</Badge>
          </div>
        </div>
      </section>

      <div class="grid gap-5 xl:grid-cols-2">
        <Card>
          <CardHeader class="flex flex-row items-start justify-between gap-4 pb-4">
            <div>
              <CardTitle class="flex items-center gap-3">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                  <CalendarClock class="h-5 w-5" aria-hidden="true" />
                </span>
                Day schedule
              </CardTitle>
              <CardDescription>Tasks and internal work planned for the selected day.</CardDescription>
            </div>
            <Button size="sm" variant="outline" type="button" @click="openTaskEditor">
              <Plus class="h-4 w-4" aria-hidden="true" />
              Task
            </Button>
          </CardHeader>
          <CardContent>
            <div v-if="!selectedEvents.length" class="rounded-xl border border-dashed p-8 text-center">
              <ClipboardList class="mx-auto h-8 w-8 text-muted-foreground/50" aria-hidden="true" />
              <p class="mt-2 text-sm font-medium">Nothing planned for this day</p>
              <p class="mt-1 text-xs text-muted-foreground">Add a staff task, meeting, deadline, or admin reminder.</p>
            </div>
            <div v-else class="space-y-3">
              <article
                v-for="event in selectedEvents"
                :key="event.id"
                class="group flex items-start gap-3 rounded-xl border p-3 transition-colors hover:bg-muted/30"
                :class="event.status === 'completed' ? 'opacity-60' : ''"
              >
                <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg" :class="eventColor(event.event_type)">
                  <component :is="eventIcon(event.event_type)" class="h-4 w-4" aria-hidden="true" />
                </div>
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <p class="font-medium" :class="event.status === 'completed' ? 'line-through' : ''">{{ event.title }}</p>
                    <Badge variant="outline" class="capitalize">{{ event.event_type }}</Badge>
                    <Badge v-if="event.resource_layout_name" variant="secondary"><LayoutGrid class="mr-1 h-3 w-3" aria-hidden="true" />{{ event.resource_layout_name }}</Badge>
                  </div>
                  <p class="mt-1 text-xs text-muted-foreground">
                    {{ formatTime(event.starts_at) }}<span v-if="event.ends_at"> – {{ formatTime(event.ends_at) }}</span>
                  </p>
                  <p v-if="event.notes" class="mt-1 line-clamp-2 text-xs text-muted-foreground">{{ event.notes }}</p>
                </div>
                <Button
                  v-if="event.status !== 'completed'"
                  variant="ghost"
                  size="icon"
                  type="button"
                  aria-label="Mark task complete"
                  @click="completeEvent(event)"
                >
                  <CheckCircle2 class="h-4 w-4 text-emerald-600" aria-hidden="true" />
                </Button>
                <CheckCircle2 v-else class="mt-2 h-4 w-4 shrink-0 text-emerald-600" aria-hidden="true" />
              </article>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader class="flex flex-row items-start justify-between gap-4 pb-4">
            <div>
              <CardTitle class="flex items-center gap-2">
                <Users class="h-5 w-5 text-primary" aria-hidden="true" />
                {{ bookingPlural }}
              </CardTitle>
              <CardDescription>Every customer visit for the selected day, ordered by arrival time.</CardDescription>
            </div>
            <Button size="sm" variant="outline" type="button" @click="openBookingEditor()">
              <Plus class="h-4 w-4" aria-hidden="true" />
              {{ bookingSingular }}
            </Button>
          </CardHeader>
          <CardContent>
            <div v-if="!selectedBookings.length" class="rounded-xl border border-dashed p-8 text-center">
              <Users class="mx-auto h-8 w-8 text-muted-foreground/50" aria-hidden="true" />
              <p class="mt-2 text-sm font-medium">No {{ bookingPlural.toLowerCase() }} for this day</p>
              <p class="mt-1 text-xs text-muted-foreground">Available {{ resourceWord.toLowerCase() }}s stay green on the layout.</p>
            </div>
            <div v-else class="space-y-3">
              <article
                v-for="booking in selectedBookings"
                :key="booking.public_id"
                class="flex flex-col gap-3 rounded-xl border p-3 transition-colors hover:bg-muted/25 sm:flex-row sm:items-center"
              >
                <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sky-100 text-sky-700">
                  <Users class="h-4 w-4" aria-hidden="true" />
                </div>
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <p class="font-medium">{{ customerName(booking) }}</p>
                    <StatusPill :value="booking.status" />
                  </div>
                  <p class="mt-1 text-xs text-muted-foreground">
                    {{ formatTime(booking.starts_at) }} – {{ formatTime(booking.ends_at) }}
                    · {{ booking.seats }} {{ booking.seats === 1 ? guestWordSingular : guestWord }}
                    <span v-if="booking.resources?.length"> · {{ booking.resources.map(item => item.name).join(', ') }}</span>
                  </p>
                  <p class="mt-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground">
                    Booking ID · <span class="font-mono tracking-normal">{{ booking.confirmation_code }}</span>
                  </p>
                </div>
                <div v-if="booking.status === 'pending'" class="flex shrink-0 gap-2">
                  <Button size="sm" variant="outline" type="button" :disabled="saving" @click="setBookingStatus(booking, 'cancelled')">Decline</Button>
                  <Button size="sm" type="button" :disabled="saving" @click="setBookingStatus(booking, 'confirmed')">Confirm</Button>
                </div>
                <Button
                  v-else-if="booking.status === 'confirmed'"
                  size="sm"
                  variant="outline"
                  type="button"
                  @click="setBookingStatus(booking, 'completed')"
                >
                  Complete
                </Button>
              </article>
            </div>
          </CardContent>
        </Card>
      </div>
        </TabsContent>

      </Tabs>

        </TabsContent>

        <TabsContent value="layouts" class="mt-0">
      <section class="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div class="flex flex-col justify-between gap-4 border-b p-5 sm:flex-row sm:items-start sm:p-6">
          <div class="flex items-start gap-3">
            <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Building2 class="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <p class="text-xs font-bold uppercase tracking-[0.16em] text-primary">Venue studio</p>
              <h2 class="mt-1 text-xl font-black tracking-tight sm:text-2xl">Reusable spaces for every occasion</h2>
              <p class="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                Build each floor once, then reuse it whenever needed. Several venues can host bookings on the same date without creating a new floor plan for that day.
              </p>
            </div>
          </div>
          <Button size="sm" type="button" class="shrink-0" @click="openLayoutEditor"><Plus class="h-4 w-4" aria-hidden="true" />New layout</Button>
        </div>

        <dl class="grid gap-3 border-b bg-muted/20 p-4 sm:grid-cols-2 xl:grid-cols-4">
          <div class="flex items-center gap-3 rounded-xl border bg-background p-4 shadow-sm"><span class="grid h-10 w-10 place-items-center rounded-lg bg-sky-100 text-sky-700"><LayoutGrid class="h-5 w-5" aria-hidden="true" /></span><div><dt class="text-xs font-semibold text-muted-foreground">Floor elements</dt><dd class="mt-0.5 text-xl font-black tabular-nums">{{ displayedResources.length }}</dd></div></div>
          <div class="flex items-center gap-3 rounded-xl border bg-background p-4 shadow-sm"><span class="grid h-10 w-10 place-items-center rounded-lg bg-violet-100 text-violet-700"><Users class="h-5 w-5" aria-hidden="true" /></span><div><dt class="text-xs font-semibold text-muted-foreground">Guest capacity</dt><dd class="mt-0.5 text-xl font-black tabular-nums">{{ venueCapacity }}</dd></div></div>
          <div class="flex items-center gap-3 rounded-xl border bg-background p-4 shadow-sm"><span class="grid h-10 w-10 place-items-center rounded-lg bg-emerald-100 text-emerald-700"><Armchair class="h-5 w-5" aria-hidden="true" /></span><div><dt class="text-xs font-semibold text-muted-foreground">Seats available</dt><dd class="mt-0.5 text-xl font-black tabular-nums text-emerald-700">{{ availableCapacity }}</dd></div></div>
          <div class="flex items-center gap-3 rounded-xl border bg-background p-4 shadow-sm"><span class="grid h-10 w-10 place-items-center rounded-lg bg-amber-100 text-amber-700"><CalendarCheck2 class="h-5 w-5" aria-hidden="true" /></span><div><dt class="text-xs font-semibold text-muted-foreground">Bookings on {{ shortSelectedDate }}</dt><dd class="mt-0.5 text-xl font-black tabular-nums">{{ selectedVenueBookings.length }}</dd></div></div>
        </dl>

        <div class="grid lg:grid-cols-[15rem_minmax(0,1fr)]">
          <aside class="border-b bg-muted/15 p-4 lg:border-b-0 lg:border-r">
            <div class="mb-4 grid gap-2 border-b pb-4">
              <Label for="venue-preview-date">Preview date</Label>
              <ScheduleDatePicker
                id="venue-preview-date"
                v-model="selectedDay"
                label="Venue availability preview date"
                @change="refreshSelectedDay"
              />
              <p class="text-[11px] leading-4 text-muted-foreground">This changes availability only. The floor plan remains reusable.</p>
            </div>
            <div class="grid gap-2">
              <Label>Editing layout</Label>
              <Select v-model="selectedLayoutId">
                <SelectTrigger><SelectValue placeholder="Choose a venue layout" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Unassigned floor</SelectItem>
                  <SelectItem v-for="layout in resourceLayouts" :key="layout.public_id" :value="layout.public_id">
                    {{ layout.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div v-if="selectedLayout" class="mt-4 rounded-xl border bg-background p-3">
              <div class="flex items-center gap-2">
                <PartyPopper v-if="selectedLayout.layout_type === 'event'" class="h-4 w-4 text-primary" aria-hidden="true" />
                <UtensilsCrossed v-else-if="selectedLayout.layout_type === 'restaurant'" class="h-4 w-4 text-primary" aria-hidden="true" />
                <LayoutGrid v-else class="h-4 w-4 text-primary" aria-hidden="true" />
                <p class="text-sm font-bold">{{ layoutTypeLabel(selectedLayout.layout_type) }}</p>
              </div>
              <p class="mt-2 text-xs leading-5 text-muted-foreground">{{ selectedLayout.description || 'A flexible venue canvas for this location.' }}</p>
            </div>
            <VenueLocationMap class="mt-4" :location="selectedVenueLocation" />
            <div class="mt-5">
              <p class="text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">Add an element</p>
              <div class="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-1">
                <Button
                  v-for="element in venueElementOptions"
                  :key="element.value"
                  variant="outline"
                  size="sm"
                  class="justify-start bg-background"
                  type="button"
                  @click="openResourceEditor(null, element.value)"
                >
                  <component :is="element.icon" class="h-4 w-4 text-primary" aria-hidden="true" />
                  {{ element.label }}
                </Button>
              </div>
            </div>
            <Button variant="ghost" class="mt-4 w-full justify-start" type="button" @click="openLayoutEditor">
              <Plus class="h-4 w-4" aria-hidden="true" />
              New layout
            </Button>
          </aside>

          <div class="min-w-0 p-4 sm:p-5">
            <div class="mb-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <div>
                <p class="font-bold">{{ selectedLayout?.name || 'Unassigned floor' }}</p>
                <p class="mt-1 text-xs text-muted-foreground">Availability shown for {{ selectedLabel }}. Drag any element to refine the venue plan.</p>
              </div>
              <div class="flex flex-wrap gap-2">
                <Button size="sm" variant="outline" type="button" @click="openResourceEditor(null, 'table')">
                  <Armchair class="h-4 w-4" aria-hidden="true" />
                  Add seating
                </Button>
                <Button size="sm" type="button" @click="floorExpanded = true">
                  <Maximize2 class="h-4 w-4" aria-hidden="true" />
                  Fullscreen plan
                </Button>
              </div>
            </div>
            <ResourceFloorPlan
              :resources="displayedResources"
              :bookings="selectedBookings"
              :selected-resource-id="selectedResource?.public_id || ''"
              :resource-word="resourceWord"
              @select="openResourceDetails"
              @move="persistResourceMove"
            />
          </div>
        </div>
      </section>
        </TabsContent>

        <TabsContent value="setup" class="mt-0">
      <Card class="border-primary/20 bg-primary/[.03]">
        <CardHeader class="pb-3">
          <CardTitle class="flex items-center gap-2 text-base">
            <SlidersHorizontal class="h-4 w-4 text-primary" aria-hidden="true" />
            Scheduling setup
          </CardTitle>
          <CardDescription>Manage the staff hours and capacity sessions that power public availability.</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs default-value="availability" class="space-y-4">
            <TabsList class="h-auto w-full justify-start overflow-x-auto sm:w-auto">
              <TabsTrigger value="availability">Availability</TabsTrigger>
              <TabsTrigger value="sessions">Sessions</TabsTrigger>
              <TabsTrigger value="all-bookings">All {{ bookingPlural.toLowerCase() }}</TabsTrigger>
            </TabsList>

            <TabsContent value="availability" class="mt-0">
              <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
                <div class="overflow-hidden rounded-xl border bg-card">
                  <StatePanel v-if="!availability.length" title="No availability yet" message="Add recurring staff hours and assign a published service." />
                  <div v-else class="divide-y">
                    <article v-for="item in availability" :key="item.public_id" class="grid gap-2 p-4 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center">
                      <div>
                        <p class="font-bold">{{ staffName(item.staff_public_id) }}</p>
                        <p class="mt-1 text-sm text-muted-foreground">{{ weekdayNames[item.weekday] }} · {{ shortTime(item.starts_at) }}–{{ shortTime(item.ends_at) }}</p>
                      </div>
                      <span class="text-sm text-muted-foreground">{{ locationName(item.location_public_id) }}</span>
                      <StatusPill :value="item.is_active ? 'active' : 'disabled'" />
                    </article>
                  </div>
                </div>
                <Card class="h-fit">
                  <CardHeader><CardTitle class="text-base">Add weekly hours</CardTitle><CardDescription>The service is assigned to this employee automatically.</CardDescription></CardHeader>
                  <CardContent>
                    <form class="space-y-4" @submit.prevent="createAvailability">
                      <div class="grid gap-2"><Label>Employee</Label><Select v-model="availabilityForm.staff_public_id"><SelectTrigger><SelectValue placeholder="Choose employee" /></SelectTrigger><SelectContent><SelectItem v-for="member in bookableStaff" :key="member.public_id" :value="member.public_id">{{ member.display_name }}</SelectItem></SelectContent></Select></div>
                      <div class="grid gap-2"><Label>Published service</Label><Select v-model="availabilityForm.offering_public_id"><SelectTrigger><SelectValue placeholder="Choose service" /></SelectTrigger><SelectContent><SelectItem v-for="offering in serviceOfferings" :key="offering.public_id" :value="offering.public_id">{{ offering.name }}</SelectItem></SelectContent></Select></div>
                      <div class="grid gap-2"><Label>Weekday</Label><Select v-model="availabilityForm.weekday"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="(day, index) in weekdayNames" :key="day" :value="String(index)">{{ day }}</SelectItem></SelectContent></Select></div>
                      <div class="grid grid-cols-2 gap-3"><div class="grid gap-2"><Label for="availability-start">Starts</Label><Input id="availability-start" v-model="availabilityForm.starts_at" type="time" required /></div><div class="grid gap-2"><Label for="availability-end">Ends</Label><Input id="availability-end" v-model="availabilityForm.ends_at" type="time" required /></div></div>
                      <Button class="w-full" :disabled="saving || !canAddAvailability">Add availability</Button>
                    </form>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="sessions" class="mt-0">
              <StatePanel v-if="!sessions.length" title="No group sessions" message="Capacity-limited service sessions will appear here when scheduled." />
              <div v-else class="divide-y rounded-xl border bg-card">
                <article v-for="session in sessions" :key="session.public_id" class="grid gap-2 p-4 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center">
                  <div><p class="font-bold">{{ offeringName(session.offering_public_id) }}</p><p class="mt-1 text-sm text-muted-foreground">{{ formatDate(session.starts_at) }} · {{ formatTime(session.starts_at) }}–{{ formatTime(session.ends_at) }}</p></div>
                  <span class="text-sm text-muted-foreground">Capacity {{ session.capacity }}</span>
                  <StatusPill :value="session.status" />
                </article>
              </div>
            </TabsContent>

            <TabsContent value="all-bookings" class="mt-0">
              <div class="overflow-x-auto rounded-xl border bg-card">
                <Table class="min-w-[70rem]">
                  <TableHeader><TableRow><TableHead>Booking ID</TableHead><TableHead>Customer</TableHead><TableHead>Service</TableHead><TableHead>Date &amp; time</TableHead><TableHead>Staff / resource</TableHead><TableHead>Payment</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                  <TableBody>
                    <TableRow v-for="booking in bookings" :key="booking.public_id">
                      <TableCell><span class="font-mono text-xs font-bold text-primary">{{ booking.confirmation_code }}</span></TableCell>
                      <TableCell><p class="font-bold">{{ customerName(booking) }}</p></TableCell>
                      <TableCell>{{ booking.offering_name }}</TableCell>
                      <TableCell><p>{{ formatDate(booking.starts_at) }}</p><p class="mt-1 text-xs text-muted-foreground">{{ formatTime(booking.starts_at) }}–{{ formatTime(booking.ends_at) }}</p></TableCell>
                      <TableCell><p>{{ booking.staff_name || 'Auto assigned' }}</p><p class="mt-1 text-xs text-muted-foreground">{{ booking.resources?.map(item => item.name).join(', ') || 'No resource' }}</p></TableCell>
                      <TableCell><StatusPill :value="booking.payment_status" /></TableCell>
                      <TableCell><StatusPill :value="booking.status" /></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
        </TabsContent>

        <TabsContent value="events" class="mt-0">
          <EventRsvpWorkspace
            mode="index"
            :business-id="business.activeBusiness.public_id"
            :locations="locations"
            :layouts="resourceLayouts"
            :resources="resources"
            :resource-types="resourceTypes"
            :staff="staff"
            :products="offerings"
          />
        </TabsContent>
      </Tabs>
    </template>

    <Dialog v-model:open="taskOpen">
      <DialogContent class="sm:max-w-lg">
        <form @submit.prevent="createEvent">
          <DialogHeader><DialogTitle>Add business task</DialogTitle><DialogDescription>Schedule internal work beside customer bookings.</DialogDescription></DialogHeader>
          <div class="mt-6 space-y-4">
            <div class="grid gap-2"><Label for="event-title">Task title</Label><Input id="event-title" v-model.trim="eventForm.title" required placeholder="Prepare the front desk" /></div>
            <div class="grid gap-2"><Label>Type</Label><Select v-model="eventForm.event_type"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="task">Task</SelectItem><SelectItem value="meeting">Meeting</SelectItem><SelectItem value="event">Event or function</SelectItem><SelectItem value="deadline">Deadline</SelectItem><SelectItem value="other">Other</SelectItem></SelectContent></Select></div>
            <div class="grid gap-2"><Label>Venue layout</Label><Select v-model="eventForm.resource_layout_public_id"><SelectTrigger><SelectValue placeholder="No venue" /></SelectTrigger><SelectContent><SelectItem value="none">No venue</SelectItem><SelectItem v-for="layout in resourceLayouts" :key="layout.public_id" :value="layout.public_id">{{ layout.name }}</SelectItem></SelectContent></Select><p class="text-xs leading-5 text-muted-foreground">Associate the task or event with a reusable floor plan. Multiple venue plans can be used on the same date.</p></div>
            <div class="grid gap-4 sm:grid-cols-2"><div class="grid gap-2"><Label for="event-start">Starts</Label><Input id="event-start" v-model="eventForm.starts_at" type="datetime-local" required /></div><div class="grid gap-2"><Label for="event-end">Ends</Label><Input id="event-end" v-model="eventForm.ends_at" type="datetime-local" /></div></div>
            <div class="grid gap-2"><Label for="event-notes">Notes</Label><Textarea id="event-notes" v-model.trim="eventForm.notes" rows="3" /></div>
          </div>
          <DialogFooter class="mt-6"><Button variant="outline" type="button" @click="taskOpen = false">Cancel</Button><Button :disabled="saving">{{ saving ? 'Saving…' : 'Save task' }}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="bookingOpen">
      <DialogContent class="max-h-[92vh] overflow-y-auto sm:max-w-xl">
        <form @submit.prevent="createBooking">
          <DialogHeader><DialogTitle>Add a {{ bookingSingular.toLowerCase() }}</DialogTitle><DialogDescription>Assign a service, customer, time, and optional resource.</DialogDescription></DialogHeader>
          <div class="grid gap-4 py-4">
            <div class="grid gap-2"><Label>Service</Label><Select v-model="bookingForm.offering_public_id"><SelectTrigger><SelectValue placeholder="Choose a published service" /></SelectTrigger><SelectContent><SelectItem v-for="offering in serviceOfferings" :key="offering.public_id" :value="offering.public_id">{{ offering.name }}</SelectItem></SelectContent></Select></div>
            <div class="grid gap-4 sm:grid-cols-2"><div class="grid gap-2"><Label for="booking-first">First name</Label><Input id="booking-first" v-model.trim="bookingForm.first_name" required /></div><div class="grid gap-2"><Label for="booking-last">Last name</Label><Input id="booking-last" v-model.trim="bookingForm.last_name" required /></div></div>
            <div class="grid gap-4 sm:grid-cols-2"><div class="grid gap-2"><Label for="booking-email">Email</Label><Input id="booking-email" v-model.trim="bookingForm.email" type="email" /></div><div class="grid gap-2"><Label for="booking-phone">Phone</Label><Input id="booking-phone" v-model.trim="bookingForm.phone" type="tel" /></div></div>
            <div class="grid gap-4 sm:grid-cols-2"><div class="grid gap-2"><Label for="booking-start">Starts</Label><Input id="booking-start" v-model="bookingForm.starts_at" type="datetime-local" required /></div><div class="grid gap-2"><Label for="booking-end">Ends</Label><Input id="booking-end" v-model="bookingForm.ends_at" type="datetime-local" required /></div></div>
            <div class="grid gap-4 sm:grid-cols-[1fr_8rem]"><div class="grid gap-2"><Label>{{ resourceWord }}</Label><Select v-model="bookingForm.resource_public_id"><SelectTrigger><SelectValue placeholder="No preference" /></SelectTrigger><SelectContent><SelectItem value="none">No preference</SelectItem><SelectItem v-for="resource in activeResources" :key="resource.public_id" :value="resource.public_id">{{ resource.name }} · {{ resource.capacity }} capacity</SelectItem></SelectContent></Select></div><div class="grid gap-2"><Label for="booking-seats">{{ isRestaurant ? 'Guests' : 'People' }}</Label><Input id="booking-seats" v-model.number="bookingForm.seats" type="number" min="1" max="50" required /></div></div>
            <div class="grid gap-2"><Label for="booking-customer-notes">Notes</Label><Textarea id="booking-customer-notes" v-model.trim="bookingForm.customer_notes" rows="2" /></div>
          </div>
          <DialogFooter><Button variant="outline" type="button" @click="bookingOpen = false">Cancel</Button><Button :disabled="saving || !canCreateBooking">{{ saving ? 'Saving…' : `Save ${bookingSingular.toLowerCase()}` }}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="resourceEditorOpen">
      <DialogContent class="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <form @submit.prevent="saveResource">
          <DialogHeader><DialogTitle>{{ editingResourceId ? 'Edit venue element' : 'Add venue element' }}</DialogTitle><DialogDescription>Define its role, shape, capacity, and position in this venue plan.</DialogDescription></DialogHeader>
          <div class="grid gap-4 py-4">
            <div class="grid gap-4 sm:grid-cols-[1fr_10rem]">
              <div class="grid gap-2"><Label for="resource-name">Display name</Label><Input id="resource-name" v-model.trim="resourceForm.name" required placeholder="Sweetheart table, Main stage…" /></div>
              <div class="grid gap-2"><Label for="resource-capacity">Capacity</Label><Input id="resource-capacity" v-model.number="resourceForm.capacity" type="number" min="1" max="999" required /></div>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="grid gap-2"><Label>Element</Label><Select v-model="resourceForm.element_type" @update:model-value="applyElementDefaults"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="element in venueElementOptions" :key="element.value" :value="element.value">{{ element.label }}</SelectItem><SelectItem value="service">Service area</SelectItem><SelectItem value="decor">Decor or landmark</SelectItem></SelectContent></Select></div>
              <div class="grid gap-2"><Label>Layout</Label><Select v-model="resourceForm.layout_public_id"><SelectTrigger><SelectValue placeholder="Choose layout" /></SelectTrigger><SelectContent><SelectItem value="none">Unassigned floor</SelectItem><SelectItem v-for="layout in layoutsAtLocation" :key="layout.public_id" :value="layout.public_id">{{ layout.name }}</SelectItem></SelectContent></Select></div>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="grid gap-2"><Label>Resource type</Label><Select v-model="resourceForm.resource_type_public_id"><SelectTrigger><SelectValue placeholder="Choose type" /></SelectTrigger><SelectContent><SelectItem v-for="type in resourceTypes" :key="type.public_id" :value="type.public_id">{{ type.singular_label }}</SelectItem></SelectContent></Select></div>
              <div class="grid gap-2"><Label>Location</Label><Select v-model="resourceForm.location_public_id"><SelectTrigger><SelectValue placeholder="Choose location" /></SelectTrigger><SelectContent><SelectItem v-for="location in locations" :key="location.public_id" :value="location.public_id">{{ location.name }}</SelectItem></SelectContent></Select></div>
            </div>
            <div class="grid gap-4 sm:grid-cols-4">
              <div class="grid gap-2"><Label>Shape</Label><Select v-model="resourceForm.shape"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="round">Round</SelectItem><SelectItem value="square">Square</SelectItem><SelectItem value="rectangle">Rectangle</SelectItem></SelectContent></Select></div>
              <div class="grid gap-2"><Label for="resource-width">Width %</Label><Input id="resource-width" v-model.number="resourceForm.width" type="number" min="4" max="80" /></div>
              <div class="grid gap-2"><Label for="resource-height">Height %</Label><Input id="resource-height" v-model.number="resourceForm.height" type="number" min="4" max="80" /></div>
              <div class="grid gap-2"><Label for="resource-rotation">Rotation</Label><Input id="resource-rotation" v-model.number="resourceForm.rotation" type="number" min="-180" max="180" /></div>
            </div>
            <div class="grid gap-3 sm:grid-cols-2">
              <div class="flex items-center justify-between rounded-xl border bg-muted/30 p-4"><div class="pr-4"><Label for="resource-bookable">Reservable element</Label><p class="mt-1 text-xs leading-5 text-muted-foreground">Tables, rooms, and booths can be selected by customers.</p></div><Switch id="resource-bookable" v-model:checked="resourceForm.is_bookable" /></div>
              <div class="flex items-center justify-between rounded-xl border bg-muted/30 p-4"><div class="pr-4"><Label for="resource-active">Visible on plan</Label><p class="mt-1 text-xs leading-5 text-muted-foreground">Hide an element without deleting its setup.</p></div><Switch id="resource-active" v-model:checked="resourceForm.is_active" /></div>
            </div>
          </div>
          <DialogFooter><Button variant="outline" type="button" @click="closeResourceEditor">Cancel</Button><Button v-if="resourceTypes.length" :disabled="saving">{{ saving ? 'Saving…' : editingResourceId ? 'Save changes' : 'Add to venue' }}</Button><Button v-else type="button" :disabled="saving" @click="createDefaultResourceType">Create resource type</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="layoutEditorOpen">
      <DialogContent class="sm:max-w-lg">
        <form @submit.prevent="createLayout">
          <DialogHeader><DialogTitle>Create venue layout</DialogTitle><DialogDescription>Start a dedicated floor plan for regular service, a wedding, an event, or a flexible room.</DialogDescription></DialogHeader>
          <div class="grid gap-4 py-5">
            <div class="grid gap-2"><Label for="layout-name">Layout name</Label><Input id="layout-name" v-model.trim="layoutForm.name" required placeholder="Garden wedding · 120 guests" /></div>
            <div class="grid gap-2"><Label>Layout purpose</Label><Select v-model="layoutForm.layout_type"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="restaurant">Restaurant dining</SelectItem><SelectItem value="event">Event or wedding</SelectItem><SelectItem value="room">Room or studio</SelectItem><SelectItem value="general">General venue</SelectItem></SelectContent></Select></div>
            <div class="grid gap-2"><Label>Location</Label><Select v-model="layoutForm.location_public_id"><SelectTrigger><SelectValue placeholder="Choose location" /></SelectTrigger><SelectContent><SelectItem v-for="location in locations" :key="location.public_id" :value="location.public_id">{{ location.name }}</SelectItem></SelectContent></Select></div>
            <div class="grid gap-2"><Label for="layout-description">Planning note</Label><Textarea id="layout-description" v-model.trim="layoutForm.description" rows="3" placeholder="Ceremony faces the garden stage; dinner service begins at 6 PM." /></div>
          </div>
          <DialogFooter><Button variant="outline" type="button" @click="layoutEditorOpen = false">Cancel</Button><Button :disabled="saving || !layoutForm.name || !layoutForm.location_public_id">{{ saving ? 'Creating…' : 'Create layout' }}</Button></DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="resourceDetailOpen">
      <DialogContent class="sm:max-w-xl">
        <DialogHeader><DialogTitle class="flex items-center gap-2"><span class="flex h-9 w-9 items-center justify-center rounded-lg" :class="selectedResource?.is_bookable ? (selectedResourceBookings.length ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700') : 'bg-sky-100 text-sky-700'"><LayoutGrid class="h-4 w-4" aria-hidden="true" /></span>{{ selectedResource?.name }}</DialogTitle><DialogDescription>{{ selectedResource?.is_bookable ? `${selectedResource?.capacity} capacity` : elementTypeLabel(selectedResource?.element_type) }} · {{ selectedResource?.is_active ? 'Visible' : 'Hidden' }} · {{ selectedLabel }}</DialogDescription></DialogHeader>
        <div v-if="selectedResource && !selectedResource.is_bookable" class="rounded-xl border border-sky-200 bg-sky-50 p-5 text-center"><Building2 class="mx-auto h-7 w-7 text-sky-700" aria-hidden="true" /><p class="mt-2 text-sm font-semibold text-sky-950">Venue feature</p><p class="mt-1 text-xs text-sky-700">This element helps plan the space but is not offered as a customer-selectable resource.</p></div>
        <div v-else-if="!selectedResourceBookings.length" class="rounded-xl border border-emerald-200 bg-emerald-50 p-5 text-center"><CheckCircle2 class="mx-auto h-7 w-7 text-emerald-600" aria-hidden="true" /><p class="mt-2 text-sm font-semibold text-emerald-900">Available all day</p><p class="mt-1 text-xs text-emerald-700">There are no bookings assigned to this resource.</p></div>
        <div v-else class="space-y-2"><article v-for="booking in selectedResourceBookings" :key="booking.public_id" class="rounded-xl border p-4"><div class="flex flex-wrap items-center gap-2"><p class="font-semibold">{{ customerName(booking) }}</p><StatusPill :value="booking.status" /></div><p class="mt-1 text-sm font-medium">{{ formatTime(booking.starts_at) }} – {{ formatTime(booking.ends_at) }}</p><p class="mt-1 text-xs text-muted-foreground">{{ booking.seats }} {{ guestWord }}</p></article></div>
        <DialogFooter><Button variant="destructive" type="button" :disabled="saving" @click="deleteSelectedResource"><Trash2 class="h-4 w-4" aria-hidden="true" />Delete</Button><Button variant="outline" type="button" @click="editSelectedResource"><Pencil class="h-4 w-4" aria-hidden="true" />Edit details</Button><Button v-if="selectedResource?.is_bookable" type="button" @click="bookSelectedResource"><Plus class="h-4 w-4" aria-hidden="true" />Add {{ bookingSingular.toLowerCase() }}</Button></DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="shareOpen">
      <DialogContent class="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader><DialogTitle class="flex items-center gap-2"><QrCode class="h-5 w-5 text-primary" aria-hidden="true" />Share public {{ bookingLabel.toLowerCase() }} form</DialogTitle><DialogDescription>Let customers scan this QR code or open the link to check live availability.</DialogDescription></DialogHeader>
        <div class="grid gap-5 py-2 sm:grid-cols-[220px_1fr] sm:items-start"><div class="rounded-2xl border bg-white p-4 shadow-sm"><div class="grid aspect-square place-items-center rounded-xl bg-white"><Loader2 v-if="qrLoading" class="h-7 w-7 animate-spin text-primary" aria-hidden="true" /><img v-else-if="qrCodeUrl" :src="qrCodeUrl" :alt="`${bookingLabel} QR code`" class="h-full w-full object-contain"></div><Button variant="outline" size="sm" class="mt-3 w-full" type="button" :disabled="!qrCodeUrl" @click="downloadQr"><Download class="h-4 w-4" aria-hidden="true" />Download QR</Button></div><div class="space-y-4"><div class="rounded-2xl border p-4"><div class="flex items-start justify-between gap-3"><div><p class="text-xs font-bold uppercase tracking-[0.16em] text-muted-foreground">Public status</p><p class="mt-1 font-semibold">{{ scheduleSettings.public_booking_enabled ? `Accepting ${bookingLabel.toLowerCase()} requests` : 'Public form is paused' }}</p></div><Badge :variant="scheduleSettings.public_booking_enabled ? 'secondary' : 'outline'">{{ scheduleSettings.public_booking_enabled ? 'Live' : 'Private' }}</Badge></div><p class="mt-2 text-xs leading-5 text-muted-foreground">Customers can select a service, date, time, group size, and an available {{ resourceWord.toLowerCase() }} when the form is enabled.</p></div><div class="grid gap-2"><Label for="public-booking-url">Public URL</Label><div class="flex gap-2"><Input id="public-booking-url" :model-value="absolutePublicBookingUrl" readonly class="min-w-0 font-mono text-xs" /><Button variant="outline" type="button" class="shrink-0" @click="copyBookingLink"><Check v-if="linkCopied" class="h-4 w-4 text-emerald-600" aria-hidden="true" /><Copy v-else class="h-4 w-4" aria-hidden="true" />{{ linkCopied ? 'Copied' : 'Copy' }}</Button></div></div><div class="rounded-xl bg-primary/5 p-4 text-xs leading-5">Print the QR code for your front desk, counter, receipt, display, or social posts.</div></div></div>
        <DialogFooter><ButtonAnchor variant="outline" :href="publicBookingUrl" target="_blank" rel="noopener"><ExternalLink class="h-4 w-4" aria-hidden="true" />Preview form</ButtonAnchor><Button type="button" @click="shareOpen = false">Done</Button></DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="floorExpanded">
      <DialogContent class="!bottom-3 !left-3 !right-3 !top-3 flex !h-auto !w-auto !max-w-none !translate-x-0 !translate-y-0 flex-col overflow-hidden rounded-xl p-0">
        <DialogHeader class="shrink-0 border-b px-6 py-5 pr-12"><DialogTitle>{{ resourceWord }} layout · {{ selectedLabel }}</DialogTitle><DialogDescription>Drag resources to rearrange them. Click any resource to view its bookings.</DialogDescription></DialogHeader>
        <div class="flex shrink-0 items-center gap-2 overflow-x-auto border-b bg-muted/20 px-5 py-3">
          <span class="shrink-0 text-xs font-bold uppercase tracking-[0.14em] text-muted-foreground">Add</span>
          <Button v-for="element in venueElementOptions" :key="element.value" size="sm" variant="outline" class="shrink-0 bg-background" type="button" @click="openResourceEditor(null, element.value, true)"><component :is="element.icon" class="h-4 w-4 text-primary" aria-hidden="true" />{{ element.label }}</Button>
        </div>
        <div class="min-h-0 flex-1 p-5"><ResourceFloorPlan expanded :resources="displayedResources" :bookings="selectedBookings" :selected-resource-id="selectedResource?.public_id || ''" :resource-word="resourceWord" @select="openResourceDetails" @move="persistResourceMove" /></div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import {
  Armchair,
  Building2,
  CalendarCheck2,
  CalendarClock,
  CalendarDays,
  CalendarHeart,
  CalendarRange,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Cloud,
  CloudOff,
  Copy,
  DoorOpen,
  Download,
  ExternalLink,
  GlassWater,
  Globe2,
  LayoutGrid,
  Maximize2,
  Music2,
  PartyPopper,
  Pencil,
  Plus,
  QrCode,
  RefreshCw,
  Shapes,
  Store,
  SlidersHorizontal,
  Trash2,
  UtensilsCrossed,
  Users,
  WandSparkles,
} from 'lucide-vue-next'
import QRCode from 'qrcode'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ButtonAnchor } from '@/components/ui/button-anchor'
import { ButtonLink } from '@/components/ui/button-link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import ResourceFloorPlan from '@/components/scheduling/ResourceFloorPlan.vue'
import EventRsvpWorkspace from '@/components/scheduling/EventRsvpWorkspace.vue'
import ScheduleDatePicker from '@/components/scheduling/ScheduleDatePicker.vue'
import VenueLocationMap from '@/components/scheduling/VenueLocationMap.vue'

useHead({ title: 'Calendar & bookings | PixelCore' })

const business = useBusinessStore()
const { apiFetch } = useApiClient()
const route = useRoute()

const events = ref([])
const bookings = ref([])
const resources = ref([])
const resourceLayouts = ref([])
const resourceTypes = ref([])
const locations = ref([])
const staff = ref([])
const offerings = ref([])
const availability = ref([])
const assignments = ref([])
const sessions = ref([])
const calendar = ref(null)
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const savingSettings = ref(false)
const activeWorkspaceTab = ref(route.query.tab === 'events' ? 'events' : 'calendar')
const calendarView = ref('month')
const taskOpen = ref(false)
const bookingOpen = ref(false)
const resourceEditorOpen = ref(false)
const returnToFloorAfterEdit = ref(false)
const layoutEditorOpen = ref(false)
const resourceDetailOpen = ref(false)
const floorExpanded = ref(false)
const shareOpen = ref(false)
const qrLoading = ref(false)
const qrCodeUrl = ref('')
const linkCopied = ref(false)
const appOrigin = ref('')
const editingResourceId = ref('')
const selectedLayoutId = ref('unassigned')
const selectedResource = ref(null)
const currentMonth = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
const selectedDay = ref(localIso(new Date()))
const weekdayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const weekdays = weekdayNames.map(day => day.slice(0, 3))

const eventForm = reactive({ title: '', event_type: 'task', starts_at: '', ends_at: '', notes: '', resource_layout_public_id: 'none' })
const bookingForm = reactive({ offering_public_id: '', resource_public_id: 'none', first_name: '', last_name: '', email: '', phone: '', seats: 2, starts_at: '', ends_at: '', customer_notes: '' })
const scheduleSettings = reactive({ public_booking_enabled: true, public_intro: '', advance_booking_days: 31 })
const layoutForm = reactive({ name: '', layout_type: 'restaurant', location_public_id: '', description: '', width: 100, height: 100, is_active: true })
const resourceForm = reactive({
  name: '',
  resource_type_public_id: '',
  location_public_id: '',
  layout_public_id: 'none',
  element_type: 'table',
  is_bookable: true,
  capacity: 2,
  shape: 'round',
  width: 16,
  height: 16,
  rotation: 0,
  position_x: 20,
  position_y: 20,
  is_active: true,
  metadata: {},
})
const availabilityForm = reactive({ staff_public_id: '', offering_public_id: '', location_public_id: '', weekday: '0', starts_at: '09:00', ends_at: '17:00', is_active: true })

const isRestaurant = computed(() => business.activeBusiness?.industry_preset === 'restaurant')
const bookingSingular = computed(() => isRestaurant.value ? 'Reservation' : 'Booking')
const bookingPlural = computed(() => isRestaurant.value ? 'Reservations' : 'Bookings')
const bookingLabel = bookingSingular
const resourceWord = computed(() => isRestaurant.value ? 'Table' : 'Resource')
const guestWordSingular = computed(() => isRestaurant.value ? 'guest' : 'person')
const guestWord = computed(() => isRestaurant.value ? 'guests' : 'people')
const publicBookingUrl = computed(() => business.activeBusiness?.slug ? `/site/${business.activeBusiness.slug}/booking` : '')
const absolutePublicBookingUrl = computed(() => appOrigin.value ? `${appOrigin.value}${publicBookingUrl.value}` : publicBookingUrl.value)
const serviceOfferings = computed(() => offerings.value.filter(item => item.offering_type === 'service' && item.status === 'published'))
const bookableStaff = computed(() => staff.value.filter(item => item.is_active && item.is_bookable))
const activeResources = computed(() => resources.value.filter(item => item.is_active && item.is_bookable))
const selectedLayout = computed(() => resourceLayouts.value.find(item => item.public_id === selectedLayoutId.value) || null)
const selectedVenueLocation = computed(() => locations.value.find(item => item.public_id === selectedLayout.value?.location_public_id) || null)
const displayedResources = computed(() => resources.value.filter(item => (
  selectedLayoutId.value === 'unassigned'
    ? !item.layout_public_id
    : item.layout_public_id === selectedLayoutId.value
)))
const layoutsAtLocation = computed(() => resourceLayouts.value.filter(item => item.location_public_id === resourceForm.location_public_id))
const todayIso = computed(() => localIso(new Date()))
const monthLabel = computed(() => new Intl.DateTimeFormat('en-PH', { month: 'long', year: 'numeric' }).format(currentMonth.value))
const selectedLabel = computed(() => new Intl.DateTimeFormat('en-PH', { dateStyle: 'full' }).format(new Date(`${selectedDay.value}T12:00:00`)))
const shortSelectedDate = computed(() => new Intl.DateTimeFormat('en-PH', { month: 'short', day: 'numeric' }).format(new Date(`${selectedDay.value}T12:00:00`)))
const monthCells = computed(() => {
  const first = currentMonth.value
  const mondayOffset = (first.getDay() + 6) % 7
  const start = new Date(first)
  start.setDate(1 - mondayOffset)
  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(start)
    date.setDate(start.getDate() + index)
    return { iso: localIso(date), day: date.getDate(), current: date.getMonth() === first.getMonth() }
  })
})
const calendarItems = computed(() => [
  ...events.value.map(item => ({ ...item, key: `event-${item.id}`, kind: 'task' })),
  ...bookings.value.map(item => ({ ...item, key: `booking-${item.public_id}`, title: item.offering_name, kind: 'booking' })),
])
const selectedEvents = computed(() => events.value.filter(item => localIso(new Date(item.starts_at)) === selectedDay.value).sort(sortByStart))
const selectedBookings = computed(() => bookings.value.filter(item => localIso(new Date(item.starts_at)) === selectedDay.value).sort(sortByStart))
const selectedVenueBookings = computed(() => {
  const resourceIds = new Set(displayedResources.value.map(item => item.public_id))
  return selectedBookings.value.filter(booking => booking.resources?.some(resource => resourceIds.has(resource.public_id)))
})
const selectedResourceBookings = computed(() => selectedResource.value ? selectedBookings.value.filter(booking => booking.resources?.some(item => item.public_id === selectedResource.value.public_id)) : [])
const reservedResources = computed(() => activeResources.value.filter(resource => selectedBookings.value.some(booking => ['pending', 'confirmed'].includes(booking.status) && booking.resources?.some(item => item.public_id === resource.public_id))).length)
const availableResources = computed(() => Math.max(0, activeResources.value.length - reservedResources.value))
const venueCapacity = computed(() => displayedResources.value.filter(item => item.is_active && item.is_bookable).reduce((total, item) => total + Number(item.capacity || 0), 0))
const availableCapacity = computed(() => displayedResources.value.filter(item => item.is_active && item.is_bookable && !selectedBookings.value.some(booking => ['pending', 'confirmed'].includes(booking.status) && booking.resources?.some(resource => resource.public_id === item.public_id))).reduce((total, item) => total + Number(item.capacity || 0), 0))
const venueElementOptions = [
  { value: 'table', label: 'Table or seating', icon: Armchair },
  { value: 'stage', label: 'Stage', icon: PartyPopper },
  { value: 'dance_floor', label: 'Dance floor', icon: Music2 },
  { value: 'bar', label: 'Bar', icon: GlassWater },
  { value: 'buffet', label: 'Buffet station', icon: UtensilsCrossed },
  { value: 'entrance', label: 'Entrance', icon: DoorOpen },
  { value: 'booth', label: 'Booth or exhibit', icon: Store },
  { value: 'other', label: 'Custom element', icon: Shapes },
]
const canAddAvailability = computed(() => Boolean(availabilityForm.staff_public_id && availabilityForm.offering_public_id && availabilityForm.starts_at && availabilityForm.ends_at))
const canCreateBooking = computed(() => Boolean(bookingForm.offering_public_id && bookingForm.first_name && bookingForm.last_name && (bookingForm.email || bookingForm.phone) && bookingForm.starts_at && bookingForm.ends_at))
const metrics = computed(() => [
  { label: `Today's ${bookingPlural.value.toLowerCase()}`, value: bookings.value.filter(item => localIso(new Date(item.starts_at)) === todayIso.value && item.status !== 'cancelled').length, detail: 'Scheduled for today', icon: CalendarCheck2 },
  { label: 'Upcoming', value: bookings.value.filter(item => new Date(item.starts_at) >= new Date() && ['pending', 'confirmed'].includes(item.status)).length, detail: 'Pending and confirmed', icon: CalendarClock },
  { label: `Active ${resourceWord.value.toLowerCase()}s`, value: activeResources.value.length, detail: 'Capacity-limited assets', icon: LayoutGrid },
  { label: 'Bookable staff', value: bookableStaff.value.length, detail: calendar.value?.connected ? 'Google Calendar connected' : 'Google Calendar disconnected', icon: Users },
])

watch(() => business.activeBusiness?.public_id, load)
watch(() => route.query.tab, (tab) => {
  if (tab === 'events') activeWorkspaceTab.value = 'events'
})
onMounted(async () => {
  appOrigin.value = window.location.origin
  if (!business.activeBusiness) await business.loadBusinesses()
  await load()
})

async function load() {
  if (!business.activeBusiness) return
  loading.value = true
  error.value = ''
  try {
    const id = business.activeBusiness.public_id
    const first = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth(), 1)
    const last = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1, 1)
    const responses = await Promise.all([
      apiFetch(`businesses/${id}/events/?starts_after=${first.toISOString()}&starts_before=${last.toISOString()}`),
      apiFetch(`businesses/${id}/bookings/?page_size=100`),
      apiFetch(`businesses/${id}/resources/?page_size=100`),
      apiFetch(`businesses/${id}/resource-types/?page_size=100`),
      apiFetch(`businesses/${id}/resource-layouts/?page_size=100`),
      apiFetch(`businesses/${id}/locations/?page_size=100`),
      apiFetch(`businesses/${id}/staff/?page_size=100`),
      apiFetch(`businesses/${id}/offerings/?page_size=100`),
      apiFetch(`businesses/${id}/availability/?page_size=100`),
      apiFetch(`businesses/${id}/service-assignments/?page_size=100`),
      apiFetch(`businesses/${id}/sessions/?page_size=100`),
      apiFetch(`businesses/${id}/google-calendar/`).catch(() => null),
      apiFetch(`businesses/${id}/schedule-settings/`),
    ])
    events.value = normalizeList(responses[0])
    bookings.value = normalizeList(responses[1])
    resources.value = normalizeList(responses[2])
    resourceTypes.value = normalizeList(responses[3])
    resourceLayouts.value = normalizeList(responses[4])
    locations.value = normalizeList(responses[5])
    staff.value = normalizeList(responses[6])
    offerings.value = normalizeList(responses[7])
    availability.value = normalizeList(responses[8])
    assignments.value = normalizeList(responses[9])
    sessions.value = normalizeList(responses[10])
    calendar.value = responses[11]
    Object.assign(scheduleSettings, responses[12])
    if (selectedLayoutId.value === 'unassigned' && resourceLayouts.value.length && !resources.value.some(item => !item.layout_public_id)) {
      selectedLayoutId.value = resourceLayouts.value[0].public_id
    }
    resourceForm.resource_type_public_id ||= resourceTypes.value[0]?.public_id || ''
    resourceForm.location_public_id ||= locations.value[0]?.public_id || ''
    layoutForm.location_public_id ||= locations.value[0]?.public_id || ''
    availabilityForm.staff_public_id ||= bookableStaff.value[0]?.public_id || ''
    availabilityForm.offering_public_id ||= serviceOfferings.value[0]?.public_id || ''
    availabilityForm.location_public_id ||= locations.value[0]?.public_id || ''
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || 'Could not load the current schedule.'
  } finally {
    loading.value = false
  }
}

async function moveMonth(amount) {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + amount, 1)
  selectedDay.value = localIso(currentMonth.value)
  await load()
}

async function goToday() {
  currentMonth.value = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  selectedDay.value = todayIso.value
  await load()
}

function selectDay(iso) {
  selectedDay.value = iso
  calendarView.value = 'day'
}

async function moveSelectedDay(amount) {
  const date = new Date(`${selectedDay.value}T12:00:00`)
  date.setDate(date.getDate() + amount)
  selectedDay.value = localIso(date)
  if (date.getMonth() !== currentMonth.value.getMonth() || date.getFullYear() !== currentMonth.value.getFullYear()) {
    currentMonth.value = new Date(date.getFullYear(), date.getMonth(), 1)
    await load()
  }
}

async function refreshSelectedDay() {
  const date = new Date(`${selectedDay.value}T12:00:00`)
  if (Number.isNaN(date.getTime())) return
  if (date.getMonth() !== currentMonth.value.getMonth() || date.getFullYear() !== currentMonth.value.getFullYear()) {
    currentMonth.value = new Date(date.getFullYear(), date.getMonth(), 1)
    await load()
  }
}

function openTaskEditor() {
  const start = defaultTime(16)
  const end = new Date(start.getTime() + 60 * 60 * 1000)
  Object.assign(eventForm, { title: '', event_type: 'task', starts_at: localDateTime(start), ends_at: localDateTime(end), notes: '', resource_layout_public_id: selectedLayoutId.value })
  taskOpen.value = true
}

function openBookingEditor(resource = null) {
  const start = defaultTime(18)
  const duration = Number(serviceOfferings.value[0]?.duration_minutes || 60)
  const end = new Date(start.getTime() + duration * 60 * 1000)
  Object.assign(bookingForm, {
    offering_public_id: serviceOfferings.value[0]?.public_id || '',
    resource_public_id: resource?.public_id || 'none',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    seats: 2,
    starts_at: localDateTime(start),
    ends_at: localDateTime(end),
    customer_notes: '',
  })
  bookingOpen.value = true
}

async function createEvent() {
  saving.value = true
  try {
    const created = await apiFetch(`businesses/${business.activeBusiness.public_id}/events/`, {
      method: 'POST',
      body: {
        ...eventForm,
        resource_layout_public_id: eventForm.resource_layout_public_id === 'none' ? null : eventForm.resource_layout_public_id,
        starts_at: toIso(eventForm.starts_at),
        ends_at: toIso(eventForm.ends_at),
        status: 'planned',
      },
    })
    events.value.push(created)
    taskOpen.value = false
    toast({ title: 'Task added', description: 'The task is now visible on the business calendar.' })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function createBooking() {
  saving.value = true
  try {
    const created = await apiFetch(`businesses/${business.activeBusiness.public_id}/bookings/`, {
      method: 'POST',
      body: {
        offering_public_id: bookingForm.offering_public_id,
        resource_public_ids: bookingForm.resource_public_id !== 'none' ? [bookingForm.resource_public_id] : [],
        location_public_id: resourceById(bookingForm.resource_public_id)?.location_public_id || locations.value[0]?.public_id || null,
        first_name: bookingForm.first_name,
        last_name: bookingForm.last_name,
        email: bookingForm.email,
        phone: bookingForm.phone,
        seats: Number(bookingForm.seats),
        starts_at: toIso(bookingForm.starts_at),
        ends_at: toIso(bookingForm.ends_at),
        timezone: business.activeBusiness.timezone || 'Asia/Manila',
        payment_method: 'manual',
        customer_notes: bookingForm.customer_notes,
      },
    })
    bookings.value.unshift(created)
    bookingOpen.value = false
    toast({ title: `${bookingSingular.value} added`, description: `${created.confirmation_code} is now on the schedule.` })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function setBookingStatus(booking, status) {
  saving.value = true
  try {
    Object.assign(booking, await apiFetch(`businesses/${business.activeBusiness.public_id}/bookings/${booking.public_id}/`, { method: 'PATCH', body: { status } }))
    toast({ title: `${bookingSingular.value} ${status}`, description: `${booking.confirmation_code} was updated.` })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function completeEvent(event) {
  try {
    Object.assign(event, await apiFetch(`businesses/${business.activeBusiness.public_id}/events/${event.id}/`, { method: 'PATCH', body: { status: 'completed' } }))
    toast({ title: 'Task completed' })
  } catch (requestError) {
    failedToast(requestError)
  }
}

function openResourceEditor(resource = null, elementType = 'table', returnToFloor = false) {
  returnToFloorAfterEdit.value = returnToFloor
  editingResourceId.value = resource?.public_id || ''
  const defaults = elementDefaults(resource?.element_type || elementType)
  Object.assign(resourceForm, {
    name: resource?.name || `${defaults.label} ${resources.value.length + 1}`,
    resource_type_public_id: resource?.resource_type_public_id || resourceTypes.value[0]?.public_id || '',
    location_public_id: resource?.location_public_id || selectedLayout.value?.location_public_id || locations.value[0]?.public_id || '',
    layout_public_id: resource?.layout_public_id || (selectedLayoutId.value !== 'unassigned' ? selectedLayoutId.value : 'none'),
    element_type: resource?.element_type || elementType,
    is_bookable: resource?.is_bookable ?? defaults.is_bookable,
    capacity: Number(resource?.capacity || 2),
    shape: resource?.shape || defaults.shape,
    width: Number(resource?.width || defaults.width),
    height: Number(resource?.height || defaults.height),
    rotation: Number(resource?.rotation || 0),
    position_x: Number(resource?.position_x ?? 20 + (resources.value.length * 17) % 60),
    position_y: Number(resource?.position_y ?? 25 + (resources.value.length * 13) % 50),
    is_active: resource?.is_active ?? true,
    metadata: resource?.metadata || {},
  })
  resourceDetailOpen.value = false
  floorExpanded.value = false
  resourceEditorOpen.value = true
}

function closeResourceEditor() {
  resourceEditorOpen.value = false
  if (returnToFloorAfterEdit.value) {
    returnToFloorAfterEdit.value = false
    floorExpanded.value = true
  }
}

function elementDefaults(elementType) {
  return {
    table: { label: isRestaurant.value ? 'Table' : 'Seating', shape: 'round', width: 16, height: 16, is_bookable: true },
    stage: { label: 'Stage', shape: 'rectangle', width: 38, height: 14, is_bookable: false },
    dance_floor: { label: 'Dance floor', shape: 'square', width: 28, height: 28, is_bookable: false },
    bar: { label: 'Bar', shape: 'rectangle', width: 30, height: 10, is_bookable: false },
    buffet: { label: 'Buffet', shape: 'rectangle', width: 30, height: 9, is_bookable: false },
    entrance: { label: 'Entrance', shape: 'rectangle', width: 18, height: 8, is_bookable: false },
    booth: { label: 'Booth', shape: 'rectangle', width: 18, height: 14, is_bookable: true },
    service: { label: 'Service area', shape: 'rectangle', width: 22, height: 10, is_bookable: false },
    decor: { label: 'Decor', shape: 'round', width: 10, height: 10, is_bookable: false },
    other: { label: 'Element', shape: 'square', width: 14, height: 14, is_bookable: false },
  }[elementType] || { label: 'Element', shape: 'square', width: 14, height: 14, is_bookable: false }
}

function applyElementDefaults(elementType) {
  const defaults = elementDefaults(elementType)
  resourceForm.element_type = elementType
  resourceForm.shape = defaults.shape
  resourceForm.width = defaults.width
  resourceForm.height = defaults.height
  resourceForm.is_bookable = defaults.is_bookable
  if (!editingResourceId.value) resourceForm.name = `${defaults.label} ${resources.value.length + 1}`
}

function layoutTypeLabel(value) {
  return {
    restaurant: 'Restaurant dining',
    event: 'Event or wedding',
    room: 'Room or studio',
    general: 'General venue',
  }[value] || 'General venue'
}

function elementTypeLabel(value) {
  return {
    table: 'Table or seating',
    stage: 'Stage',
    dance_floor: 'Dance floor',
    bar: 'Bar',
    buffet: 'Buffet station',
    entrance: 'Entrance',
    booth: 'Booth or exhibit',
    service: 'Service area',
    decor: 'Decor or landmark',
    other: 'Venue element',
  }[value] || 'Venue element'
}

function openLayoutEditor() {
  Object.assign(layoutForm, {
    name: '',
    layout_type: isRestaurant.value ? 'restaurant' : 'event',
    location_public_id: locations.value[0]?.public_id || '',
    description: '',
    width: 100,
    height: 100,
    is_active: true,
  })
  layoutEditorOpen.value = true
}

async function createLayout() {
  saving.value = true
  try {
    const created = await apiFetch(`businesses/${business.activeBusiness.public_id}/resource-layouts/`, {
      method: 'POST',
      body: { ...layoutForm },
    })
    resourceLayouts.value.push(created)
    selectedLayoutId.value = created.public_id
    layoutEditorOpen.value = false
    toast({ title: 'Venue layout created', description: `${created.name} is ready for tables and event elements.` })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function togglePublicBooking(nextValue = !scheduleSettings.public_booking_enabled) {
  const previousValue = scheduleSettings.public_booking_enabled
  scheduleSettings.public_booking_enabled = Boolean(nextValue)
  savingSettings.value = true
  try {
    const saved = await apiFetch(`businesses/${business.activeBusiness.public_id}/schedule-settings/`, {
      method: 'PATCH',
      body: { public_booking_enabled: scheduleSettings.public_booking_enabled },
    })
    Object.assign(scheduleSettings, saved)
    toast({
      title: saved.public_booking_enabled ? 'Public form enabled' : 'Public form paused',
      description: saved.public_booking_enabled
        ? 'Customers can now see availability and send requests.'
        : 'The public URL now shows that online booking is unavailable.',
    })
  } catch (requestError) {
    scheduleSettings.public_booking_enabled = previousValue
    failedToast(requestError)
  } finally {
    savingSettings.value = false
  }
}

async function saveResource() {
  saving.value = true
  try {
    const url = editingResourceId.value
      ? `businesses/${business.activeBusiness.public_id}/resources/${editingResourceId.value}/`
      : `businesses/${business.activeBusiness.public_id}/resources/`
    const saved = await apiFetch(url, {
      method: editingResourceId.value ? 'PATCH' : 'POST',
      body: {
        ...resourceForm,
        layout_public_id: resourceForm.layout_public_id === 'none' ? null : resourceForm.layout_public_id,
        capacity: Number(resourceForm.capacity),
        width: Number(resourceForm.width),
        height: Number(resourceForm.height),
        rotation: Number(resourceForm.rotation),
      },
    })
    if (editingResourceId.value) {
      Object.assign(resources.value.find(item => item.public_id === editingResourceId.value), saved)
    } else {
      resources.value.push(saved)
    }
    resourceEditorOpen.value = false
    if (returnToFloorAfterEdit.value) {
      returnToFloorAfterEdit.value = false
      floorExpanded.value = true
    }
    toast({ title: editingResourceId.value ? `${resourceWord.value} updated` : `${resourceWord.value} added`, description: 'The shared resource layout is up to date.' })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function createDefaultResourceType() {
  saving.value = true
  try {
    const created = await apiFetch(`businesses/${business.activeBusiness.public_id}/resource-types/`, {
      method: 'POST',
      body: { name: resourceWord.value, singular_label: resourceWord.value, plural_label: `${resourceWord.value}s`, icon: 'layout-grid', is_active: true },
    })
    resourceTypes.value.push(created)
    resourceForm.resource_type_public_id = created.public_id
    toast({ title: `${resourceWord.value} type created`, description: 'Complete the resource details and save.' })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

function openResourceDetails(resource) {
  selectedResource.value = resource
  resourceDetailOpen.value = true
}

function editSelectedResource() {
  if (selectedResource.value) openResourceEditor(selectedResource.value)
}

function bookSelectedResource() {
  const resource = selectedResource.value
  resourceDetailOpen.value = false
  floorExpanded.value = false
  openBookingEditor(resource)
}

async function deleteSelectedResource() {
  if (!selectedResource.value) return
  saving.value = true
  try {
    await apiFetch(`businesses/${business.activeBusiness.public_id}/resources/${selectedResource.value.public_id}/`, { method: 'DELETE' })
    resources.value = resources.value.filter(item => item.public_id !== selectedResource.value.public_id)
    resourceDetailOpen.value = false
    toast({ title: `${resourceWord.value} deleted`, description: 'It was removed from the public availability layout.' })
    selectedResource.value = null
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function persistResourceMove({ resource, position_x, position_y }) {
  const previous = { position_x: resource.position_x, position_y: resource.position_y }
  Object.assign(resource, { position_x, position_y })
  try {
    await apiFetch(`businesses/${business.activeBusiness.public_id}/resources/${resource.public_id}/`, { method: 'PATCH', body: { position_x, position_y } })
    toast({ title: `${resource.name} moved`, description: 'The layout position was saved.' })
  } catch (requestError) {
    Object.assign(resource, previous)
    failedToast(requestError)
  }
}

async function createAvailability() {
  saving.value = true
  try {
    const id = business.activeBusiness.public_id
    const assignmentExists = assignments.value.some(item => item.staff_public_id === availabilityForm.staff_public_id && item.offering_public_id === availabilityForm.offering_public_id && (item.location_public_id || '') === (availabilityForm.location_public_id || '') && item.is_active)
    if (!assignmentExists) {
      assignments.value.push(await apiFetch(`businesses/${id}/service-assignments/`, { method: 'POST', body: { staff_public_id: availabilityForm.staff_public_id, offering_public_id: availabilityForm.offering_public_id, location_public_id: availabilityForm.location_public_id || null, is_active: true } }))
    }
    availability.value.push(await apiFetch(`businesses/${id}/availability/`, { method: 'POST', body: { ...availabilityForm, weekday: Number(availabilityForm.weekday), location_public_id: availabilityForm.location_public_id || null } }))
    toast({ title: 'Availability saved', description: 'The public form now uses these weekly hours.' })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function syncCalendar() {
  saving.value = true
  try {
    const response = await apiFetch(`businesses/${business.activeBusiness.public_id}/google-calendar/sync/`, { method: 'POST' })
    calendar.value = await apiFetch(`businesses/${business.activeBusiness.public_id}/google-calendar/`)
    toast({ title: 'Google Calendar is up to date', description: `${response.synced} of ${response.total} events synced.` })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function openBookingShare() {
  if (!publicBookingUrl.value) return
  linkCopied.value = false
  shareOpen.value = true
  qrLoading.value = true
  try {
    qrCodeUrl.value = await QRCode.toDataURL(absolutePublicBookingUrl.value, { width: 720, margin: 2, errorCorrectionLevel: 'H' })
  } catch {
    qrCodeUrl.value = ''
    toast({ title: 'QR code could not be created', description: 'The public link can still be copied.', variant: 'destructive' })
  } finally {
    qrLoading.value = false
  }
}

async function copyBookingLink() {
  await navigator.clipboard.writeText(absolutePublicBookingUrl.value)
  linkCopied.value = true
  toast({ title: `${bookingSingular.value} link copied` })
}

function downloadQr() {
  if (!qrCodeUrl.value) return
  const anchor = document.createElement('a')
  anchor.href = qrCodeUrl.value
  anchor.download = `${business.activeBusiness.slug}-${bookingSingular.value.toLowerCase()}-qr.png`
  anchor.click()
}

function entriesFor(iso) {
  return calendarItems.value.filter(item => localIso(new Date(item.starts_at)) === iso).sort(sortByStart)
}

function dayCellClass(day) {
  return [day.current ? 'bg-card' : 'bg-muted/20 text-muted-foreground', selectedDay.value === day.iso ? 'z-10 bg-primary/[.055] ring-2 ring-inset ring-primary' : '']
}

function entryClass(entry) {
  if (entry.kind === 'booking') {
    if (['cancelled', 'no_show'].includes(entry.status)) return 'bg-slate-100 text-slate-500'
    if (entry.status === 'completed') return 'bg-emerald-100 text-emerald-800'
    return 'bg-sky-100 text-sky-800'
  }
  return { meeting: 'bg-violet-100 text-violet-800', event: 'bg-fuchsia-100 text-fuchsia-800', deadline: 'bg-amber-100 text-amber-800', task: 'bg-primary/10 text-primary', other: 'bg-muted text-muted-foreground' }[entry.event_type] || 'bg-muted text-muted-foreground'
}

function eventColor(type) {
  return { meeting: 'bg-violet-100 text-violet-700', event: 'bg-fuchsia-100 text-fuchsia-700', deadline: 'bg-amber-100 text-amber-700', task: 'bg-primary/10 text-primary', other: 'bg-muted text-muted-foreground' }[type] || 'bg-muted text-muted-foreground'
}

function eventIcon(type) {
  return type === 'event' ? PartyPopper : type === 'meeting' ? Users : type === 'deadline' ? CalendarClock : ClipboardList
}

function customerName(booking) {
  const customer = booking.customer || {}
  return [customer.first_name, customer.last_name].filter(Boolean).join(' ') || customer.email || customer.phone || 'Guest customer'
}

function resourceById(id) {
  return resources.value.find(item => item.public_id === id)
}

function staffName(id) {
  return staff.value.find(item => item.public_id === id)?.display_name || 'Employee'
}

function locationName(id) {
  return locations.value.find(item => item.public_id === id)?.name || 'Any location'
}

function offeringName(id) {
  return offerings.value.find(item => item.public_id === id)?.name || 'Service session'
}

function normalizeList(value) {
  return Array.isArray(value) ? value : value?.results || []
}

function sortByStart(left, right) {
  return new Date(left.starts_at) - new Date(right.starts_at)
}

function defaultTime(hour) {
  const date = new Date(`${selectedDay.value}T${String(hour).padStart(2, '0')}:00:00`)
  if (selectedDay.value === todayIso.value && date < new Date()) {
    date.setTime(Date.now() + 60 * 60 * 1000)
    date.setMinutes(0, 0, 0)
  }
  return date
}

function localIso(date) {
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 10)
}

function localDateTime(date) {
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 16)
}

function toIso(value) {
  return value ? new Date(value).toISOString() : null
}

function formatTime(value) {
  return new Intl.DateTimeFormat('en-PH', { hour: 'numeric', minute: '2-digit' }).format(new Date(value))
}

function shortTime(value) {
  return new Intl.DateTimeFormat('en-PH', { hour: 'numeric', minute: '2-digit' }).format(new Date(`2000-01-01T${value}`))
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value))
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function failedToast(requestError) {
  const payload = requestError?.data || {}
  const details = payload?.error?.details || payload
  const firstField = Object.values(details).find(value => Array.isArray(value) && value.length)?.[0]
  toast({ title: 'Schedule update failed', description: payload?.error?.message || payload?.detail || firstField || 'Check the details and try again.', variant: 'destructive' })
}
</script>
