<template>
  <div
    ref="pageRef"
    class="wedding-invitation min-h-screen overflow-x-hidden"
    :class="selectedTemplate.className"
    :style="pageStyle"
  >
    <Transition name="preloader">
      <div v-if="showPreloader" class="fixed inset-0 z-[100] grid place-items-center bg-black" aria-live="polite">
        <div class="preloader-frame relative h-[58vh] w-[min(66vw,22rem)] overflow-hidden bg-[#111]" :class="loadingProgress === 100 ? 'is-complete' : ''">
          <img
            v-if="heroImage"
            :src="heroImage.image_url"
            :alt="heroImage.alt_text"
            class="h-full w-full object-cover grayscale transition-transform duration-700"
            :style="{ transform: `scale(${1.12 - loadingProgress / 850})` }"
            @load="finishPreloader"
            @error="finishPreloader"
          >
          <div v-else class="grid h-full place-items-center border border-white/10">
            <Camera class="h-8 w-8 text-white/40" aria-hidden="true" />
          </div>
          <p class="absolute inset-0 grid place-items-center text-5xl text-white mix-blend-difference wedding-display">
            {{ loadingProgress }}%
          </p>
        </div>
      </div>
    </Transition>

    <Dialog v-model:open="welcomeOpen">
      <DialogContent
        class="event-welcome max-w-xl overflow-hidden border-white/15 p-0 sm:rounded-none"
        :style="{ ...pageStyle, backgroundColor: 'var(--event-bg)', color: 'var(--event-text)' }"
      >
        <div v-if="popupImage" class="aspect-[16/7] overflow-hidden bg-black">
          <img :src="popupImage.image_url" :alt="popupImage.alt_text" class="h-full w-full object-cover" />
        </div>
        <div class="p-7 sm:p-9">
          <DialogHeader class="text-left">
            <DialogTitle class="text-balance text-4xl leading-none wedding-display sm:text-5xl">{{ popupTitle }}</DialogTitle>
            <DialogDescription class="mt-4 max-w-lg text-sm leading-7 text-white/60">{{ popupMessage }}</DialogDescription>
          </DialogHeader>
          <p v-if="musicAvailable" class="mt-6 flex items-center gap-2 text-xs text-white/50">
            <Music2 class="h-4 w-4" aria-hidden="true" />
            {{ website.background_music_title || 'Background music' }} can play while you explore.
          </p>
          <Button type="button" class="mt-7 h-12 w-full bg-white text-black hover:bg-white/85" @click="beginExperience">
            <Volume2 v-if="musicAvailable" class="h-4 w-4" aria-hidden="true" />
            {{ website.popup_button_label || 'Enter event' }}
          </Button>
        </div>
      </DialogContent>
    </Dialog>

    <audio
      v-if="musicAvailable"
      ref="musicRef"
      :src="website.background_music_url"
      loop
      preload="metadata"
      @play="isMusicPlaying = true"
      @pause="isMusicPlaying = false"
      @ended="isMusicPlaying = false"
    />

    <nav class="fixed inset-x-0 top-0 z-50 border-b border-white/15 bg-black/60 px-4 text-white backdrop-blur-md" aria-label="Invitation sections">
      <div class="mx-auto grid h-20 max-w-7xl grid-cols-[1fr_auto_1fr] items-center gap-4">
        <div class="hidden items-center gap-1 md:flex">
          <a v-if="showSection('event_detail')" href="#details" class="nav-link">Schedule</a>
          <a v-if="showSection('story')" href="#story" class="nav-link">Story</a>
          <a v-if="showSection('gallery')" href="#gallery" class="nav-link">Gallery</a>
          <a v-if="showSection('wish')" href="#wish" class="nav-link">Wishes</a>
        </div>
        <a href="#hero" class="col-start-2 inline-flex max-w-[70vw] items-center justify-center text-center text-2xl leading-none text-white event-script sm:text-3xl" aria-label="Return to invitation opening">
          <img v-if="headerLogo" :src="headerLogo" :alt="event.business?.display_name || 'Event logo'" class="max-h-10 max-w-36 object-contain" />
          <span v-else class="truncate">{{ headerMark }}</span>
        </a>
        <p class="hidden justify-self-end text-xs tabular-nums text-white/65 md:block">{{ formatShortDate(event.starts_at) }}</p>
      </div>
    </nav>

    <main>
      <section id="hero" class="relative isolate min-h-svh overflow-hidden bg-black">
        <img
          v-if="heroImage"
          :src="heroImage.image_url"
          :alt="heroImage.alt_text"
          class="absolute inset-0 h-full w-full scale-[1.03] object-cover grayscale"
          :style="heroImageStyle"
        >
        <div v-else class="absolute inset-0 bg-[#090909]" />
        <div class="absolute inset-0 bg-black/45" />
        <div class="absolute inset-x-0 top-0 h-32 bg-black/20" />
        <GardenBotanicalDecoration v-if="isGardenVow" placement="frame" />
        <GardenBotanicalDecoration v-if="isGardenVow" placement="corner" />

        <div class="hero-content relative z-10 flex min-h-svh flex-col items-center justify-center px-5 pb-28 pt-24 text-center text-white">
          <p class="text-sm tracking-[0.16em] text-white/70">{{ publicCopy.salutation }}</p>
          <h1 class="mt-3 max-w-4xl text-balance text-6xl leading-[0.88] wedding-display sm:text-7xl lg:text-8xl">
            Our cherished guest
          </h1>
          <p class="mt-7 max-w-xl text-balance text-sm leading-6 text-white/75 sm:text-base">
            {{ website.invitation_text || event.description || 'You are invited to celebrate with us.' }}
          </p>
          <p class="mt-3 text-sm text-white/75">{{ formatLongDate(event.starts_at) }}</p>
          <div
            v-if="showCountdown"
            class="mt-8 w-full max-w-xl border-y border-white/25 py-5"
            role="timer"
            aria-live="off"
          >
            <p class="text-xs tracking-[0.12em] text-white/60">{{ website.countdown_label || 'Until we celebrate' }}</p>
            <p v-if="countdown.isComplete" class="mt-4 text-2xl wedding-display">{{ publicCopy.countdownComplete }}</p>
            <div v-else class="mt-4 grid grid-cols-4 divide-x divide-white/20">
              <div v-for="part in countdown.parts" :key="part.label" class="px-2 text-center">
                <span class="block text-3xl tabular-nums wedding-display sm:text-4xl">{{ part.value }}</span>
                <span class="mt-1 block text-[10px] uppercase tracking-[0.12em] text-white/50">{{ part.label }}</span>
              </div>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            class="mt-8 border-white/50 bg-transparent text-white hover:bg-white hover:text-black"
            @click="downloadCalendar"
          >
            <CalendarPlus class="h-4 w-4" aria-hidden="true" />
            Save the date
          </Button>
        </div>

        <p class="pointer-events-none absolute -bottom-[0.14em] left-1/2 z-10 w-[112%] -translate-x-1/2 whitespace-nowrap text-center text-[clamp(7rem,22vw,22rem)] leading-none text-white/20 wedding-display" aria-hidden="true">
          {{ heroDate }}
        </p>
      </section>

      <section v-if="showSection('event_detail')" id="details" class="min-h-svh bg-black px-5 py-28 text-white sm:px-8 sm:py-36">
        <div class="mx-auto max-w-7xl">
          <div class="grid gap-7 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
            <h2 data-reveal="copy" class="max-w-4xl text-balance text-5xl leading-[0.95] wedding-display sm:text-7xl lg:text-8xl">{{ publicCopy.detailHeading }}</h2>
            <p data-reveal="copy" class="max-w-md text-base leading-8 text-white/60 lg:justify-self-end">
              Follow the day in order. Each venue and time comes directly from the organizer's event plan.
            </p>
          </div>

          <div v-if="schedules.length" class="mt-20">
            <ol class="event-timeline relative mx-auto max-w-6xl" aria-label="Event schedule timeline">
              <li
                v-for="(entry, index) in schedules"
                :key="entry.public_id || entry.title"
                data-reveal="copy"
                class="relative grid min-h-52 grid-cols-[3rem_minmax(0,1fr)] items-center py-8 sm:min-h-64 sm:grid-cols-[minmax(0,1fr)_4rem_minmax(0,1fr)] sm:py-10"
                :style="revealDelay(index)"
              >
                <span
                  class="timeline-node absolute left-6 top-1/2 z-10 grid h-5 w-5 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border sm:left-1/2"
                  :class="activeScheduleIndex === index ? 'is-active border-white bg-white' : 'border-white/50 bg-black'"
                  aria-hidden="true"
                >
                  <span class="h-1.5 w-1.5 rounded-full bg-black" />
                </span>

                <Button
                  type="button"
                  variant="ghost"
                  class="group col-start-2 row-start-1 h-auto w-full flex-col items-start rounded-none px-4 py-4 text-left text-white hover:bg-transparent hover:text-white sm:px-8"
                  :class="[
                    index % 2 === 0
                      ? 'sm:col-start-3 sm:items-start sm:text-left'
                      : 'sm:col-start-1 sm:items-end sm:text-right',
                    activeScheduleIndex === index ? 'opacity-100' : 'opacity-55 hover:opacity-90',
                  ]"
                  :aria-current="activeScheduleIndex === index ? 'step' : undefined"
                  @click="activeScheduleIndex = index"
                >
                  <span class="text-4xl leading-none tabular-nums wedding-display sm:text-5xl">{{ formatTime(entry.starts_at) }}</span>
                  <span class="mt-3 text-2xl leading-tight wedding-display sm:text-4xl">{{ entry.title }}</span>
                  <span v-if="entry.venue_name" class="mt-4 flex items-start gap-2 text-sm leading-6 text-white/65">
                    <MapPin class="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                    <span>
                      {{ entry.venue_name }}
                      <span v-if="entry.address" class="block text-white/45">{{ entry.address }}</span>
                    </span>
                  </span>
                </Button>

                <span
                  class="pointer-events-none row-start-1 hidden items-center text-white/20 sm:flex"
                  :class="index % 2 === 0 ? 'col-start-1 justify-end pr-12' : 'col-start-3 justify-start pl-12'"
                  aria-hidden="true"
                >
                  <component :is="scheduleIcon(entry, index)" class="h-16 w-16 stroke-1 lg:h-20 lg:w-20" />
                </span>
              </li>
            </ol>

            <Transition name="schedule-shift" mode="out-in">
              <article v-if="activeSchedule" :key="activeSchedule.public_id || activeSchedule.title" class="schedule-focus relative mx-auto mt-12 min-h-[28rem] max-w-6xl overflow-hidden border-y border-white/20 bg-[#111]">
                <img
                  v-if="mapImageUrl"
                  :src="mapImageUrl"
                  :alt="`Map showing ${mapVenueName}`"
                  class="absolute inset-0 h-full w-full object-cover grayscale contrast-125 brightness-[0.32]"
                />
                <div class="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-black/20" />
                <div class="relative z-10 flex min-h-[28rem] flex-col justify-between p-7 sm:p-10 lg:p-12">
                  <div class="flex flex-wrap items-start justify-between gap-6">
                    <div>
                      <p class="text-sm tabular-nums text-white/55">{{ formatLongDate(activeSchedule.starts_at) }}</p>
                      <p class="mt-3 text-5xl leading-none tabular-nums wedding-display sm:text-7xl">{{ formatTimeRange(activeSchedule.starts_at, activeSchedule.ends_at, activeSchedule.end_time_label) }}</p>
                    </div>
                    <component :is="scheduleIcon(activeSchedule, activeScheduleIndex)" class="h-9 w-9 stroke-1 text-white/55" aria-hidden="true" />
                  </div>
                  <div class="max-w-2xl">
                    <h3 class="text-balance text-5xl leading-none wedding-display sm:text-7xl">{{ activeSchedule.title }}</h3>
                    <p class="mt-7 flex items-start gap-3 text-lg leading-7 text-white/80">
                      <MapPin class="mt-1 h-5 w-5 shrink-0" aria-hidden="true" />
                      <span>{{ activeSchedule.venue_name }}<span v-if="activeSchedule.address" class="mt-1 block text-sm leading-6 text-white/55">{{ activeSchedule.address }}</span></span>
                    </p>
                    <a v-if="mapDirectionsUrl" :href="mapDirectionsUrl" target="_blank" rel="noopener" class="mt-8 inline-flex items-center gap-2 border-b border-white/50 pb-1 text-sm text-white transition-colors hover:border-white">
                      Open directions
                      <ArrowUpRight class="h-4 w-4" aria-hidden="true" />
                    </a>
                  </div>
                </div>
              </article>
            </Transition>
          </div>

          <div v-else data-reveal="copy" class="mt-20 flex min-h-72 items-start gap-5 border-y border-white/15 py-12">
            <CalendarDays class="h-8 w-8 shrink-0 text-white/50" aria-hidden="true" />
            <div>
              <p class="text-3xl text-white wedding-display">The day is still taking shape.</p>
              <p class="mt-3 max-w-lg text-sm leading-6 text-white/55">Ceremony, reception, and venue details will appear here once the organizer publishes the schedule.</p>
            </div>
          </div>
        </div>
      </section>

      <section v-if="showSection('participants')" class="relative flex min-h-svh flex-col justify-center overflow-hidden bg-black px-5 py-24 text-white sm:px-8">
        <div class="mx-auto w-full max-w-7xl text-center">
          <p data-reveal="copy" class="text-sm tracking-[0.16em] text-white/50">{{ publicCopy.participantLabel }}</p>
          <h2 data-reveal="copy" class="mx-auto mt-8 max-w-6xl text-balance text-[clamp(4.5rem,13vw,11rem)] leading-[0.78] wedding-display">
            {{ participantHeading }}
          </h2>
          <div v-if="website.participants?.length" class="mt-24 grid gap-5 text-left sm:grid-cols-2">
            <article v-for="(person, index) in website.participants" :key="person.public_id || person.name" data-reveal="copy" :style="revealDelay(index)">
              <figure v-if="templateGroup === 'wedding'" class="aspect-[4/5] overflow-hidden bg-[#111]">
                <img v-if="person.image_url" :src="person.image_url" :alt="person.image_alt_text || `Portrait of ${person.name}`" class="h-full w-full object-cover grayscale transition duration-700 hover:grayscale-0" loading="lazy" decoding="async" />
                <div v-else class="grid h-full place-items-center border border-white/15 text-white/35">
                  <UserRound class="h-12 w-12 stroke-1" aria-hidden="true" />
                </div>
              </figure>
              <div class="border-t border-white/20 py-6" :class="templateGroup === 'wedding' ? 'mt-4' : ''">
                <p class="text-xs uppercase tracking-[0.16em] text-white/45">{{ person.subtitle || person.role || 'Celebrating' }}</p>
                <p class="mt-3 text-4xl leading-none wedding-display sm:text-5xl">{{ person.name }}</p>
                <p v-if="person.family_text" class="mt-4 max-w-md text-sm leading-6 text-white/55">{{ person.family_text }}</p>
              </div>
            </article>
          </div>
          <div v-else data-reveal="copy" class="mx-auto mt-16 max-w-xl border-y border-white/15 py-8 text-sm leading-7 text-white/55">
            Participant names and family acknowledgements will appear here when they are ready to share.
          </div>
        </div>
      </section>

      <section v-if="showSection('story')" id="story" class="relative overflow-hidden bg-black px-5 py-28 text-white sm:px-8 sm:py-40">
        <div class="mx-auto max-w-7xl">
          <h2 class="sr-only">Our story</h2>
          <div v-if="website.story_blocks?.length" class="space-y-28 sm:space-y-40">
            <article
              v-for="(block, index) in website.story_blocks"
              :key="block.public_id || index"
              class="grid min-h-[70vh] items-center gap-10 border-t border-white/15 pt-10 lg:grid-cols-2 lg:gap-20"
            >
              <figure
                v-if="storyImage(block)"
                class="aspect-[4/5] min-h-[28rem] overflow-hidden bg-[#111]"
                :class="index % 2 ? 'lg:order-2' : ''"
              >
                <img
                  :src="storyImage(block).image_url"
                  :alt="storyImage(block).alt_text"
                  class="h-full w-full object-cover grayscale transition duration-700 hover:grayscale-0"
                  loading="lazy"
                />
              </figure>
              <div class="flex min-h-[28rem] items-center" :class="storyImage(block) ? '' : 'lg:col-span-2 lg:justify-center'">
                <div data-reveal="copy" class="max-w-3xl" :class="storyImage(block) ? '' : 'text-center'">
                  <p v-if="block.date_label" class="mb-5 text-xs uppercase tracking-[0.16em] text-white/45">{{ block.date_label }}</p>
                  <h3 v-if="block.title" class="mb-6 text-5xl wedding-display sm:text-7xl">{{ block.title }}</h3>
                  <p class="text-balance text-3xl leading-[1.08] wedding-display sm:text-5xl lg:text-6xl">{{ block.body }}</p>
                </div>
              </div>
            </article>
          </div>
          <div v-else data-reveal="copy" class="mx-auto flex min-h-[60vh] max-w-5xl flex-col items-center justify-center text-center">
            <p class="text-balance text-5xl leading-[1.02] wedding-display sm:text-7xl">A story waiting for its first chapter.</p>
            <p class="mt-8 max-w-xl text-sm leading-7 text-white/50">The organizer can add milestones, photographs, and the moments that brought everyone to this day.</p>
          </div>
        </div>
      </section>

      <section v-if="showQuote" class="quote-panel bg-[#161616] px-5 py-28 text-white sm:px-8 sm:py-36">
        <figure data-reveal="copy" class="mx-auto max-w-5xl text-center">
          <blockquote class="text-balance text-4xl leading-tight wedding-display sm:text-6xl">{{ website.quote?.original_text || 'A meaningful line can hold the feeling of the day.' }}</blockquote>
          <p v-if="website.quote?.translation" class="mx-auto mt-10 max-w-3xl text-sm leading-7 text-white/60">{{ website.quote.translation }}</p>
          <figcaption v-if="website.quote?.citation" class="mt-6 text-xs uppercase tracking-[0.16em] text-white/40">{{ website.quote.citation }}</figcaption>
          <figcaption v-else-if="!website.quote?.original_text" class="mt-6 text-xs uppercase tracking-[0.16em] text-white/40">A quote can be added in the event editor</figcaption>
        </figure>
      </section>

      <section
        v-if="dressCodeConfig.enabled || eventNotesConfig.enabled"
        id="guest-details"
        class="invitation-guidance relative overflow-hidden bg-black px-5 py-28 text-white sm:px-8 sm:py-36"
      >
        <GardenBotanicalDecoration v-if="isGardenVow" placement="corner" />
        <div class="relative z-10 mx-auto max-w-7xl">
          <GardenBotanicalDecoration v-if="isGardenVow" placement="divider" />
          <div class="grid gap-14 lg:grid-cols-2 lg:gap-20">
            <article v-if="dressCodeConfig.enabled" data-reveal="copy" class="guidance-panel">
              <div>
                <h2 class="text-5xl leading-none wedding-display sm:text-7xl">{{ dressCodeConfig.heading }}</h2>
                <p v-if="dressCodeConfig.subtitle" class="mt-5 text-sm tracking-[0.12em] text-white/55">{{ dressCodeConfig.subtitle }}</p>
                <p v-if="dressCodeConfig.description" class="mt-7 max-w-xl text-base leading-8 text-white/70">{{ dressCodeConfig.description }}</p>
              </div>
              <div v-if="dressCodeConfig.colors.length" class="mt-9 flex flex-wrap gap-3" aria-label="Suggested dress-code colors">
                <span
                  v-for="color in dressCodeConfig.colors"
                  :key="color"
                  class="h-11 w-11 rounded-full border border-white/25 shadow-[0_8px_22px_rgba(0,0,0,0.22)]"
                  :style="{ backgroundColor: color }"
                  :title="color"
                />
              </div>
              <figure v-if="dressCodeConfig.media_url" class="mt-10 aspect-[4/3] overflow-hidden bg-white/5">
                <img :src="dressCodeConfig.media_url" :alt="`${dressCodeConfig.heading} inspiration`" class="h-full w-full object-cover" loading="lazy" decoding="async" />
              </figure>
            </article>

            <article v-if="eventNotesConfig.enabled" data-reveal="copy" class="guidance-panel">
              <h2 class="text-5xl leading-none wedding-display sm:text-7xl">{{ eventNotesConfig.heading }}</h2>
              <p v-if="eventNotesConfig.subtitle" class="mt-5 max-w-xl text-sm leading-7 text-white/55">{{ eventNotesConfig.subtitle }}</p>
              <div v-if="eventNotesConfig.items.length" class="mt-9 divide-y divide-white/15 border-y border-white/15">
                <div v-for="item in eventNotesConfig.items" :key="`${item.icon}:${item.title}`" class="flex gap-4 py-6">
                  <component :is="eventNoteIcon(item.icon)" class="mt-1 h-5 w-5 shrink-0 text-white/55" aria-hidden="true" />
                  <div>
                    <h3 class="text-xl wedding-display">{{ item.title }}</h3>
                    <p v-if="item.body" class="mt-2 text-sm leading-7 text-white/60">{{ item.body }}</p>
                  </div>
                </div>
              </div>
              <p v-else class="mt-9 border-y border-white/15 py-7 text-sm text-white/50">The organizer will add practical details here.</p>
            </article>
          </div>
        </div>
      </section>

      <section v-if="showSection('wish')" id="wish" class="bg-black px-5 py-28 text-white sm:px-8 sm:py-36">
        <div class="mx-auto max-w-7xl">
          <div data-reveal="copy" class="max-w-3xl">
            <h2 class="text-6xl leading-none wedding-display sm:text-8xl">{{ publicCopy.wishHeading }}</h2>
            <p class="mt-6 max-w-2xl text-lg leading-8 text-white/70">
              Wishes shared by the people who make this celebration meaningful. Attendance responses remain private on each guest's RSVP page.
            </p>
            <p v-if="rsvpDeadlineLabel" class="mt-5 flex items-center gap-2 text-xs text-white/50">
              <CalendarDays class="h-4 w-4" aria-hidden="true" />
              Private invitations accept responses until {{ rsvpDeadlineLabel }}
            </p>
          </div>
        </div>

        <div v-if="wishesUnlocked && website.approved_wishes?.length" class="mt-24 border-y border-white/15 py-12">
          <div class="mx-auto mb-10 flex max-w-7xl items-end justify-between gap-5 px-5 sm:px-8">
            <div data-reveal="copy">
              <h3 class="text-4xl leading-none wedding-display sm:text-5xl">Messages from your people.</h3>
              <p class="mt-3 text-sm text-white/50">{{ website.approved_wishes.length }} approved {{ website.approved_wishes.length === 1 ? 'wish' : 'wishes' }} shared for this celebration.</p>
            </div>
            <Button type="button" size="icon" variant="outline" class="shrink-0 rounded-full border-white/30 bg-transparent text-white hover:bg-white hover:text-black" :aria-label="wishesPaused ? 'Play wishes carousel' : 'Pause wishes carousel'" @click="wishesPaused = !wishesPaused">
              <Play v-if="wishesPaused" class="h-4 w-4" aria-hidden="true" />
              <Pause v-else class="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
          <div class="wish-marquee overflow-hidden" aria-label="Approved guest wishes">
            <div class="wish-track flex w-max" :class="wishesPaused ? 'is-paused' : ''">
              <div v-for="cycle in 2" :key="cycle" class="wish-set flex shrink-0 gap-4 pr-4" :aria-hidden="cycle === 2 ? 'true' : undefined">
                <article v-for="wish in website.approved_wishes" :key="`${cycle}:${wish.name}:${wish.message}`" class="flex w-[min(82vw,24rem)] shrink-0 flex-col justify-between bg-[#171717] p-7 sm:w-[26rem] sm:p-8">
                  <div>
                    <Heart class="h-6 w-6 stroke-1 text-white/35" aria-hidden="true" />
                    <p class="mt-8 text-lg leading-8 text-white/80">“{{ wish.message }}”</p>
                  </div>
                  <div class="mt-10 flex items-center gap-3 border-t border-white/15 pt-5">
                    <span class="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-white/20 text-sm wedding-display" aria-hidden="true">{{ wishInitials(wish.name) }}</span>
                    <span>
                      <span class="block text-sm text-white">{{ wish.name }}</span>
                      <span class="mt-0.5 block text-xs text-white/40">Guest wish</span>
                    </span>
                  </div>
                </article>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="!wishesUnlocked" data-reveal="copy" class="mx-auto mt-20 max-w-4xl border-y border-white/15 py-12 text-center">
          <LockKeyhole class="mx-auto h-7 w-7 stroke-1 text-white/45" aria-hidden="true" />
          <h3 class="mt-7 text-4xl leading-none wedding-display sm:text-5xl">Wishes open on the {{ wishRevealDayLabel }}.</h3>
          <p class="mx-auto mt-4 max-w-xl text-sm leading-6 text-white/55">
            Approved messages are safely held until {{ formatLongDate(event.starts_at) }}. The guest book will open automatically when the celebration begins.
          </p>
          <div class="mx-auto mt-9 grid max-w-2xl grid-cols-4 divide-x divide-white/15 border-y border-white/15 py-5" role="timer" aria-live="off" aria-label="Time until guest wishes are revealed">
            <div v-for="part in countdown.parts" :key="part.label" class="px-2">
              <span class="block text-3xl tabular-nums wedding-display sm:text-4xl">{{ part.value }}</span>
              <span class="mt-1 block text-[0.65rem] uppercase tracking-[0.12em] text-white/45">{{ part.label }}</span>
            </div>
          </div>
        </div>
        <div v-else data-reveal="copy" class="mx-auto mt-20 max-w-3xl border-y border-white/15 py-9 text-center">
          <p class="text-lg text-white">The guest book is ready.</p>
          <p class="mt-2 text-sm leading-6 text-white/50">Approved messages will gather here as guests send their wishes.</p>
        </div>
      </section>

      <section v-if="showSection('gallery')" id="gallery" class="relative min-h-svh overflow-hidden bg-black px-5 py-28 text-white sm:px-8 sm:py-40">
        <div class="mx-auto max-w-7xl">
          <div v-if="galleryImages.length">
            <div data-reveal="copy" class="mb-12 flex flex-col gap-3 border-b border-white/15 pb-6 sm:flex-row sm:items-end sm:justify-between">
              <h2 class="max-w-3xl text-5xl leading-none wedding-display sm:text-7xl">Photographs from the celebration.</h2>
              <p class="text-sm tabular-nums text-white/50">{{ galleryImages.length }} {{ galleryImages.length === 1 ? 'image' : 'images' }}</p>
            </div>
            <div class="grid auto-rows-[14rem] grid-cols-2 gap-3 sm:auto-rows-[22rem] sm:grid-cols-4">
              <figure v-for="(image, index) in galleryImages" :key="image.public_id" class="overflow-hidden" :class="galleryClass(index)">
                <img :src="image.image_url" :alt="image.alt_text" class="h-full w-full object-cover grayscale transition duration-700 hover:grayscale-0" loading="lazy" decoding="async" />
              </figure>
            </div>
          </div>
          <div v-else-if="heroImage" class="mx-auto aspect-[4/5] max-w-xl overflow-hidden">
            <img :src="heroImage.image_url" :alt="heroImage.alt_text" class="h-full w-full object-cover grayscale" loading="lazy" decoding="async" />
          </div>
          <div v-else class="empty-visual mx-auto aspect-[4/5] max-w-xl">
            <Camera class="h-9 w-9 text-white/45" aria-hidden="true" />
            <p class="mt-5 text-lg text-white">A gallery made for the memories.</p>
            <p class="mt-2 max-w-sm text-center text-sm leading-6 text-white/50">Photographs will settle into this space as soon as the organizer adds them.</p>
          </div>
        </div>
      </section>

      <section id="closing" class="relative isolate flex min-h-svh items-center justify-center overflow-hidden bg-black px-5 py-28 text-white sm:px-8">
        <img
          v-if="closingImage"
          :src="closingImage.image_url"
          :alt="closingImage.alt_text"
          class="absolute inset-0 h-full w-full object-cover grayscale"
          loading="lazy"
        />
        <div class="absolute inset-0 bg-black/55" />
        <GardenBotanicalDecoration v-if="isGardenVow" placement="frame" />
        <GardenBotanicalDecoration v-if="isGardenVow" placement="corner" />
        <div class="relative z-10 mx-auto max-w-6xl text-center">
          <p data-reveal="copy" class="text-balance text-[clamp(4rem,12vw,6rem)] leading-[0.9] wedding-display">{{ website.closing_message || 'With love' }}</p>
          <p class="mt-10 text-sm tracking-[0.12em] text-white/65">{{ participantHeading }}</p>
          <p class="mt-3 text-sm tabular-nums text-white/55">{{ formatLongDate(event.starts_at) }}</p>
        </div>
      </section>
    </main>

    <Transition name="story-jump">
      <Button
        v-if="showStoryJump && !showPreloader && !welcomeOpen"
        type="button"
        variant="outline"
        class="fixed bottom-6 left-1/2 z-40 h-12 -translate-x-1/2 rounded-full border-white/30 bg-black/75 px-5 text-white shadow-[0_10px_30px_rgba(0,0,0,0.3)] backdrop-blur-md transition-transform duration-300 hover:-translate-y-1 hover:bg-white hover:text-black"
        @click="scrollToStory"
      >
        <BookOpenText class="h-4 w-4" aria-hidden="true" />
        Our story
        <ArrowDown class="h-4 w-4" aria-hidden="true" />
      </Button>
    </Transition>

    <footer class="border-t border-white/15 bg-black px-5 pb-10 pt-16 text-white sm:px-8 sm:pb-14 sm:pt-20">
      <div class="mx-auto max-w-7xl">
        <div data-reveal="rule" class="h-px origin-left bg-white/25" />
        <div class="grid gap-12 py-12 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr]">
          <div data-reveal="copy">
            <p class="max-w-xl text-4xl leading-none wedding-display sm:text-5xl">{{ participantHeading }}</p>
            <p class="mt-5 max-w-md text-sm leading-6 text-white/55">{{ website.closing_message || 'Thank you for being part of this day.' }}</p>
          </div>
          <div data-reveal="copy">
            <p class="text-sm text-white">{{ formatLongDate(event.starts_at) }}</p>
            <p class="mt-3 text-sm leading-6 text-white/55">{{ schedules[0]?.venue_name || event.location?.name || 'Venue details to follow' }}</p>
          </div>
          <nav data-reveal="copy" class="flex flex-col items-start gap-3 text-sm" aria-label="Footer navigation">
            <a v-if="showSection('event_detail')" href="#details" class="footer-link">Event detail</a>
            <a v-if="showSection('story')" href="#story" class="footer-link">Our story</a>
            <a v-if="showSection('gallery')" href="#gallery" class="footer-link">Gallery</a>
            <a v-if="showSection('wish')" href="#wish" class="footer-link">Guest wishes</a>
          </nav>
        </div>
        <div class="flex flex-col gap-3 border-t border-white/15 pt-6 text-xs text-white/40 sm:flex-row sm:items-center sm:justify-between">
          <p>{{ event.business?.display_name || 'Event invitation' }}</p>
          <p>Created with PixelCore</p>
        </div>
      </div>
    </footer>

    <Button
      v-if="musicAvailable"
      type="button"
      size="icon"
      variant="outline"
      class="fixed bottom-5 right-20 z-40 rounded-full border-white/30 bg-black/60 text-white backdrop-blur-md hover:bg-white hover:text-black"
      :aria-label="isMusicPlaying ? 'Pause background music' : 'Play background music'"
      @click="toggleMusic"
    >
      <Volume2 v-if="isMusicPlaying" class="h-4 w-4" aria-hidden="true" />
      <VolumeX v-else class="h-4 w-4" aria-hidden="true" />
    </Button>

    <Button type="button" size="icon" variant="outline" class="fixed bottom-5 right-5 z-40 rounded-full border-white/30 bg-black/60 text-white backdrop-blur-md hover:bg-white hover:text-black" aria-label="Return to top" @click="scrollToTop">
      <ArrowUp class="h-4 w-4" aria-hidden="true" />
    </Button>
  </div>
