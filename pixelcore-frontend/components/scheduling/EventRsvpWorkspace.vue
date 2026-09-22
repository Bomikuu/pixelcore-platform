<template>
  <div class="space-y-5">
    <div v-if="mode === 'detail'" class="flex flex-wrap items-center justify-between gap-3">
      <ButtonLink to="/workspace/schedule?tab=events" variant="outline" size="sm">
        <ArrowLeft class="h-4 w-4" aria-hidden="true" />
        Back to events
      </ButtonLink>
      <Badge variant="outline">Dedicated event workspace</Badge>
    </div>

    <Alert v-if="mode === 'index'" class="border-violet-200 bg-violet-50/70 text-violet-950">
      <PartyPopper class="h-4 w-4 text-violet-700" aria-hidden="true" />
      <AlertTitle>Events and appointments are separate</AlertTitle>
      <AlertDescription class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span>
          Weddings and private events use invitations, RSVP tracking, and assigned seating here. Restaurant
          reservations and service appointments stay in the Calendar tab.
        </span>
        <Button size="sm" class="shrink-0" type="button" @click="openEventDialog">
          <Plus class="h-4 w-4" aria-hidden="true" />
          New event
        </Button>
      </AlertDescription>
    </Alert>

    <StatePanel
      v-if="loading"
      kind="loading"
      title="Loading events"
      message="Retrieving event invitations, responses, and seating plans."
    />
    <StatePanel v-else-if="error" kind="error" title="Events unavailable" :message="error">
      <Button variant="outline" type="button" @click="loadEvents">Try again</Button>
    </StatePanel>

    <div v-else-if="!events.length" class="rounded-2xl border border-dashed bg-card px-6 py-14 text-center">
      <div class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-violet-100 text-violet-700">
        <CalendarHeart class="h-7 w-7" aria-hidden="true" />
      </div>
      <h2 class="mt-4 text-xl font-bold">
        {{ hasActiveFilters ? 'No events match these filters' : 'Create your first guest event' }}
      </h2>
      <p class="mx-auto mt-2 max-w-lg text-sm leading-6 text-muted-foreground">
        {{ hasActiveFilters
          ? 'Try a broader search or clear the status and event-type filters.'
          : 'Give a wedding, reception, or private function its own guest list and RSVP links without mixing it with daily bookings.' }}
      </p>
      <Button v-if="hasActiveFilters" class="mt-5" variant="outline" type="button" @click="clearFilters">
        Clear filters
      </Button>
      <Button v-else class="mt-5" type="button" @click="openEventDialog">
        <Plus class="h-4 w-4" aria-hidden="true" />
        Create event
      </Button>
    </div>

    <template v-else-if="mode === 'index'">
      <section class="rounded-2xl border bg-card shadow-sm">
        <div class="flex flex-col gap-4 border-b p-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 class="text-lg font-bold">Event directory</h2>
            <p class="mt-1 text-sm text-muted-foreground">{{ eventCount }} event{{ eventCount === 1 ? '' : 's' }} across all RSVP states.</p>
          </div>
          <div class="flex items-center gap-2">
            <Button
              type="button"
              size="icon"
              :variant="viewMode === 'grid' ? 'default' : 'outline'"
              aria-label="Grid view"
              @click="viewMode = 'grid'"
            >
              <Grid3X3 class="h-4 w-4" aria-hidden="true" />
            </Button>
            <Button
              type="button"
              size="icon"
              :variant="viewMode === 'table' ? 'default' : 'outline'"
              aria-label="Table view"
              @click="viewMode = 'table'"
            >
              <List class="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </div>

        <form class="grid gap-3 border-b bg-muted/15 p-4 md:grid-cols-[minmax(14rem,1fr)_11rem_11rem_auto]" @submit.prevent="applyFilters">
          <div class="relative">
            <Search class="pointer-events-none absolute left-3 top-3 h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <Input v-model.trim="search" class="pl-10" placeholder="Search event, organizer, or venue" aria-label="Search events" />
          </div>
          <Select v-model="statusFilter">
            <SelectTrigger aria-label="Filter event status"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="planning">Planning</SelectItem>
              <SelectItem value="open">RSVP open</SelectItem>
              <SelectItem value="closed">RSVP closed</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
          <Select v-model="typeFilter">
            <SelectTrigger aria-label="Filter event type"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All event types</SelectItem>
              <SelectItem value="wedding">Weddings</SelectItem>
              <SelectItem value="private_event">Private events</SelectItem>
              <SelectItem value="corporate">Corporate</SelectItem>
              <SelectItem value="community">Community</SelectItem>
              <SelectItem value="other">Other events</SelectItem>
            </SelectContent>
          </Select>
          <Button type="submit" variant="outline">Apply filters</Button>
        </form>

        <div v-if="viewMode === 'grid'" class="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3">
          <article
            v-for="event in events"
            :key="event.public_id"
            class="group overflow-hidden rounded-2xl border bg-background transition-[transform,box-shadow] hover:-translate-y-0.5 hover:shadow-lg"
          >
            <div class="relative aspect-[16/9] overflow-hidden bg-[#173d36]">
              <img
                v-if="event.thumbnail_url"
                :src="event.thumbnail_url"
                :alt="`${event.title} thumbnail`"
                class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.025]"
              >
              <div v-else class="flex h-full items-center justify-center text-emerald-100">
                <CalendarHeart class="h-12 w-12 opacity-80" aria-hidden="true" />
              </div>
              <div class="absolute inset-x-0 bottom-0 bg-slate-950/65 px-4 py-3 text-white">
                <p class="text-sm font-bold">{{ formatEventDate(event.starts_at) }}</p>
                <p class="mt-0.5 text-xs text-white/70">{{ event.location_name || 'Location not assigned' }}</p>
              </div>
            </div>
            <div class="space-y-4 p-4">
              <div>
                <div class="flex items-start justify-between gap-3">
                  <h3 class="text-lg font-bold leading-6">{{ event.title }}</h3>
                  <Badge :variant="event.status === 'open' ? 'secondary' : 'outline'" class="shrink-0">{{ statusLabel(event.status) }}</Badge>
                </div>
                <p class="mt-2 line-clamp-2 min-h-10 text-sm leading-5 text-muted-foreground">
                  {{ event.description || `${eventTypeLabel(event.event_type)} managed by ${event.organizer_name}.` }}
                </p>
              </div>
              <div class="grid grid-cols-2 gap-3 rounded-xl bg-muted/40 p-3 text-xs">
                <div><span class="block text-muted-foreground">Confirmed people</span><strong class="mt-1 block text-base tabular-nums">{{ event.guest_counts?.attending_people || 0 }} / {{ event.max_guests }}</strong></div>
                <div><span class="block text-muted-foreground">Awaiting</span><strong class="mt-1 block text-base tabular-nums">{{ event.guest_counts?.pending || 0 }}</strong></div>
              </div>
              <ButtonLink :to="eventPath(event)" class="w-full">
                Open event
                <ArrowRight class="h-4 w-4" aria-hidden="true" />
              </ButtonLink>
            </div>
          </article>
        </div>

        <div v-else class="overflow-x-auto">
          <Table class="min-w-[78rem]">
            <TableHeader>
              <TableRow>
                <TableHead class="pl-5">Event</TableHead>
                <TableHead>Date and venue</TableHead>
                <TableHead>Capacity</TableHead>
                <TableHead>Responses</TableHead>
                <TableHead>Organizer</TableHead>
                <TableHead>Status</TableHead>
                <TableHead class="pr-5 text-right">Manage</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="event in events" :key="event.public_id" class="transition-colors hover:bg-muted/40">
                <TableCell class="pl-5">
                  <div class="flex items-center gap-3">
                    <div class="h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-[#173d36]">
                      <img v-if="event.thumbnail_url" :src="event.thumbnail_url" alt="" class="h-full w-full object-cover">
                      <div v-else class="grid h-full place-items-center text-emerald-100"><CalendarHeart class="h-6 w-6" aria-hidden="true" /></div>
                    </div>
                    <div class="min-w-0">
                      <div class="flex items-center gap-2">
                        <p class="font-bold">{{ event.title }}</p>
                        <Badge variant="outline" class="shrink-0 text-[10px]">{{ eventTypeLabel(event.event_type) }}</Badge>
                      </div>
                      <p class="mt-1 max-w-sm line-clamp-2 text-xs leading-5 text-muted-foreground">
                        {{ event.description || `${eventTypeLabel(event.event_type)} managed by ${event.organizer_name}.` }}
                      </p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <p class="flex items-center gap-2 font-medium"><CalendarDays class="h-4 w-4 text-muted-foreground" aria-hidden="true" />{{ formatEventDate(event.starts_at) }}</p>
                  <p class="mt-1 flex items-center gap-2 text-xs text-muted-foreground"><MapPin class="h-3.5 w-3.5" aria-hidden="true" />{{ event.location_name || 'No venue' }}</p>
                </TableCell>
                <TableCell>
                  <div class="w-36">
                    <div class="flex items-center justify-between gap-3 text-xs"><span class="text-muted-foreground">Confirmed</span><strong class="tabular-nums">{{ event.guest_counts?.attending_people || 0 }} / {{ event.max_guests }}</strong></div>
                    <Progress class="mt-2 h-1.5" :model-value="capacityPercent(event)" />
                  </div>
                </TableCell>
                <TableCell>
                  <div class="flex gap-4 text-xs">
                    <span><strong class="block text-base tabular-nums">{{ event.guest_counts?.accepted || 0 }}</strong><span class="text-muted-foreground">Accepted</span></span>
                    <span><strong class="block text-base tabular-nums">{{ event.guest_counts?.pending || 0 }}</strong><span class="text-muted-foreground">Waiting</span></span>
                    <span><strong class="block text-base tabular-nums">{{ (event.guest_counts?.declined || 0) + (event.guest_counts?.maybe || 0) }}</strong><span class="text-muted-foreground">Other</span></span>
                  </div>
                </TableCell>
                <TableCell><p class="font-medium">{{ event.organizer_name }}</p><p class="mt-1 text-xs text-muted-foreground">{{ event.organizer_email || 'No email added' }}</p></TableCell>
                <TableCell><Badge :variant="event.status === 'open' ? 'secondary' : 'outline'">{{ statusLabel(event.status) }}</Badge></TableCell>
                <TableCell class="pr-5 text-right"><ButtonLink :to="eventPath(event)" size="sm" variant="outline">Open<ArrowRight class="h-4 w-4" aria-hidden="true" /></ButtonLink></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <RecordPagination :page="page" :count="eventCount" :size="pageSize" :busy="loading" @page="changePage" />
      </section>
    </template>

    <div v-else :class="mode === 'detail' ? 'block' : 'grid gap-5 xl:grid-cols-[19rem_minmax(0,1fr)]'">
      <Card v-if="mode !== 'detail'" class="h-fit overflow-hidden xl:sticky xl:top-4">
        <CardHeader class="border-b bg-muted/20 p-4">
          <div class="flex items-center justify-between gap-3">
            <div>
              <CardTitle class="text-base">Guest events</CardTitle>
              <CardDescription>{{ events.length }} event{{ events.length === 1 ? '' : 's' }}</CardDescription>
            </div>
            <Button size="icon" variant="outline" type="button" aria-label="Create event" @click="openEventDialog">
              <Plus class="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </CardHeader>
        <CardContent class="space-y-2 p-2">
          <Button
            v-for="event in events"
            :key="event.public_id"
            type="button"
            variant="ghost"
            class="h-auto w-full justify-start rounded-xl px-3 py-3 text-left"
            :class="event.public_id === selectedEventId ? 'bg-primary/8 ring-1 ring-primary/20' : ''"
            @click="selectEvent(event.public_id)"
          >
            <span class="min-w-0 flex-1">
              <span class="flex items-center justify-between gap-2">
                <span class="truncate font-bold">{{ event.title }}</span>
                <Badge :variant="event.status === 'open' ? 'secondary' : 'outline'" class="shrink-0 capitalize">
                  {{ event.status }}
                </Badge>
              </span>
              <span class="mt-1 block text-xs text-muted-foreground">
                {{ formatEventDate(event.starts_at) }}
              </span>
              <span class="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                <Users class="h-3.5 w-3.5" aria-hidden="true" />
                {{ event.guest_counts?.accepted || 0 }} attending · {{ event.guest_counts?.pending || 0 }} waiting
              </span>
            </span>
          </Button>
        </CardContent>
      </Card>

      <div v-if="selectedEvent" class="min-w-0 space-y-5">
        <section class="overflow-hidden rounded-2xl border bg-[#102f2a] text-white shadow-sm">
          <div class="grid gap-0 lg:grid-cols-[minmax(0,1fr)_19rem]">
            <div class="p-5 sm:p-6">
              <div class="flex flex-wrap items-center gap-2">
                <Badge class="border-white/15 bg-white/10 text-white hover:bg-white/10">
                  {{ eventTypeLabel(selectedEvent.event_type) }}
                </Badge>
                <Badge class="border-emerald-200/20 bg-emerald-200/10 text-emerald-100 hover:bg-emerald-200/10">
                  {{ selectedEvent.status === 'open' ? 'RSVP open' : statusLabel(selectedEvent.status) }}
                </Badge>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  class="h-6 gap-1.5 rounded-full border border-white/15 bg-white/10 px-2.5 text-xs text-white hover:bg-white/15 hover:text-white"
                  @click="openCapacityDialog"
                >
                  <Users class="h-3.5 w-3.5" aria-hidden="true" />
                  Maximum {{ selectedEvent.max_guests }} people
                </Button>
              </div>
              <h2 class="mt-4 text-2xl font-black tracking-tight sm:text-3xl">{{ selectedEvent.title }}</h2>
              <div class="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-white/75">
                <span class="flex items-center gap-2">
                  <CalendarDays class="h-4 w-4" aria-hidden="true" />
                  {{ formatEventDateTime(selectedEvent.starts_at) }}
                </span>
                <span class="flex items-center gap-2">
                  <MapPin class="h-4 w-4" aria-hidden="true" />
                  {{ selectedEvent.location_name || 'Location not assigned' }}
                </span>
                <span class="flex items-center gap-2">
                  <LayoutGrid class="h-4 w-4" aria-hidden="true" />
                  {{ selectedEvent.layout_name || 'No floor plan' }}
                </span>
                <span class="flex items-center gap-2">
                  <UserRoundCog class="h-4 w-4" aria-hidden="true" />
                  {{ selectedEvent.handler_name || 'No staff handler' }}
                </span>
              </div>
            </div>
            <div class="border-t border-white/10 bg-black/10 p-5 lg:border-l lg:border-t-0">
              <p class="text-xs font-bold uppercase tracking-[0.16em] text-emerald-200">Organizer access</p>
              <p class="mt-2 text-sm leading-6 text-white/75">
                Review the current private link, copy it, or deliberately replace it when access needs to change.
              </p>
              <Button
                type="button"
                size="sm"
                class="mt-4 w-full bg-white text-emerald-950 hover:bg-emerald-50"
                :disabled="saving"
                @click="openOrganizerLinkDialog"
              >
                <Link2 class="h-4 w-4" aria-hidden="true" />
                Manage organizer link
              </Button>
            </div>
          </div>
        </section>

        <Tabs v-model="activeTab" class="space-y-5">
          <div class="overflow-x-auto">
            <TabsList class="h-auto min-w-max">
              <TabsTrigger value="details">
                <FilePenLine class="h-4 w-4" aria-hidden="true" />
                Event details
              </TabsTrigger>
              <TabsTrigger value="website">
                <PanelsTopLeft class="h-4 w-4" aria-hidden="true" />
                Event website
              </TabsTrigger>
              <TabsTrigger value="guests">
                <Users class="h-4 w-4" aria-hidden="true" />
                Guests & seating
              </TabsTrigger>
              <TabsTrigger value="rsvp">
                <MailCheck class="h-4 w-4" aria-hidden="true" />
                RSVP customization
              </TabsTrigger>
              <TabsTrigger value="staff">
                <UserRoundCog class="h-4 w-4" aria-hidden="true" />
                Staff
              </TabsTrigger>
              <TabsTrigger value="products">
                <PackageOpen class="h-4 w-4" aria-hidden="true" />
                Products & services
              </TabsTrigger>
              <TabsTrigger value="venue">
                <PencilRuler class="h-4 w-4" aria-hidden="true" />
                Venue layout
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="staff">
            <EventStaffTab
              :business-id="businessId"
              :event="selectedEvent"
              :staff="staff"
              @updated="handleEventUpdated"
            />
          </TabsContent>

          <TabsContent value="details">
            <EventDetailsTab
              :business-id="businessId"
              :event="selectedEvent"
              :locations="locations"
              :layouts="layouts"
              @updated="handleEventUpdated"
            />
          </TabsContent>

          <TabsContent value="guests" class="space-y-5">
            <dl class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4">
              <div
                v-for="metric in metrics"
                :key="metric.label"
                class="border-b p-4 sm:border-r xl:border-b-0 last:border-r-0"
              >
                <div class="flex items-center justify-between gap-3">
                  <dt class="text-xs font-bold uppercase tracking-[0.12em] text-muted-foreground">{{ metric.label }}</dt>
                  <component :is="metric.icon" class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                </div>
                <dd class="mt-2 text-2xl font-black tabular-nums">{{ metric.value }}</dd>
                <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
              </div>
            </dl>

            <Card>
              <CardHeader class="border-b p-5">
                <div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                  <div>
                    <CardTitle class="text-lg">Seating and invited guests</CardTitle>
                    <CardDescription class="mt-1">Choose a table to focus the guest list without losing the full seating picture.</CardDescription>
                  </div>
                  <Button type="button" :disabled="saving" @click="openGuestDialog">
                    <UserPlus class="h-4 w-4" aria-hidden="true" />
                    Add guest
                  </Button>
                </div>
              </CardHeader>

              <CardContent class="p-0">
                <div class="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-4">
                  <Button
                    type="button"
                    variant="outline"
                    class="group h-auto min-h-28 items-start justify-start gap-3 whitespace-normal rounded-xl bg-background p-4 text-left transition-[border-color,box-shadow,transform] hover:-translate-y-0.5 hover:border-primary/45 hover:bg-background hover:shadow-sm"
                    :class="selectedTableId === 'all' ? 'border-primary bg-primary/[0.035] ring-1 ring-primary/20' : ''"
                    @click="selectGuestTable('all')"
                  >
                    <span class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
                      <Users class="h-5 w-5" aria-hidden="true" />
                    </span>
                    <span class="min-w-0 flex-1">
                      <span class="block font-bold">All invited</span>
                      <span class="mt-1 block text-xs text-muted-foreground">{{ guestSummary.total }} guest records</span>
                    </span>
                    <ChevronRight class="mt-2 h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                  </Button>

                  <Button
                    v-for="table in eventTables"
                    :key="table.public_id"
                    type="button"
                    variant="outline"
                    class="group h-auto min-h-28 items-start justify-start gap-3 whitespace-normal rounded-xl bg-background p-4 text-left transition-[border-color,box-shadow,transform] hover:-translate-y-0.5 hover:border-primary/45 hover:bg-background hover:shadow-sm"
                    :class="selectedTableId === table.public_id ? 'border-primary bg-primary/[0.035] ring-1 ring-primary/20' : ''"
                    @click="selectGuestTable(table.public_id)"
                  >
                    <span class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-emerald-50 text-emerald-800">
                      <Armchair class="h-5 w-5" aria-hidden="true" />
                    </span>
                    <span class="min-w-0 flex-1">
                      <span class="block truncate font-bold">{{ table.name }}</span>
                      <span class="mt-1 block text-xs text-muted-foreground">
                        {{ assignedSeats(table.public_id) }} / {{ table.capacity }} seats assigned
                      </span>
                      <span class="mt-2 block line-clamp-2 text-xs leading-5 text-muted-foreground">
                        {{ guestNamesAt(table.public_id) || 'No guests assigned' }}
                      </span>
                    </span>
                    <ChevronRight class="mt-2 h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                  </Button>
                </div>

                <div class="mx-5 overflow-x-auto rounded-xl border">
                  <Table class="min-w-[72rem]">
                    <TableHeader>
                      <TableRow>
                        <TableHead class="w-[18rem]">Guest</TableHead>
                        <TableHead>Response</TableHead>
                        <TableHead>Party</TableHead>
                        <TableHead>Table</TableHead>
                        <TableHead>Invitation</TableHead>
                        <TableHead class="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow v-if="guestLoading">
                        <TableCell colspan="6" class="h-32 text-center text-muted-foreground">
                          <span class="inline-flex items-center gap-2">
                            <Loader2 class="h-4 w-4 animate-spin" aria-hidden="true" />
                            Loading guests…
                          </span>
                        </TableCell>
                      </TableRow>
                      <template v-else>
                        <TableRow
                          v-for="guest in guests"
                          :key="guest.public_id"
                          class="transition-colors hover:bg-muted/30"
                        >
                          <TableCell class="py-4">
                            <div class="flex items-center gap-3">
                              <Avatar class="h-10 w-10 border" :class="guestAvatarClass(guest.full_name)">
                                <AvatarFallback class="font-bold">{{ guestInitials(guest.full_name) }}</AvatarFallback>
                              </Avatar>
                              <div class="min-w-0">
                                <p class="truncate font-semibold">{{ guest.full_name }}</p>
                                <p class="mt-0.5 truncate text-xs text-muted-foreground">{{ guest.email || guest.phone }}</p>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell class="py-4">
                            <Select :model-value="guest.response" @update:model-value="value => updateGuest(guest, { response: value })">
                              <SelectTrigger class="h-9 w-36"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="pending">Awaiting reply</SelectItem>
                                <SelectItem value="accepted">Attending</SelectItem>
                                <SelectItem value="maybe">Maybe</SelectItem>
                                <SelectItem value="declined">Not attending</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell class="py-4 font-semibold tabular-nums">{{ guest.party_size }}</TableCell>
                          <TableCell class="py-4">
                            <Select :model-value="guest.table_public_id || 'unassigned'" @update:model-value="value => updateGuest(guest, { table_public_id: value === 'unassigned' ? null : value })">
                              <SelectTrigger class="h-9 w-40"><SelectValue placeholder="Unassigned" /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="unassigned">Unassigned</SelectItem>
                                <SelectItem v-for="table in eventTables" :key="table.public_id" :value="table.public_id">
                                  {{ table.name }}
                                </SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell class="py-4">
                            <div class="flex items-center gap-2">
                              <span class="h-2 w-2 rounded-full" :class="guest.invite_sent_at ? 'bg-emerald-500' : 'bg-slate-300'" aria-hidden="true" />
                              <span>
                                <span class="block text-sm font-medium">{{ guest.invite_sent_at ? 'Email queued' : 'Not emailed' }}</span>
                                <span v-if="guest.invite_sent_at" class="mt-0.5 block text-xs text-muted-foreground">{{ formatEventDateTime(guest.invite_sent_at) }}</span>
                              </span>
                            </div>
                          </TableCell>
                          <TableCell class="py-4">
                            <div class="flex justify-end gap-2">
                              <Button variant="outline" size="sm" type="button" :disabled="saving" @click="copyGuestInviteLink(guest)">
                                <Copy class="h-4 w-4" aria-hidden="true" />
                                Copy link
                              </Button>
                              <Button size="sm" type="button" :disabled="saving || !guest.email" @click="sendGuestInviteEmail(guest)">
                                <Mail class="h-4 w-4" aria-hidden="true" />
                                Send email
                              </Button>
                              <Button
                                v-if="guest.guest_message"
                                variant="outline"
                                size="icon"
                                type="button"
                                :disabled="saving"
                                :aria-label="guest.wish_approved ? `Hide ${guest.full_name}'s wish` : `Approve ${guest.full_name}'s wish`"
                                @click="updateGuest(guest, { wish_approved: !guest.wish_approved })"
                              >
                                <EyeOff v-if="guest.wish_approved" class="h-4 w-4" aria-hidden="true" />
                                <Eye v-else class="h-4 w-4" aria-hidden="true" />
                              </Button>
                              <Button variant="outline" size="icon" type="button" :disabled="saving" :aria-label="`Remove ${guest.full_name}`" @click="removeGuest(guest)">
                                <Trash2 class="h-4 w-4 text-destructive" aria-hidden="true" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      </template>
                      <TableRow v-if="!guestLoading && !guests.length">
                        <TableCell colspan="6" class="h-32 text-center text-muted-foreground">
                          {{ selectedTableId === 'all' ? 'No guests have been invited yet.' : 'No guests are assigned to this table.' }}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>

                <RecordPagination
                  class="mt-5"
                  :page="guestPage"
                  :count="guestCount"
                  :size="guestPageSize"
                  :busy="guestLoading || saving"
                  @page="changeGuestPage"
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rsvp">
            <EventRsvpCustomizationTab
              :business-id="businessId"
              :event-id="selectedEvent.public_id"
              @updated="handleWebsiteUpdated"
            />
          </TabsContent>

          <TabsContent value="products">
            <EventProductsTab
              :business-id="businessId"
              :event="selectedEvent"
              :products="products"
              @updated="handleEventUpdated"
            />
          </TabsContent>

          <TabsContent value="venue">
            <EventVenueLayoutTab
              :business-id="businessId"
              :event="selectedEvent"
              :layouts="layouts"
              :resources="resources"
              :resource-types="resourceTypes"
              :locations="locations"
              @updated="handleEventUpdated"
            />
          </TabsContent>

          <TabsContent value="website">
            <EventWebsiteEditor
              :business-id="businessId"
              :event-id="selectedEvent.public_id"
              @updated="handleWebsiteUpdated"
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>

    <Dialog v-model:open="eventDialogOpen">
      <DialogContent class="flex max-h-[calc(100dvh-2rem)] flex-col gap-0 overflow-hidden p-0 sm:max-w-2xl">
        <DialogHeader class="shrink-0 border-b px-6 py-5 pr-14">
          <DialogTitle class="flex items-center gap-2">
            <CalendarHeart class="h-5 w-5 text-primary" aria-hidden="true" />
            Create guest event
          </DialogTitle>
          <DialogDescription>This creates an RSVP event, not a restaurant reservation or service appointment.</DialogDescription>
        </DialogHeader>
        <div class="grid min-h-0 flex-1 gap-4 overflow-y-auto px-6 py-5 sm:grid-cols-2">
          <div class="grid gap-2 sm:col-span-2">
            <Label for="event-title">Event name</Label>
            <Input id="event-title" v-model="eventForm.title" placeholder="Jordan and Riley's wedding" />
          </div>
          <div class="grid gap-2 sm:col-span-2">
            <Label for="event-thumbnail">Event thumbnail</Label>
            <Input
              id="event-thumbnail"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              @change="selectThumbnail"
            />
            <p class="text-xs text-muted-foreground">Optional JPG, PNG, or WebP up to 5 MB. The business cover is used as a fallback.</p>
          </div>
          <div class="grid gap-2">
            <Label>Event type</Label>
            <Select v-model="eventForm.event_type">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="wedding">Wedding</SelectItem>
                <SelectItem value="birthday">Birthday</SelectItem>
                <SelectItem value="general">General event</SelectItem>
                <SelectItem value="private_event">Private event</SelectItem>
                <SelectItem value="corporate">Corporate event</SelectItem>
                <SelectItem value="community">Community event</SelectItem>
                <SelectItem value="other">Other event</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label>RSVP status</Label>
            <Select v-model="eventForm.status">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="planning">Planning</SelectItem>
                <SelectItem value="open">Open for RSVP</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2 sm:col-span-2">
            <Label for="event-max-guests">Maximum attendance</Label>
            <Input
              id="event-max-guests"
              v-model.number="eventForm.max_guests"
              class="sm:max-w-48"
              type="number"
              min="1"
              max="10000"
            />
            <p class="text-xs text-muted-foreground">Accepted RSVP party sizes cannot exceed this capacity.</p>
          </div>
          <div class="grid gap-2">
            <Label for="event-start">Starts</Label>
            <Input id="event-start" v-model="eventForm.starts_at" type="datetime-local" />
          </div>
          <div class="grid gap-2">
            <Label for="event-end">Ends</Label>
            <Input id="event-end" v-model="eventForm.ends_at" type="datetime-local" />
          </div>
          <div class="grid gap-2">
            <Label>Location</Label>
            <Select v-model="eventForm.location_public_id">
              <SelectTrigger><SelectValue placeholder="Choose a location" /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="location in locations" :key="location.public_id" :value="location.public_id">
                  {{ location.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label>Floor plan</Label>
            <Select v-model="eventForm.layout_public_id">
              <SelectTrigger><SelectValue placeholder="Choose a venue layout" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No floor plan</SelectItem>
                <SelectItem v-for="layout in matchingLayouts" :key="layout.public_id" :value="layout.public_id">
                  {{ layout.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label for="organizer-name">Organizer name</Label>
            <Input id="organizer-name" v-model="eventForm.organizer_name" />
          </div>
          <div class="grid gap-2">
            <Label>Staff handler</Label>
            <Select v-model="eventForm.handler_public_id">
              <SelectTrigger><SelectValue placeholder="Choose an employee" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Assign after creation</SelectItem>
                <SelectItem v-for="member in availableHandlers" :key="member.public_id" :value="member.public_id">
                  {{ member.display_name }}{{ member.job_title ? ` · ${member.job_title}` : '' }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label for="organizer-email">Organizer email</Label>
            <Input id="organizer-email" v-model="eventForm.organizer_email" type="email" />
          </div>
          <div class="grid gap-2">
            <Label for="organizer-phone">Organizer phone</Label>
            <Input id="organizer-phone" v-model="eventForm.organizer_phone" type="tel" />
          </div>
          <div class="grid gap-2 sm:col-span-2">
            <Label for="event-description">Invitation note</Label>
            <Textarea id="event-description" v-model="eventForm.description" rows="3" placeholder="Share arrival details or a short welcome." />
          </div>
        </div>
        <DialogFooter class="shrink-0 border-t bg-background px-6 py-4">
          <Button variant="outline" type="button" @click="eventDialogOpen = false">Cancel</Button>
          <Button type="button" :disabled="!canCreateEvent || saving" @click="createEvent">
            <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
            Create event
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="guestDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle class="flex items-center gap-2">
            <UserPlus class="h-5 w-5 text-primary" aria-hidden="true" />
            Add invited guest
          </DialogTitle>
          <DialogDescription>Add one household or party. You can generate their private RSVP link after saving.</DialogDescription>
        </DialogHeader>
        <div class="grid gap-4 py-2">
          <div class="grid gap-2">
            <Label for="guest-name">Guest or household name</Label>
            <Input id="guest-name" v-model="guestForm.full_name" placeholder="Sam Rivera" />
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2">
              <Label for="guest-email">Email</Label>
              <Input id="guest-email" v-model="guestForm.email" type="email" />
            </div>
            <div class="grid gap-2">
              <Label for="guest-phone">Phone</Label>
              <Input id="guest-phone" v-model="guestForm.phone" />
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            <div class="grid gap-2">
              <Label for="guest-party">Invited party size</Label>
              <Input id="guest-party" v-model.number="guestForm.party_size" type="number" min="1" max="50" />
            </div>
            <div class="grid gap-2">
              <Label>Table</Label>
              <Select v-model="guestForm.table_public_id">
                <SelectTrigger><SelectValue placeholder="Unassigned" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Unassigned</SelectItem>
                  <SelectItem v-for="table in eventTables" :key="table.public_id" :value="table.public_id">
                    {{ table.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" type="button" @click="guestDialogOpen = false">Cancel</Button>
          <Button type="button" :disabled="!canCreateGuest || saving" @click="createGuest">
            <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
            Add guest
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="organizerLinkOpen">
      <DialogContent class="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle class="flex items-center gap-2">
            <ShieldCheck class="h-5 w-5 text-primary" aria-hidden="true" />
            Organizer access
          </DialogTitle>
          <DialogDescription>
            This private link lets the organizer manage invitees, RSVP responses, and table assignments.
          </DialogDescription>
        </DialogHeader>

        <div v-if="organizerLinkLoading" class="flex min-h-36 items-center justify-center text-muted-foreground">
          <Loader2 class="mr-2 h-5 w-5 animate-spin" aria-hidden="true" />
          Checking current access…
        </div>

        <div v-else-if="organizerUrl" class="space-y-4 py-2">
          <div class="rounded-xl border bg-muted/30 p-4">
            <div class="flex items-start gap-3">
              <div class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                <Link2 class="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <p class="font-bold">Current organizer link</p>
                <p class="mt-1 text-sm leading-5 text-muted-foreground">Opening this dialog does not replace or invalidate the link.</p>
              </div>
            </div>
            <Input class="mt-4 font-mono text-xs" :model-value="organizerUrl" readonly aria-label="Current organizer link" />
          </div>
          <div class="grid gap-2 sm:grid-cols-2">
            <Button variant="outline" type="button" @click="copyOrganizerLink">
              <Copy class="h-4 w-4" aria-hidden="true" />
              Copy link
            </Button>
            <ButtonAnchor :href="organizerUrl" target="_blank" rel="noopener">
              <ExternalLink class="h-4 w-4" aria-hidden="true" />
              Go to link
            </ButtonAnchor>
          </div>
          <div class="flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
            <p class="text-xs leading-5 text-muted-foreground">Replacing the link immediately revokes the current organizer URL.</p>
            <Button variant="ghost" size="sm" type="button" :disabled="saving" @click="generateOrganizerLink(true)">
              <RefreshCw class="h-4 w-4" aria-hidden="true" />
              Replace link
            </Button>
          </div>
        </div>

        <div v-else class="rounded-xl border border-dashed bg-muted/20 px-5 py-8 text-center">
          <div class="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-primary/10 text-primary">
            <ShieldCheck class="h-6 w-6" aria-hidden="true" />
          </div>
          <p class="mt-4 font-bold">{{ organizerLinkState.has_link ? 'The previous link cannot be displayed' : 'No organizer link yet' }}</p>
          <p class="mx-auto mt-2 max-w-sm text-sm leading-6 text-muted-foreground">
            {{ organizerLinkState.has_link
              ? 'It was created before reusable secure-link storage was available. Generate a replacement once.'
              : 'Generate a private organizer link when the event owner is ready to manage guests.' }}
          </p>
          <Button class="mt-5" type="button" :disabled="saving" @click="generateOrganizerLink(organizerLinkState.has_link)">
            <Link2 class="h-4 w-4" aria-hidden="true" />
            {{ organizerLinkState.has_link ? 'Generate replacement' : 'Generate organizer link' }}
          </Button>
        </div>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="capacityDialogOpen">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle class="flex items-center gap-2">
            <Users class="h-5 w-5 text-primary" aria-hidden="true" />
            Event capacity
          </DialogTitle>
          <DialogDescription>Set the maximum number of people who can confirm attendance.</DialogDescription>
        </DialogHeader>
        <div class="grid gap-2 py-2">
          <Label for="capacity-limit">Maximum attendance</Label>
          <Input id="capacity-limit" v-model.number="capacityValue" type="number" min="1" max="10000" />
          <p class="text-xs text-muted-foreground">Currently {{ selectedEvent?.guest_counts?.attending_people || 0 }} people are confirmed.</p>
        </div>
        <DialogFooter>
          <Button variant="outline" type="button" @click="capacityDialogOpen = false">Cancel</Button>
          <Button type="button" :disabled="saving || capacityValue < 1" @click="saveCapacity">Save capacity</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import {
  ArrowLeft,
  ArrowRight,
  Armchair,
  CalendarDays,
  CalendarHeart,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Copy,
  ExternalLink,
  Eye,
  EyeOff,
  FilePenLine,
  Grid3X3,
  LayoutGrid,
  List,
  Link2,
  Loader2,
  Mail,
  MailCheck,
  MapPin,
  PackageOpen,
  PartyPopper,
  PanelsTopLeft,
  PencilRuler,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  UserPlus,
  UserRoundCog,
  Users,
} from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ButtonAnchor } from '@/components/ui/button-anchor'
import { ButtonLink } from '@/components/ui/button-link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import EventStaffTab from '@/components/scheduling/EventOverviewTab.vue'
import EventDetailsTab from '@/components/scheduling/EventDetailsTab.vue'
import EventProductsTab from '@/components/scheduling/EventProductsTab.vue'
import EventRsvpCustomizationTab from '@/components/scheduling/EventRsvpCustomizationTab.vue'
import EventVenueLayoutTab from '@/components/scheduling/EventVenueLayoutTab.vue'
import EventWebsiteEditor from '@/components/scheduling/EventWebsiteEditor.vue'
import RecordPagination from '@/components/workspace/RecordPagination.vue'

const props = defineProps({
  businessId: { type: String, required: true },
  mode: { type: String, default: 'index' },
  eventId: { type: String, default: '' },
  locations: { type: Array, default: () => [] },
  layouts: { type: Array, default: () => [] },
  resources: { type: Array, default: () => [] },
  resourceTypes: { type: Array, default: () => [] },
  staff: { type: Array, default: () => [] },
  products: { type: Array, default: () => [] },
})

const { apiFetch } = useApiClient()
const route = useRoute()
const router = useRouter()
const eventTabs = ['details', 'website', 'guests', 'rsvp', 'staff', 'products', 'venue']
const activeTab = computed({
  get: () => normalizeEventTab(route.query.tab),
  set: value => {
    if (!eventTabs.includes(value)) return
    const current = Array.isArray(route.query.tab) ? route.query.tab[0] : route.query.tab
    if (current === value) return
    void router.replace({
      query: {
        ...route.query,
        tab: value,
      },
    })
  },
})
const events = ref([])
const eventCount = ref(0)
const page = ref(1)
const pageSize = 20
const viewMode = ref('grid')
const search = ref('')
const statusFilter = ref('all')
const typeFilter = ref('all')
const guests = ref([])
const guestCount = ref(0)
const guestPage = ref(1)
const guestPageSize = 20
const guestLoading = ref(false)
const guestSummary = ref({ total: 0, unassigned: 0, tables: [] })
const selectedEventId = ref('')
const selectedTableId = ref('all')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const eventDialogOpen = ref(false)
const guestDialogOpen = ref(false)
const organizerLinkOpen = ref(false)
const organizerLinkLoading = ref(false)
const capacityDialogOpen = ref(false)
const capacityValue = ref(100)
const organizerLinkState = reactive({
  has_link: false,
  recoverable: false,
  token: '',
})

const eventForm = reactive({
  title: '',
  event_type: 'wedding',
  status: 'open',
  starts_at: '',
  ends_at: '',
  location_public_id: '',
  layout_public_id: 'none',
  organizer_name: '',
  handler_public_id: 'none',
  organizer_email: '',
  organizer_phone: '',
  description: '',
  max_guests: 100,
  public_rsvp_enabled: true,
  thumbnail: null,
})

const guestForm = reactive({
  full_name: '',
  email: '',
  phone: '',
  party_size: 1,
  table_public_id: 'unassigned',
})

const selectedEvent = computed(() => events.value.find(event => event.public_id === selectedEventId.value) || null)
const availableHandlers = computed(() => props.staff.filter(member => member.is_active && member.employment_status === 'active'))
const organizerUrl = computed(() => (
  organizerLinkState.token && selectedEventId.value
    ? `${window.location.origin}/event/${selectedEventId.value}/manage/${organizerLinkState.token}`
    : ''
))
const hasActiveFilters = computed(() => Boolean(
  search.value || statusFilter.value !== 'all' || typeFilter.value !== 'all',
))
const matchingLayouts = computed(() => props.layouts.filter(layout => !eventForm.location_public_id || layout.location_public_id === eventForm.location_public_id))
const eventTables = computed(() => props.resources.filter(resource => (
  resource.layout_public_id === selectedEvent.value?.layout_public_id
    && resource.is_active
    && ['table', 'booth'].includes(resource.element_type)
)))
const metrics = computed(() => {
  const counts = selectedEvent.value?.guest_counts || {}
  return [
    { label: 'Invited', value: counts.total || guestSummary.value.total, detail: 'Households and parties', icon: Users },
    { label: 'Attending', value: counts.attending_people || 0, detail: `${counts.capacity_remaining ?? selectedEvent.value?.max_guests ?? 0} places remaining`, icon: CheckCircle2 },
    { label: 'Awaiting', value: counts.pending || 0, detail: 'Still need a response', icon: Clock3 },
    { label: 'Tables', value: eventTables.value.length, detail: `${unassignedCount.value} unassigned guests`, icon: Armchair },
  ]
})
const unassignedCount = computed(() => guestSummary.value.unassigned || 0)
const canCreateEvent = computed(() => Boolean(
  eventForm.title.trim()
    && eventForm.organizer_name.trim()
    && eventForm.starts_at
    && eventForm.location_public_id
    && Number(eventForm.max_guests) > 0,
))
const canCreateGuest = computed(() => Boolean(
  guestForm.full_name.trim()
    && (guestForm.email.trim() || guestForm.phone.trim())
    && Number(guestForm.party_size) > 0,
))

onMounted(loadEvents)
watch(() => props.businessId, loadEvents)
watch(() => props.eventId, loadEvents)
watch(() => eventForm.location_public_id, () => {
  if (eventForm.layout_public_id !== 'none' && !matchingLayouts.value.some(layout => layout.public_id === eventForm.layout_public_id)) {
    eventForm.layout_public_id = 'none'
  }
})

async function loadEvents() {
  if (!props.businessId) return
  loading.value = true
  error.value = ''
  try {
    if (props.mode === 'detail') {
      const event = await apiFetch(`businesses/${props.businessId}/venue-events/${props.eventId}/`)
      events.value = [event]
      eventCount.value = 1
      selectedEventId.value = event.public_id
      guestPage.value = 1
      selectedTableId.value = 'all'
      await loadGuests()
      return
    }

    const query = new URLSearchParams({ page: String(page.value) })
    if (search.value) query.set('search', search.value)
    if (statusFilter.value !== 'all') query.set('status', statusFilter.value)
    if (typeFilter.value !== 'all') query.set('event_type', typeFilter.value)
    const response = await apiFetch(`businesses/${props.businessId}/venue-events/?${query.toString()}`)
    events.value = normalizeList(response)
    eventCount.value = Number(response?.count ?? events.value.length)
    selectedEventId.value = ''
    guests.value = []
    guestCount.value = 0
    guestSummary.value = { total: 0, unassigned: 0, tables: [] }
  } catch (requestError) {
    error.value = apiError(requestError, 'Could not load guest events.')
  } finally {
    loading.value = false
  }
}

async function applyFilters() {
  page.value = 1
  await loadEvents()
}

async function clearFilters() {
  search.value = ''
  statusFilter.value = 'all'
  typeFilter.value = 'all'
  page.value = 1
  await loadEvents()
}

async function changePage(nextPage) {
  page.value = nextPage
  await loadEvents()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function eventPath(event) {
  return `/workspace/schedule/events/${event.public_id}`
}

async function selectEvent(eventId) {
  selectedEventId.value = eventId
  selectedTableId.value = 'all'
  guestPage.value = 1
  await loadGuests()
}

async function loadGuests() {
  if (!selectedEventId.value) {
    guests.value = []
    guestCount.value = 0
    guestSummary.value = { total: 0, unassigned: 0, tables: [] }
    return
  }
  guestLoading.value = true
  try {
    const query = new URLSearchParams({
      page: String(guestPage.value),
      page_size: String(guestPageSize),
      table: selectedTableId.value,
    })
    const response = await apiFetch(
      `businesses/${props.businessId}/venue-events/${selectedEventId.value}/guests/?${query.toString()}`,
    )
    guests.value = normalizeList(response)
    guestCount.value = Number(response?.count ?? guests.value.length)
    guestSummary.value = response?.summary || {
      total: guests.value.length,
      unassigned: guests.value.filter(guest => !guest.table_public_id).length,
      tables: [],
    }
  } finally {
    guestLoading.value = false
  }
}

async function selectGuestTable(tableId) {
  if (selectedTableId.value === tableId && guestPage.value === 1) return
  selectedTableId.value = tableId
  guestPage.value = 1
  await loadGuests()
}

async function changeGuestPage(nextPage) {
  guestPage.value = nextPage
  await loadGuests()
}

async function refreshSelectedEvent() {
  if (!selectedEventId.value || !selectedEvent.value) return
  const refreshed = await apiFetch(
    `businesses/${props.businessId}/venue-events/${selectedEventId.value}/`,
  )
  Object.assign(selectedEvent.value, refreshed)
}

async function refreshGuestWorkspace() {
  await Promise.all([loadGuests(), refreshSelectedEvent()])
  if (!guests.value.length && guestPage.value > 1) {
    guestPage.value -= 1
    await loadGuests()
  }
}

function openEventDialog() {
  const start = new Date()
  start.setDate(start.getDate() + 14)
  start.setHours(16, 0, 0, 0)
  const end = new Date(start.getTime() + 5 * 60 * 60 * 1000)
  Object.assign(eventForm, {
    title: '',
    event_type: 'wedding',
    status: 'open',
    starts_at: localDateTime(start),
    ends_at: localDateTime(end),
    location_public_id: props.locations[0]?.public_id || '',
    layout_public_id: 'none',
    organizer_name: '',
    handler_public_id: 'none',
    organizer_email: '',
    organizer_phone: '',
    description: '',
    max_guests: 100,
    public_rsvp_enabled: true,
    thumbnail: null,
  })
  eventDialogOpen.value = true
}

function selectThumbnail(event) {
  eventForm.thumbnail = event.target.files?.[0] || null
}

async function createEvent() {
  saving.value = true
  try {
    const payload = {
      ...eventForm,
      max_guests: Number(eventForm.max_guests),
      starts_at: new Date(eventForm.starts_at).toISOString(),
      ends_at: eventForm.ends_at ? new Date(eventForm.ends_at).toISOString() : null,
      layout_public_id: eventForm.layout_public_id === 'none' ? null : eventForm.layout_public_id,
      handler_public_id: eventForm.handler_public_id === 'none' ? null : eventForm.handler_public_id,
    }
    delete payload.thumbnail

    let body = payload
    if (eventForm.thumbnail) {
      body = new FormData()
      for (const [key, value] of Object.entries(payload)) {
        if (value !== null && value !== undefined) body.append(key, String(value))
      }
      body.append('thumbnail', eventForm.thumbnail)
    }

    const created = await apiFetch(`businesses/${props.businessId}/venue-events/`, {
      method: 'POST',
      body,
    })
    eventDialogOpen.value = false
    toast({ title: 'Event created', description: `${created.title} now has its own RSVP workspace.` })
    await router.push(eventPath(created))
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

function openGuestDialog() {
  Object.assign(guestForm, {
    full_name: '',
    email: '',
    phone: '',
    party_size: 1,
    table_public_id: selectedTableId.value === 'all' ? 'unassigned' : selectedTableId.value,
  })
  guestDialogOpen.value = true
}

async function createGuest() {
  saving.value = true
  try {
    await apiFetch(`businesses/${props.businessId}/venue-events/${selectedEventId.value}/guests/`, {
      method: 'POST',
      body: {
        ...guestForm,
        party_size: Number(guestForm.party_size),
        table_public_id: guestForm.table_public_id === 'unassigned' ? null : guestForm.table_public_id,
      },
    })
    guestDialogOpen.value = false
    guestPage.value = 1
    await refreshGuestWorkspace()
    toast({ title: 'Guest added', description: 'Generate their private RSVP link when you are ready to send it.' })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function updateGuest(guest, changes) {
  saving.value = true
  const previous = { ...guest }
  Object.assign(guest, changes)
  try {
    const saved = await apiFetch(`businesses/${props.businessId}/venue-events/${selectedEventId.value}/guests/${guest.public_id}/`, {
      method: 'PATCH',
      body: changes,
    })
    Object.assign(guest, saved)
    await refreshGuestWorkspace()
    toast({ title: 'Guest updated' })
  } catch (requestError) {
    Object.assign(guest, previous)
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function removeGuest(guest) {
  saving.value = true
  try {
    await apiFetch(`businesses/${props.businessId}/venue-events/${selectedEventId.value}/guests/${guest.public_id}/`, { method: 'DELETE' })
    await refreshGuestWorkspace()
    toast({ title: 'Guest removed', description: `${guest.full_name} is no longer on this event list.` })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function openOrganizerLinkDialog() {
  organizerLinkOpen.value = true
  organizerLinkLoading.value = true
  try {
    const response = await apiFetch(`businesses/${props.businessId}/venue-events/${selectedEventId.value}/organizer-link/`)
    Object.assign(organizerLinkState, {
      has_link: Boolean(response.has_link),
      recoverable: Boolean(response.recoverable),
      token: response.token || '',
    })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    organizerLinkLoading.value = false
  }
}

async function generateOrganizerLink(regenerate = false) {
  saving.value = true
  try {
    const response = await apiFetch(`businesses/${props.businessId}/venue-events/${selectedEventId.value}/organizer-link/`, {
      method: 'POST',
      body: { regenerate },
    })
    Object.assign(organizerLinkState, {
      has_link: true,
      recoverable: true,
      token: response.token,
    })
    toast({
      title: regenerate ? 'Organizer link replaced' : 'Organizer link generated',
      description: regenerate
        ? 'The previous organizer link no longer works.'
        : 'The private organizer link is ready to share.',
    })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function copyOrganizerLink() {
  try {
    await navigator.clipboard.writeText(organizerUrl.value)
    toast({ title: 'Organizer link copied', description: 'Only share it with someone allowed to manage the guest list.' })
  } catch (requestError) {
    failedToast(requestError)
  }
}

async function copyGuestInviteLink(guest) {
  saving.value = true
  try {
    const response = await apiFetch(`businesses/${props.businessId}/venue-events/${selectedEventId.value}/guests/${guest.public_id}/invite-link/`, {
      method: 'POST',
      body: { regenerate: false, send_email: false },
    })
    const link = `${window.location.origin}/event/${selectedEventId.value}/rsvp/${response.token}`
    await navigator.clipboard.writeText(link)
    toast({ title: 'Private RSVP link copied', description: `The link only opens ${guest.full_name}'s invitation.` })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

async function sendGuestInviteEmail(guest) {
  saving.value = true
  try {
    const response = await apiFetch(`businesses/${props.businessId}/venue-events/${selectedEventId.value}/guests/${guest.public_id}/invite-link/`, {
      method: 'POST',
      body: { regenerate: false, send_email: true },
    })
    guest.invite_sent_at = response.invite_sent_at
    toast({ title: 'Invitation queued', description: `PixelCore is sending the private RSVP link to ${guest.email}.` })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

function openCapacityDialog() {
  capacityValue.value = Number(selectedEvent.value?.max_guests || 100)
  capacityDialogOpen.value = true
}

function handleWebsiteUpdated(website) {
  if (!selectedEvent.value) return
  selectedEvent.value.title = website.title
  selectedEvent.value.website_enabled = website.website_enabled
  selectedEvent.value.website_published_at = website.website_published_at
}

function handleEventUpdated(updated) {
  if (!selectedEvent.value) return
  Object.assign(selectedEvent.value, updated)
}

async function saveCapacity() {
  saving.value = true
  try {
    const saved = await apiFetch(`businesses/${props.businessId}/venue-events/${selectedEventId.value}/`, {
      method: 'PATCH',
      body: { max_guests: Number(capacityValue.value) },
    })
    Object.assign(selectedEvent.value, saved)
    capacityDialogOpen.value = false
    toast({ title: 'Capacity updated', description: `This event can accept up to ${saved.max_guests} people.` })
  } catch (requestError) {
    failedToast(requestError)
  } finally {
    saving.value = false
  }
}

function capacityPercent(event) {
  const maximum = Math.max(1, Number(event.max_guests || 1))
  return Math.min(100, Math.round((Number(event.guest_counts?.attending_people || 0) / maximum) * 100))
}

function assignedSeats(tableId) {
  return guestSummary.value.tables.find(table => table.public_id === tableId)?.assigned_seats || 0
}

function guestNamesAt(tableId) {
  const summary = guestSummary.value.tables.find(table => table.public_id === tableId)
  if (!summary) return ''
  const visibleNames = summary.guest_names.join(', ')
  const remaining = Math.max(0, summary.guest_count - summary.guest_names.length)
  return remaining ? `${visibleNames} +${remaining} more` : visibleNames
}

function guestInitials(name) {
  return String(name || '?')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0])
    .join('')
    .toUpperCase()
}

function guestAvatarClass(name) {
  const palette = [
    'bg-rose-50 text-rose-800',
    'bg-emerald-50 text-emerald-800',
    'bg-blue-50 text-blue-800',
    'bg-violet-50 text-violet-800',
    'bg-amber-50 text-amber-800',
  ]
  const index = [...String(name || '')].reduce((total, character) => total + character.charCodeAt(0), 0)
  return palette[index % palette.length]
}

function eventTypeLabel(type) {
  return {
    wedding: 'Wedding',
    birthday: 'Birthday',
    general: 'General event',
    private_event: 'Private event',
    corporate: 'Corporate event',
    community: 'Community event',
    other: 'Event',
  }[type] || 'Event'
}

function statusLabel(status) {
  return {
    planning: 'Planning',
    open: 'RSVP open',
    closed: 'RSVP closed',
    completed: 'Completed',
    cancelled: 'Cancelled',
  }[status] || status
}

function formatEventDate(value) {
  return new Intl.DateTimeFormat('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value))
}

function formatEventDateTime(value) {
  return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function localDateTime(date) {
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60 * 1000).toISOString().slice(0, 16)
}

function normalizeList(response) {
  return Array.isArray(response) ? response : response?.results || []
}

function normalizeEventTab(value) {
  const candidate = Array.isArray(value) ? value[0] : String(value || '')
  return eventTabs.includes(candidate) ? candidate : 'details'
}

function apiError(requestError, fallback) {
  return requestError?.data?.error?.message
    || requestError?.data?.detail
    || requestError?.message
    || fallback
}

function failedToast(requestError) {
  toast({
    title: 'Could not save changes',
    description: apiError(requestError, 'Please review the details and try again.'),
    variant: 'destructive',
  })
}
</script>