</template>

<script setup>
import {
  ArrowDown,
  ArrowUp,
  ArrowUpRight,
  BookOpenText,
  CalendarDays,
  CalendarPlus,
  Camera,
  Car,
  Gift,
  GlassWater,
  Heart,
  Hotel,
  Info,
  LockKeyhole,
  MapPin,
  Music2,
  Pause,
  Play,
  Sparkles,
  Utensils,
  UserRound,
  Volume2,
  VolumeX,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { toast } from '@/components/ui/toast'
import GardenBotanicalDecoration from '@/components/event/GardenBotanicalDecoration.vue'
import { eventTemplate, templateGroupForEventType } from '@/utils/eventTemplates'
import { normalizeEventSectionsConfig } from '@/utils/eventRsvpConfig'

const props = defineProps({
  payload: { type: Object, required: true },
})

const emit = defineEmits(['refresh'])
const config = useRuntimeConfig()
const pageRef = ref(null)
const musicRef = ref(null)
const loadingProgress = ref(10)
const showPreloader = ref(true)
const welcomeOpen = ref(false)
const isMusicPlaying = ref(false)
const nowTimestamp = ref(Date.now())
const scrollY = ref(0)
const activeScheduleIndex = ref(0)
const wishesPaused = ref(false)
const storyReached = ref(false)
let progressTimer
let countdownTimer
let wishRefreshTimer
let revealObserver

const event = computed(() => props.payload?.event || {})
const website = computed(() => event.value.website || {})
const selectedTemplate = computed(() => eventTemplate(website.value.website_template))
const isGardenVow = computed(() => website.value.website_template === 'wedding_garden')
const templateGroup = computed(() => templateGroupForEventType(event.value.event_type))
const sectionConfig = computed(() => normalizeEventSectionsConfig(website.value.sections_config))
const rsvpConfig = computed(() => sectionConfig.value.rsvp)
const dressCodeConfig = computed(() => sectionConfig.value.dress_code)
const eventNotesConfig = computed(() => sectionConfig.value.event_notes)
const rsvpDeadline = computed(() => {
  if (!rsvpConfig.value.deadline) return null
  const value = new Date(rsvpConfig.value.deadline)
  return Number.isNaN(value.getTime()) ? null : value
})
const rsvpDeadlineLabel = computed(() => {
  if (!rsvpDeadline.value) return ''
  return new Intl.DateTimeFormat('en-PH', {
    dateStyle: 'long',
    timeStyle: 'short',
    timeZone: event.value.timezone || 'Asia/Manila',
  }).format(rsvpDeadline.value)
})
const media = computed(() => website.value.media || [])
const heroImage = computed(() => media.value.find(item => item.placement === 'hero' && item.is_featured) || media.value.find(item => item.placement === 'hero') || (website.value.thumbnail_url ? { image_url: website.value.thumbnail_url, alt_text: `${event.value.title} event photograph` } : null))
const popupImage = computed(() => media.value.find(item => item.placement === 'popup') || heroImage.value)
const galleryImages = computed(() => media.value.filter(item => item.placement === 'gallery'))
const closingImage = computed(() => media.value.find(item => item.placement === 'closing') || null)
const heroDate = computed(() => website.value.hero_date_text || compactDate(event.value.starts_at))
const participantHeading = computed(() => website.value.participants?.map(person => person.name).filter(Boolean).join('\n') || event.value.title)
const headerMark = computed(() => {
  const names = website.value.participants?.map(person => person.name).filter(Boolean).slice(0, 2) || []
  if (website.value.header_mark_text) return website.value.header_mark_text
  return templateGroup.value === 'wedding' && names.length ? names.join(' × ') : event.value.title || event.value.business?.display_name || 'Our event'
})
const headerLogo = computed(() => website.value.header_mark_type === 'logo' ? event.value.business?.logo || '' : '')
const showStoryJump = computed(() => showSection('story') && !storyReached.value)
const schedules = computed(() => website.value.schedule_entries || [])
const activeSchedule = computed(() => schedules.value[activeScheduleIndex.value] || null)
const mapLocation = computed(() => {
  const selected = activeSchedule.value
  const selectedHasMap = selected?.map_url || (
    selected?.latitude !== null
    && selected?.latitude !== undefined
    && selected?.longitude !== null
    && selected?.longitude !== undefined
  )
  if (selectedHasMap) return selected
  return schedules.value.find(entry => (
    entry.map_url
    || (
      entry.latitude !== null
      && entry.latitude !== undefined
      && entry.longitude !== null
      && entry.longitude !== undefined
    )
  )) || event.value.location || null
})
const mapVenueName = computed(() => mapLocation.value?.venue_name || mapLocation.value?.name || 'Event venue')
const mapDirectionsUrl = computed(() => mapLocation.value?.map_url || (mapLocation.value?.latitude && mapLocation.value?.longitude ? `https://www.google.com/maps/search/?api=1&query=${mapLocation.value.latitude},${mapLocation.value.longitude}` : ''))
const mapImageUrl = computed(() => {
  const token = String(config.public.mapboxAccessToken || '')
  const latitude = Number(mapLocation.value?.latitude)
  const longitude = Number(mapLocation.value?.longitude)
  if (!token || !Number.isFinite(latitude) || !Number.isFinite(longitude)) return ''
  const marker = `pin-s+ffffff(${longitude},${latitude})`
  return `https://api.mapbox.com/styles/v1/mapbox/dark-v11/static/${marker}/${longitude},${latitude},14,0/1200x525@2x?access_token=${encodeURIComponent(token)}`
})
const showQuote = computed(() => showSection('quote'))
const musicAvailable = computed(() => Boolean(website.value.music_enabled && website.value.background_music_url))
const showCountdown = computed(() => Boolean(website.value.countdown_enabled && Number.isFinite(new Date(event.value.starts_at).getTime())))
const countdown = computed(() => {
  const eventTime = new Date(event.value.starts_at).getTime()
  const remaining = Math.max(0, eventTime - nowTimestamp.value)
  const totalSeconds = Math.floor(remaining / 1000)
  const days = Math.floor(totalSeconds / 86400)
  const hours = Math.floor((totalSeconds % 86400) / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  return {
    isComplete: remaining <= 0,
    parts: [
      { label: 'Days', value: String(days).padStart(2, '0') },
      { label: 'Hours', value: String(hours).padStart(2, '0') },
      { label: 'Minutes', value: String(minutes).padStart(2, '0') },
      { label: 'Seconds', value: String(seconds).padStart(2, '0') },
    ],
  }
})
const wishesUnlocked = computed(() => website.value.wish_display_mode !== 'event_day' || countdown.value.isComplete)
const needsCountdownClock = computed(() => (
  showCountdown.value
  || website.value.wish_display_mode === 'event_day'
  || Boolean(rsvpDeadline.value)
))
const wishRevealDayLabel = computed(() => templateGroup.value === 'wedding' ? 'wedding day' : 'event day')
const popupTitle = computed(() => website.value.popup_title || publicCopy.value.popupTitle)
const popupMessage = computed(() => website.value.popup_message || website.value.invitation_text || event.value.description || publicCopy.value.popupMessage)
const publicCopy = computed(() => {
  if (templateGroup.value === 'birthday') {
    return {
      salutation: 'You are invited,',
      detailHeading: 'A celebration worth making room for.',
      participantLabel: 'Celebrating',
      wishHeading: 'Joy from our people.',
      popupTitle: 'Come celebrate with us.',
      popupMessage: 'Open the details, save the date, and explore everything prepared for the celebration.',
      countdownComplete: 'The celebration is here.',
    }
  }
  if (templateGroup.value === 'general') {
    return {
      salutation: 'Welcome,',
      detailHeading: 'Everything, in the right place.',
      participantLabel: 'At the center of the event',
      wishHeading: 'Notes from our guests.',
      popupTitle: 'Welcome to the event.',
      popupMessage: 'Explore the programme, location, and everything prepared for the day.',
      countdownComplete: 'The event is underway.',
    }
  }
  return {
    salutation: 'Dear,',
    detailHeading: 'Every moment, held with intention.',
    participantLabel: 'The wedding of',
    wishHeading: 'Wishes from our people.',
    popupTitle: 'Welcome to our celebration.',
    popupMessage: 'We are so glad you are here. Enter to explore the day and everything prepared for the celebration.',
    countdownComplete: 'Today, we celebrate.',
  }
})
const headingFontStack = computed(() => `'${website.value.heading_font || 'Bodoni Moda'}', Georgia, serif`)
const bodyFontStack = computed(() => `'${website.value.body_font || 'Manrope'}', Arial, sans-serif`)
const pageStyle = computed(() => ({
  '--event-bg': website.value.theme_background || '#000000',
  '--event-text': website.value.theme_text || '#F5F3EE',
  '--event-accent': website.value.theme_accent || '#D6D1C8',
  '--event-heading': headingFontStack.value,
  '--event-body': bodyFontStack.value,
}))
const heroImageStyle = computed(() => ({ transform: `translate3d(0, ${Math.min(scrollY.value * 0.12, 80)}px, 0) scale(1.08)` }))

useHead(() => ({
  title: `${event.value.title || 'Event invitation'} | ${event.value.business?.display_name || 'PixelCore'}`,
  meta: [{ name: 'referrer', content: 'no-referrer' }, { name: 'theme-color', content: website.value.theme_background || '#000000' }],
  link: [{ rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500&family=Cormorant+Garamond:wght@400;500&family=Italiana&family=Manrope:wght@400;500;600&family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Playball&display=swap' }],
}))

onMounted(() => {
  progressTimer = window.setInterval(() => {
    loadingProgress.value = Math.min(92, loadingProgress.value + 11)
  }, 65)
  window.addEventListener('scroll', updateScroll, { passive: true })
  updateStoryJump()
  if (needsCountdownClock.value) {
    countdownTimer = window.setInterval(() => {
      nowTimestamp.value = Date.now()
    }, 1000)
  }
  wishRefreshTimer = window.setInterval(() => {
    if (document.hidden || !showSection('wish')) return
    emit('refresh')
  }, 30000)
  window.requestAnimationFrame(setupEntryTransitions)
  if (!heroImage.value) finishPreloader()
  window.setTimeout(finishPreloader, 900)
})

onBeforeUnmount(() => {
  window.clearInterval(progressTimer)
  window.clearInterval(countdownTimer)
  window.clearInterval(wishRefreshTimer)
  window.removeEventListener('scroll', updateScroll)
  revealObserver?.disconnect()
  pageRef.value?.classList.remove('reveal-ready')
})

function finishPreloader() {
  if (loadingProgress.value === 100) return
  loadingProgress.value = 100
  window.clearInterval(progressTimer)
  window.setTimeout(() => {
    showPreloader.value = false
    if (website.value.popup_enabled) welcomeOpen.value = true
  }, 420)
}

async function beginExperience() {
  welcomeOpen.value = false
  if (musicAvailable.value) await playMusic()
}

async function toggleMusic() {
  if (!musicRef.value) return
  if (isMusicPlaying.value) {
    musicRef.value.pause()
    return
  }
  await playMusic()
}

async function playMusic() {
  if (!musicRef.value) return
  musicRef.value.volume = Math.max(0, Math.min(1, Number(website.value.music_volume || 35) / 100))
  try {
    await musicRef.value.play()
  } catch {
    toast({
      title: 'Music needs one more tap',
      description: 'Use the sound control at the bottom of the page to begin playback.',
    })
  }
}

function updateScroll() {
  updateStoryJump()
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  scrollY.value = window.scrollY
}

function updateStoryJump() {
  const storySection = pageRef.value?.querySelector('#story')
  if (!storySection) {
    storyReached.value = true
    return
  }
  storyReached.value = storySection.getBoundingClientRect().top <= window.innerHeight * 0.72
}

function showSection(name) {
  return sectionConfig.value[name] !== false
}

function setupEntryTransitions() {
  const elements = Array.from(pageRef.value?.querySelectorAll('[data-reveal]') || [])
  if (!elements.length) return

  pageRef.value.classList.add('reveal-ready')
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !('IntersectionObserver' in window)) {
    elements.forEach(element => element.classList.add('is-visible'))
    return
  }

  revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return
      entry.target.classList.add('is-visible')
      revealObserver?.unobserve(entry.target)
    })
  }, {
    rootMargin: '0px 0px -12% 0px',
    threshold: 0.12,
  })

  elements.forEach(element => revealObserver.observe(element))
}

function revealDelay(index) {
  return { '--reveal-delay': `${Math.min(index, 4) * 70}ms` }
}

function storyImage(block) {
  if (!block.image_url) return null
  return {
    image_url: block.image_url,
    alt_text: block.image_alt_text || (block.title ? `Photograph for ${block.title}` : 'Event story photograph'),
  }
}

function scheduleIcon(entry, index) {
  const label = `${entry?.title || ''} ${entry?.venue_name || ''}`.toLowerCase()
  if (label.includes('photo')) return Camera
  if (label.includes('ceremony') || label.includes('wedding')) return Heart
  if (label.includes('dinner') || label.includes('meal') || label.includes('reception')) return Utensils
  if (label.includes('dance') || label.includes('music')) return Music2
  if (label.includes('toast') || label.includes('cocktail')) return GlassWater
  return index % 2 === 0 ? CalendarDays : Sparkles
}

function eventNoteIcon(icon) {
  return {
    calendar: CalendarDays,
    car: Car,
    gift: Gift,
    heart: Heart,
    hotel: Hotel,
    info: Info,
    sparkles: Sparkles,
    utensils: Utensils,
  }[icon] || Info
}

function wishInitials(name) {
  return String(name || 'Guest')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part.charAt(0).toUpperCase())
    .join('')
}

function galleryClass(index) {
  return index % 5 === 0 ? 'col-span-2 row-span-2' : index % 3 === 0 ? 'row-span-2' : ''
}

function downloadCalendar() {
  const start = toIcsDate(event.value.starts_at)
  const end = toIcsDate(event.value.ends_at || event.value.starts_at)
  const location = schedules.value[0]?.address || schedules.value[0]?.venue_name || event.value.location?.name || ''
  const content = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'BEGIN:VEVENT', `DTSTART:${start}`, `DTEND:${end}`, `SUMMARY:${escapeIcs(event.value.title)}`, `LOCATION:${escapeIcs(location)}`, 'END:VEVENT', 'END:VCALENDAR'].join('\r\n')
  const url = URL.createObjectURL(new Blob([content], { type: 'text/calendar;charset=utf-8' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${String(event.value.title || 'event').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.ics`
  anchor.click()
  URL.revokeObjectURL(url)
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
}

function scrollToStory() {
  pageRef.value?.querySelector('#story')?.scrollIntoView({
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    block: 'start',
  })
}

function formatLongDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('en-PH', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).format(new Date(value))
}

function formatTimeRange(start, end, endLabel) {
  const formatter = new Intl.DateTimeFormat('en-PH', { hour: 'numeric', minute: '2-digit' })
  if (!end) return `${formatter.format(new Date(start))}${endLabel ? ` – ${endLabel}` : ''}`
  return `${formatter.format(new Date(start))} – ${formatter.format(new Date(end))}`
}

function formatTime(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('en-PH', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatShortDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value))
}

function compactDate(value) {
  if (!value) return ''
  const date = new Date(value)
  return `${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}${String(date.getFullYear()).slice(-2)}`
}

function toIcsDate(value) {
  return new Date(value).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

function escapeIcs(value) {
  return String(value || '').replace(/([,;])/g, '\\$1').replace(/\n/g, '\\n')
}
</script>

<style scoped>
.wedding-invitation {
  background: var(--event-bg);
  color: var(--event-text);
  font-family: var(--event-body);
  scrollbar-color: color-mix(in srgb, var(--event-accent) 55%, transparent) var(--event-bg);
}

.wedding-invitation ::selection {
  background: var(--event-accent);
  color: var(--event-bg);
}

.wedding-invitation.template-garden img,
.wedding-invitation.template-community img {
  filter: sepia(0.12) saturate(0.82) !important;
}

.wedding-invitation.template-garden nav {
  border-color: color-mix(in srgb, var(--event-accent) 34%, transparent);
  background: color-mix(in srgb, var(--event-bg) 84%, transparent);
}

.wedding-invitation.template-garden #hero::before {
  position: absolute;
  inset: clamp(5.8rem, 10vw, 8rem) clamp(1rem, 4vw, 4rem) clamp(1rem, 4vw, 4rem);
  z-index: 2;
  border: 1px solid color-mix(in srgb, var(--event-accent) 58%, transparent);
  content: '';
  pointer-events: none;
}

.wedding-invitation.template-garden .hero-content {
  margin: 0 auto;
  max-width: 72rem;
}

.wedding-invitation.template-garden .hero-content h1 {
  text-shadow: 0 0.15em 0.8em color-mix(in srgb, var(--event-bg) 72%, transparent);
}

.wedding-invitation.template-garden .event-timeline::before {
  width: 1px;
  background: var(--event-accent);
}

.wedding-invitation.template-garden .timeline-node {
  border-color: var(--event-accent);
  background: var(--event-bg);
  box-shadow: 0 0 0 0.5rem var(--event-bg);
}

.wedding-invitation.template-garden .timeline-node.is-active {
  background: var(--event-accent);
}

.wedding-invitation.template-garden .schedule-focus,
.wedding-invitation.template-garden .guidance-panel,
.wedding-invitation.template-garden .rsvp-confirmation {
  border-color: color-mix(in srgb, var(--event-accent) 48%, transparent);
  background: color-mix(in srgb, var(--event-bg) 88%, var(--event-accent));
}

.wedding-invitation.template-garden .guidance-panel {
  position: relative;
  padding: clamp(1.5rem, 4vw, 3rem);
  border: 1px solid color-mix(in srgb, var(--event-accent) 40%, transparent);
}

.wedding-invitation.template-garden .guidance-panel::after {
  position: absolute;
  inset: 0.55rem;
  border: 1px solid color-mix(in srgb, var(--event-accent) 18%, transparent);
  content: '';
  pointer-events: none;
}

.wedding-invitation.template-garden #wish > div:first-child {
  position: relative;
  padding: clamp(1.5rem, 5vw, 4rem);
  border: 1px solid color-mix(in srgb, var(--event-accent) 44%, transparent);
}

.wedding-invitation.template-garden #closing::after {
  position: absolute;
  inset: clamp(1rem, 4vw, 4rem);
  z-index: 2;
  border: 1px solid color-mix(in srgb, var(--event-accent) 52%, transparent);
  content: '';
  pointer-events: none;
}

.wedding-invitation.template-garden footer {
  border-color: color-mix(in srgb, var(--event-accent) 35%, transparent);
  background: color-mix(in srgb, var(--event-bg) 94%, black);
}

.wedding-invitation.template-birthday-color img {
  filter: saturate(1.08) contrast(1.02) !important;
}

.wedding-invitation.template-milestone img {
  filter: sepia(0.18) saturate(0.72) !important;
}

.wedding-invitation.template-modern .hero-content,
.wedding-invitation.template-spotlight .hero-content,
.wedding-invitation.template-studio .hero-content {
  align-items: flex-start;
  padding-left: max(2rem, 8vw);
  padding-right: max(2rem, 8vw);
  text-align: left;
}

.wedding-invitation.template-modern .hero-content h1,
.wedding-invitation.template-spotlight .hero-content h1,
.wedding-invitation.template-studio .hero-content h1 {
  margin-left: 0;
  margin-right: 0;
}

.wedding-invitation.template-birthday-color #hero::after,
.wedding-invitation.template-after-dark #hero::after,
.wedding-invitation.template-community #hero::after {
  position: absolute;
  right: -8vw;
  top: 16vh;
  z-index: 1;
  width: min(34vw, 30rem);
  height: min(34vw, 30rem);
  border: 1px solid color-mix(in srgb, var(--event-accent) 62%, transparent);
  border-radius: 9999px;
  content: '';
  pointer-events: none;
}

.wedding-invitation.template-garden .quote-panel,
.wedding-invitation.template-milestone .quote-panel,
.wedding-invitation.template-community .quote-panel {
  background-color: color-mix(in srgb, var(--event-bg) 82%, var(--event-accent));
}

.wedding-invitation main > section:not(#hero):not(.quote-panel) {
  background-color: var(--event-bg);
  color: var(--event-text);
}

.wedding-display {
  font-family: var(--event-heading);
  font-weight: 400;
  letter-spacing: -0.03em;
  white-space: pre-line;
}

.event-script {
  font-family: 'Playball', cursive;
  letter-spacing: -0.02em;
  text-decoration: none;
}

.nav-link {
  flex: none;
  padding: 0.5rem 0.75rem;
  font-size: 0.7rem;
  color: rgb(255 255 255 / 0.65);
  text-decoration: none;
  transition: color 180ms ease-out;
}

.nav-link:hover,
.nav-link:focus-visible {
  color: white;
  outline: none;
}

.empty-state {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.empty-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid rgb(255 255 255 / 0.15);
  background: #0d0d0d;
  padding: 2rem;
}

.footer-link {
  color: rgb(255 255 255 / 0.58);
  text-decoration-color: transparent;
  text-underline-offset: 0.35rem;
  transition:
    color 180ms ease-out,
    text-decoration-color 180ms ease-out;
}

.footer-link:hover,
.footer-link:focus-visible {
  color: white;
  outline: none;
  text-decoration-line: underline;
  text-decoration-color: rgb(255 255 255 / 0.45);
}

.event-timeline::before {
  position: absolute;
  top: 6.5rem;
  bottom: 6.5rem;
  left: 1.5rem;
  width: 2px;
  background: color-mix(in srgb, var(--event-accent) 70%, transparent);
  content: '';
}

.timeline-node {
  box-shadow: 0 0 0 0.4rem var(--event-bg);
  transition:
    transform 220ms cubic-bezier(0.16, 1, 0.3, 1),
    background-color 220ms cubic-bezier(0.16, 1, 0.3, 1);
}

.timeline-node.is-active {
  transform: translate(-50%, -50%) scale(1.25);
}

.wish-track {
  animation: wish-scroll 42s linear infinite;
}

.wish-track.is-paused,
.wish-marquee:hover .wish-track,
.wish-marquee:focus-within .wish-track {
  animation-play-state: paused;
}

@keyframes wish-scroll {
  to {
    transform: translateX(-50%);
  }
}

@media (min-width: 640px) {
  .event-timeline::before {
    top: 8rem;
    bottom: 8rem;
    left: 50%;
  }
}

.reveal-ready [data-reveal] {
  transition-delay: var(--reveal-delay, 0ms);
}

.reveal-ready [data-reveal="copy"] {
  opacity: 0;
  transform: translate3d(0, 2rem, 0);
  transition:
    opacity 720ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 720ms cubic-bezier(0.16, 1, 0.3, 1);
}

.reveal-ready [data-reveal="media"] {
  opacity: 0.35;
  clip-path: inset(0 0 100% 0);
  transition:
    opacity 880ms cubic-bezier(0.16, 1, 0.3, 1),
    clip-path 880ms cubic-bezier(0.16, 1, 0.3, 1);
}

.reveal-ready [data-reveal="rule"] {
  transform: scaleX(0);
  transition: transform 880ms cubic-bezier(0.16, 1, 0.3, 1);
}

.reveal-ready [data-reveal].is-visible {
  opacity: 1;
  transform: none;
  clip-path: inset(0 0 0 0);
}

.preloader-frame {
  transform: scale(1);
  transition: transform 360ms cubic-bezier(0.16, 1, 0.3, 1);
}

.preloader-frame.is-complete {
  transform: scale(1.9, 0.075);
}

.preloader-frame.is-complete p {
  opacity: 0;
}

.preloader-enter-active,
.preloader-leave-active {
  transition: opacity 500ms cubic-bezier(0.16, 1, 0.3, 1);
}

.preloader-enter-from,
.preloader-leave-to {
  opacity: 0;
}

.story-jump-enter-active,
.story-jump-leave-active {
  transition:
    opacity 240ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 240ms cubic-bezier(0.16, 1, 0.3, 1);
}

.story-jump-enter-from,
.story-jump-leave-to {
  opacity: 0;
  transform: translate(-50%, 1rem);
}

.schedule-shift-enter-active,
.schedule-shift-leave-active {
  transition:
    opacity 280ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 280ms cubic-bezier(0.16, 1, 0.3, 1);
}

.schedule-shift-enter-from {
  opacity: 0;
  transform: translate3d(1.5rem, 0, 0);
}

.schedule-shift-leave-to {
  opacity: 0;
  transform: translate3d(-1rem, 0, 0);
}

@media (prefers-reduced-motion: reduce) {
  .wedding-invitation *,
  .wedding-invitation *::before,
  .wedding-invitation *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }

  .reveal-ready [data-reveal] {
    opacity: 1;
    transform: none;
    clip-path: none;
  }

  .wish-track {
    animation: none;
    transform: none;
  }
}
</style>
