<template>
  <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
    <Card class="min-w-0 overflow-hidden">
      <CardHeader class="border-b p-5">
        <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle class="flex items-center gap-2 text-lg">
              <PanelsTopLeft class="h-5 w-5 text-primary" aria-hidden="true" />
              {{ eventTypeLabel(form.event_type) }} website
            </CardTitle>
            <CardDescription class="mt-1 max-w-2xl leading-6">
              Shape the public event page here. Private guest links open a separate RSVP page that keeps the same theme.
            </CardDescription>
          </div>
          <div class="flex items-center gap-2">
            <Badge :variant="form.website_enabled ? 'secondary' : 'outline'">
              {{ form.website_enabled ? 'Published' : 'Draft' }}
            </Badge>
            <ButtonAnchor
              v-if="form.website_enabled"
              :href="previewUrl"
              target="_blank"
              rel="noopener"
              size="sm"
              variant="outline"
            >
              <ExternalLink class="h-4 w-4" aria-hidden="true" />
              Preview
            </ButtonAnchor>
          </div>
        </div>
      </CardHeader>

      <StatePanel
        v-if="loading"
        class="m-5"
        kind="loading"
        title="Loading event website"
        message="Retrieving the invitation content, photographs, and theme."
      />

      <CardContent v-else class="p-0">
        <Tabs v-model="activeTab" default-value="invitation">
          <div class="overflow-x-auto border-b px-5 pt-4">
            <TabsList class="h-auto min-w-max justify-start">
              <TabsTrigger value="invitation">
                <LetterText class="h-4 w-4" aria-hidden="true" />
                Invitation
              </TabsTrigger>
              <TabsTrigger value="guest-details">
                <Shirt class="h-4 w-4" aria-hidden="true" />
                Guest details
              </TabsTrigger>
              <TabsTrigger value="welcome">
                <Volume2 class="h-4 w-4" aria-hidden="true" />
                Welcome & sound
              </TabsTrigger>
              <TabsTrigger value="schedule">
                <CalendarDays class="h-4 w-4" aria-hidden="true" />
                People & schedule
              </TabsTrigger>
              <TabsTrigger value="story">
                <BookOpenText class="h-4 w-4" aria-hidden="true" />
                Story & quote
              </TabsTrigger>
              <TabsTrigger value="gallery">
                <Images class="h-4 w-4" aria-hidden="true" />
                Gallery
              </TabsTrigger>
              <TabsTrigger value="theme">
                <Palette class="h-4 w-4" aria-hidden="true" />
                Theme
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="invitation" class="m-0 space-y-6 p-5">
            <div class="flex items-start justify-between gap-5 rounded-xl border bg-muted/20 p-4">
              <div>
                <Label for="website-published" class="font-bold">Publish event website</Label>
                <p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">
                  When enabled, anyone with the event page can view the invitation. RSVP controls still require a private guest link.
                </p>
              </div>
              <Switch id="website-published" v-model:checked="form.website_enabled" />
            </div>

            <section class="space-y-4">
              <div class="grid gap-2 sm:max-w-sm">
                <Label>What kind of event is this?</Label>
                <Select :model-value="form.event_type" @update:model-value="changeEventType">
                  <SelectTrigger>
                    <SelectValue placeholder="Choose an event type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="option in eventTypeOptions" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </SelectItem>
                  </SelectContent>
                </Select>
                <p class="text-xs leading-5 text-muted-foreground">The event type controls which landing-page templates are available.</p>
              </div>

              <div>
                <h3 class="font-bold">Choose a template</h3>
                <p class="mt-1 text-sm text-muted-foreground">Each event type includes three distinct compositions. Colors and fonts remain editable in Theme.</p>
                <div class="mt-4 grid gap-3 md:grid-cols-3">
                  <Button
                    v-for="template in availableTemplates"
                    :key="template.value"
                    type="button"
                    variant="outline"
                    class="h-auto min-h-44 items-stretch justify-start overflow-hidden p-0 text-left"
                    :class="form.website_template === template.value ? 'border-primary ring-2 ring-primary/20' : ''"
                    :aria-pressed="form.website_template === template.value"
                    @click="selectTemplate(template)"
                  >
                    <span class="flex w-full flex-col">
                      <span class="template-swatch flex min-h-24 items-end p-4" :style="templatePreviewStyle(template)">
                        <span class="text-2xl leading-none" :style="{ fontFamily: `'${template.preset.heading_font}', Georgia, serif` }">{{ template.label }}</span>
                      </span>
                      <span class="space-y-1 p-4">
                        <span class="block font-semibold">{{ template.label }}</span>
                        <span class="block whitespace-normal text-xs leading-5 text-muted-foreground">{{ template.description }}</span>
                      </span>
                    </span>
                  </Button>
                </div>
              </div>
            </section>

            <div class="grid gap-5 sm:grid-cols-2">
              <div class="grid gap-2 sm:col-span-2">
                <Label for="website-title">Event title</Label>
                <Input id="website-title" v-model="form.title" maxlength="180" />
              </div>
              <div class="grid gap-2">
                <Label>Header identity</Label>
                <Select v-model="form.header_mark_type">
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="text">Cursive event text</SelectItem>
                    <SelectItem value="logo">Business logo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div v-if="form.header_mark_type === 'text'" class="grid gap-2">
                <Label for="header-mark-text">Header text</Label>
                <Input id="header-mark-text" v-model="form.header_mark_text" maxlength="120" :placeholder="participantNames || 'Alex × Jamie'" />
                <p class="text-xs text-muted-foreground">Leave blank to use the participant names automatically.</p>
              </div>
              <div v-else class="flex items-end">
                <p class="text-sm leading-6 text-muted-foreground">The centered header will use the logo saved in Business Identity.</p>
              </div>
              <div class="grid gap-2 sm:col-span-2">
                <Label for="invitation-text">Invitation message</Label>
                <Textarea id="invitation-text" v-model="form.invitation_text" rows="3" maxlength="500" />
              </div>
              <div class="grid gap-2">
                <Label for="hero-date">Large hero date</Label>
                <Input id="hero-date" v-model="form.hero_date_text" maxlength="32" placeholder="091226" />
                <p class="text-xs text-muted-foreground">Leave blank to format the event date automatically.</p>
              </div>
              <div class="grid gap-2">
                <Label for="closing-message">Closing message</Label>
                <Input id="closing-message" v-model="form.closing_message" maxlength="180" placeholder="With love" />
              </div>
            </div>

            <section class="border-y py-5">
              <div class="flex items-start justify-between gap-5">
                <div class="flex min-w-0 gap-3">
                  <TimerReset class="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                  <div>
                    <Label for="countdown-enabled" class="font-bold">Countdown to the event</Label>
                    <p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">Show live days, hours, minutes, and seconds in the landing-page hero. The event start time remains the source of truth.</p>
                  </div>
                </div>
                <Switch id="countdown-enabled" v-model:checked="form.countdown_enabled" />
              </div>
              <div v-if="form.countdown_enabled" class="mt-4 grid gap-2 sm:ml-8 sm:max-w-sm">
                <Label for="countdown-label">Countdown label</Label>
                <Input id="countdown-label" v-model="form.countdown_label" maxlength="80" placeholder="Until we celebrate" />
              </div>
            </section>

            <section class="border-b pb-5">
              <div class="grid gap-4 sm:grid-cols-[minmax(0,1fr)_18rem] sm:items-start">
                <div class="flex min-w-0 gap-3">
                  <Heart class="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                  <div>
                    <Label for="wish-display-mode" class="font-bold">When should approved wishes appear?</Label>
                    <p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">
                      Guests can submit messages at any time. Choose whether approved wishes appear immediately or stay private until the event begins.
                    </p>
                  </div>
                </div>
                <Select v-model="form.wish_display_mode">
                  <SelectTrigger id="wish-display-mode">
                    <SelectValue placeholder="Choose a release time" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="realtime">Show as they are approved</SelectItem>
                    <SelectItem value="event_day">Reveal on the event day</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Alert v-if="form.wish_display_mode === 'event_day'" class="mt-4 sm:ml-8 sm:max-w-2xl">
                <TimerReset class="h-4 w-4" aria-hidden="true" />
                <AlertTitle>The countdown protects the reveal</AlertTitle>
                <AlertDescription>
                  The public page holds approved messages until the event start time, then opens them automatically.
                </AlertDescription>
              </Alert>
            </section>

            <div>
              <h3 class="font-bold">Visible sections</h3>
              <p class="mt-1 text-sm text-muted-foreground">Keep the page focused by hiding sections that are not ready.</p>
              <div class="mt-4 grid gap-3 sm:grid-cols-2">
                <label
                  v-for="section in sectionOptions"
                  :key="section.value"
                  class="flex items-center justify-between gap-4 rounded-xl border px-4 py-3"
                >
                  <span>
                    <span class="block text-sm font-semibold">{{ section.label }}</span>
                    <span class="mt-0.5 block text-xs text-muted-foreground">{{ section.detail }}</span>
                  </span>
                  <Switch v-model:checked="form.sections_config[section.value]" :aria-label="`Show ${section.label}`" />
                </label>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="guest-details" class="m-0 space-y-8 p-5">
            <section class="space-y-5" aria-labelledby="website-dress-code-heading">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div class="flex min-w-0 gap-3">
                  <Shirt class="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                  <div>
                    <h3 id="website-dress-code-heading" class="font-bold">Dress code</h3>
                    <p class="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
                      Give guests clear attire guidance, an optional inspiration image, and a restrained color palette.
                    </p>
                  </div>
                </div>
                <Switch v-model:checked="form.sections_config.dress_code.enabled" aria-label="Show dress code" />
              </div>

              <div
                class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_20rem]"
                :class="!form.sections_config.dress_code.enabled ? 'opacity-55' : ''"
              >
                <div class="grid gap-4 sm:grid-cols-2">
                  <div class="grid gap-2">
                    <Label for="dress-code-heading">Heading</Label>
                    <Input
                      id="dress-code-heading"
                      v-model="form.sections_config.dress_code.heading"
                      maxlength="80"
                      :disabled="!form.sections_config.dress_code.enabled"
                    />
                  </div>
                  <div class="grid gap-2">
                    <Label for="dress-code-subtitle">Short label</Label>
                    <Input
                      id="dress-code-subtitle"
                      v-model="form.sections_config.dress_code.subtitle"
                      maxlength="180"
                      :disabled="!form.sections_config.dress_code.enabled"
                    />
                  </div>
                  <div class="grid gap-2 sm:col-span-2">
                    <Label for="dress-code-description">Guidance</Label>
                    <Textarea
                      id="dress-code-description"
                      v-model="form.sections_config.dress_code.description"
                      rows="4"
                      maxlength="1200"
                      :disabled="!form.sections_config.dress_code.enabled"
                    />
                  </div>
                  <div class="grid gap-2 sm:col-span-2">
                    <Label for="dress-code-media">Inspiration image</Label>
                    <Select v-model="dressCodeMedia" :disabled="!form.sections_config.dress_code.enabled">
                      <SelectTrigger id="dress-code-media">
                        <SelectValue placeholder="No image" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No image</SelectItem>
                        <SelectItem v-for="image in form.media" :key="image.public_id" :value="image.public_id">
                          {{ image.alt_text || image.caption || image.placement }}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <p class="text-xs leading-5 text-muted-foreground">Choose an image from the event media library in Gallery.</p>
                  </div>
                </div>

                <div class="rounded-xl border bg-muted/20 p-4">
                  <div class="flex items-center justify-between gap-3">
                    <div>
                      <h4 class="font-bold">Suggested colors</h4>
                      <p class="mt-1 text-xs text-muted-foreground">Up to eight guest-facing colors.</p>
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      :disabled="!form.sections_config.dress_code.enabled || form.sections_config.dress_code.colors.length >= 8"
                      @click="addDressColor"
                    >
                      <Plus class="h-4 w-4" aria-hidden="true" />
                      Add
                    </Button>
                  </div>
                  <div v-if="form.sections_config.dress_code.colors.length" class="mt-4 space-y-2">
                    <div
                      v-for="(color, index) in form.sections_config.dress_code.colors"
                      :key="`${index}:${color}`"
                      class="flex items-center gap-2"
                    >
                      <Input
                        :model-value="color"
                        class="h-10 w-14 shrink-0 p-1"
                        type="color"
                        :aria-label="`Dress-code color ${index + 1}`"
                        :disabled="!form.sections_config.dress_code.enabled"
                        @update:model-value="value => updateDressColor(index, value)"
                      />
                      <Input
                        :model-value="color"
                        class="min-w-0 flex-1 font-mono uppercase"
                        maxlength="7"
                        :disabled="!form.sections_config.dress_code.enabled"
                        @update:model-value="value => updateDressColor(index, value)"
                      />
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        :disabled="!form.sections_config.dress_code.enabled"
                        :aria-label="`Remove dress-code color ${index + 1}`"
                        @click="form.sections_config.dress_code.colors.splice(index, 1)"
                      >
                        <Trash2 class="h-4 w-4" aria-hidden="true" />
                      </Button>
                    </div>
                  </div>
                  <p v-else class="mt-5 rounded-lg border border-dashed p-4 text-center text-xs text-muted-foreground">
                    Add colors only when they help guests choose what to wear.
                  </p>
                </div>
              </div>
            </section>

            <Separator />

            <section class="space-y-5" aria-labelledby="website-event-notes-heading">
              <div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div class="flex min-w-0 gap-3">
                  <Info class="mt-0.5 h-5 w-5 shrink-0 text-primary" aria-hidden="true" />
                  <div>
                    <div class="flex items-center gap-3">
                      <h3 id="website-event-notes-heading" class="font-bold">Practical event notes</h3>
                      <Switch v-model:checked="form.sections_config.event_notes.enabled" aria-label="Show event notes" />
                    </div>
                    <p class="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
                      Group parking, arrival, accommodation, gift, and accessibility information for guests.
                    </p>
                  </div>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  :disabled="!form.sections_config.event_notes.enabled || form.sections_config.event_notes.items.length >= 8"
                  @click="addEventNote"
                >
                  <Plus class="h-4 w-4" aria-hidden="true" />
                  Add note
                </Button>
              </div>

              <div class="grid gap-4 sm:grid-cols-2">
                <div class="grid gap-2">
                  <Label for="event-notes-heading">Section heading</Label>
                  <Input
                    id="event-notes-heading"
                    v-model="form.sections_config.event_notes.heading"
                    maxlength="80"
                    :disabled="!form.sections_config.event_notes.enabled"
                  />
                </div>
                <div class="grid gap-2">
                  <Label for="event-notes-subtitle">Section introduction</Label>
                  <Input
                    id="event-notes-subtitle"
                    v-model="form.sections_config.event_notes.subtitle"
                    maxlength="180"
                    :disabled="!form.sections_config.event_notes.enabled"
                  />
                </div>
              </div>

              <div v-if="form.sections_config.event_notes.items.length" class="space-y-3">
                <article
                  v-for="(item, index) in form.sections_config.event_notes.items"
                  :key="item.key"
                  class="grid gap-4 rounded-xl border bg-background p-4 lg:grid-cols-[10rem_minmax(0,0.7fr)_minmax(0,1.3fr)_auto] lg:items-end"
                >
                  <div class="grid gap-2">
                    <Label :for="`event-note-icon-${index}`">Icon</Label>
                    <Select v-model="item.icon" :disabled="!form.sections_config.event_notes.enabled">
                      <SelectTrigger :id="`event-note-icon-${index}`">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem v-for="option in noteIconOptions" :key="option.value" :value="option.value">
                          {{ option.label }}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div class="grid gap-2">
                    <Label :for="`event-note-title-${index}`">Title</Label>
                    <Input
                      :id="`event-note-title-${index}`"
                      v-model="item.title"
                      maxlength="100"
                      :disabled="!form.sections_config.event_notes.enabled"
                    />
                  </div>
                  <div class="grid gap-2">
                    <Label :for="`event-note-body-${index}`">Details</Label>
                    <Textarea
                      :id="`event-note-body-${index}`"
                      v-model="item.body"
                      rows="3"
                      maxlength="800"
                      :disabled="!form.sections_config.event_notes.enabled"
                    />
                  </div>
                  <div class="flex items-center justify-end gap-1">
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      :disabled="index === 0"
                      :aria-label="`Move ${item.title || 'note'} up`"
                      @click="moveEventNote(index, -1)"
                    >
                      <ArrowUp class="h-4 w-4" aria-hidden="true" />
                    </Button>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      :disabled="index === form.sections_config.event_notes.items.length - 1"
                      :aria-label="`Move ${item.title || 'note'} down`"
                      @click="moveEventNote(index, 1)"
                    >
                      <ArrowDown class="h-4 w-4" aria-hidden="true" />
                    </Button>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      :aria-label="`Remove ${item.title || 'note'}`"
                      @click="form.sections_config.event_notes.items.splice(index, 1)"
                    >
                      <Trash2 class="h-4 w-4 text-destructive" aria-hidden="true" />
                    </Button>
                  </div>
                </article>
              </div>
              <div v-else class="rounded-xl border border-dashed px-5 py-8 text-center">
                <Info class="mx-auto h-6 w-6 text-muted-foreground" aria-hidden="true" />
                <p class="mt-3 font-semibold">No practical notes yet</p>
                <p class="mt-1 text-sm text-muted-foreground">Add only the details guests need before they arrive.</p>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="welcome" class="m-0 space-y-8 p-5">
            <section class="space-y-4">
              <div class="flex items-start justify-between gap-5">
                <div>
                  <h3 class="font-bold">Welcome popup</h3>
                  <p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">Introduce the event before the page opens. The popup also provides the browser-approved action that can start background music.</p>
                </div>
                <Switch v-model:checked="form.popup_enabled" aria-label="Show welcome popup" />
              </div>
              <div v-if="form.popup_enabled" class="grid gap-4 sm:grid-cols-2">
                <div class="grid gap-2 sm:col-span-2">
                  <Label for="popup-title">Popup title</Label>
                  <Input id="popup-title" v-model="form.popup_title" maxlength="120" placeholder="Welcome to our celebration" />
                </div>
                <div class="grid gap-2 sm:col-span-2">
                  <Label for="popup-message">Message</Label>
                  <Textarea id="popup-message" v-model="form.popup_message" rows="4" maxlength="500" placeholder="A short note before guests enter the event page" />
                </div>
                <div class="grid gap-2 sm:max-w-sm">
                  <Label for="popup-button">Button label</Label>
                  <Input id="popup-button" v-model="form.popup_button_label" maxlength="50" placeholder="Enter event" />
                </div>
                <div class="flex items-end sm:justify-end">
                  <Button type="button" variant="outline" @click="goToMediaSlot('popup')">
                    <ImagePlus class="h-4 w-4" aria-hidden="true" />
                    Manage popup image
                  </Button>
                </div>
              </div>
            </section>

            <Separator />

            <section class="space-y-4">
              <div class="flex items-start justify-between gap-5">
                <div>
                  <h3 class="font-bold">Background music</h3>
                  <p class="mt-1 max-w-xl text-sm leading-6 text-muted-foreground">Use one short, licensed track. Playback begins only after a guest chooses to enter or presses the sound control.</p>
                </div>
                <Switch v-model:checked="form.music_enabled" :disabled="!form.background_music_url" aria-label="Enable background music" />
              </div>

              <div v-if="form.background_music_url" class="flex flex-col gap-4 border-y py-4 sm:flex-row sm:items-end sm:justify-between">
                <div class="min-w-0">
                  <p class="font-semibold">{{ form.background_music_title || 'Event soundtrack' }}</p>
                  <p class="mt-1 truncate text-xs text-muted-foreground">Audio is uploaded and ready for the public page.</p>
                </div>
                <Button type="button" variant="outline" class="shrink-0 text-destructive" @click="removeMusic">
                  <Trash2 class="h-4 w-4" aria-hidden="true" />
                  Remove audio
                </Button>
              </div>

              <div class="grid gap-4 rounded-xl border bg-muted/20 p-4 sm:grid-cols-[minmax(0,1fr)_14rem_auto] sm:items-end">
                <div class="grid gap-2">
                  <Label for="event-music">{{ form.background_music_url ? 'Replace audio' : 'Audio file' }}</Label>
                  <Input :key="musicInputKey" id="event-music" type="file" accept="audio/mpeg,audio/mp4,audio/ogg,audio/wav,audio/webm" @change="selectMusic" />
                  <p class="text-xs text-muted-foreground">MP3, M4A, OGG, WAV, or WebM up to 15 MB.</p>
                </div>
                <div class="grid gap-2">
                  <Label for="music-title">Track title</Label>
                  <Input id="music-title" v-model="form.background_music_title" maxlength="120" placeholder="Our song" />
                </div>
                <Button type="button" :disabled="!musicFile || savingMusic" @click="uploadMusic">
                  <Loader2 v-if="savingMusic" class="h-4 w-4 animate-spin" aria-hidden="true" />
                  <Upload v-else class="h-4 w-4" aria-hidden="true" />
                  Upload audio
                </Button>
              </div>

              <div class="grid gap-2 sm:max-w-sm">
                <Label for="music-volume">Starting volume: {{ form.music_volume }}%</Label>
                <Input id="music-volume" v-model.number="form.music_volume" type="range" min="0" max="100" step="5" />
                <p class="text-xs text-muted-foreground">Guests can pause or resume the track at any time.</p>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="schedule" class="m-0 space-y-8 p-5">
            <section>
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="font-bold">Main participants</h3>
                  <p class="mt-1 text-sm text-muted-foreground">Add the couple or other people at the center of the occasion.</p>
                </div>
                <Button type="button" size="sm" variant="outline" @click="addParticipant">
                  <Plus class="h-4 w-4" aria-hidden="true" />
                  Add person
                </Button>
              </div>
              <div class="mt-4 space-y-3">
                <div v-for="(person, index) in form.participants" :key="person.key" class="grid gap-3 rounded-xl border p-4 sm:grid-cols-2">
                  <div v-if="form.event_type === 'wedding'" class="grid gap-4 sm:col-span-2 md:grid-cols-[7rem_minmax(0,1fr)] md:items-end">
                    <div class="aspect-square overflow-hidden rounded-xl border bg-muted">
                      <img v-if="participantImageFor(person)" :src="participantImageFor(person).image_url" :alt="participantImageFor(person).alt_text" class="h-full w-full object-cover" />
                      <div v-else class="grid h-full place-items-center text-muted-foreground">
                        <UserRound class="h-7 w-7" aria-hidden="true" />
                      </div>
                    </div>
                    <div class="grid gap-2">
                      <Label :for="`person-upload-${index}`">{{ participantImageFor(person) ? 'Replace portrait' : 'Upload portrait' }}</Label>
                      <div class="flex min-w-0 items-center gap-2">
                        <Input
                          :key="inlineUploadVersion('participant', person.key)"
                          :id="`person-upload-${index}`"
                          class="min-w-0 flex-1"
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          @change="selectInlineUpload('participant', person.key, $event)"
                        />
                        <Button
                          type="button"
                          class="h-10 shrink-0"
                          :disabled="!inlineUploadFile('participant', person.key) || inlineUploadState === inlineUploadId('participant', person.key)"
                          @click="uploadInlineMedia('participant', person)"
                        >
                          <Loader2 v-if="inlineUploadState === inlineUploadId('participant', person.key)" class="h-4 w-4 animate-spin" aria-hidden="true" />
                          <Upload v-else class="h-4 w-4" aria-hidden="true" />
                          {{ participantImageFor(person) ? 'Replace' : 'Upload' }}
                        </Button>
                      </div>
                      <p class="text-xs leading-5 text-muted-foreground">Portraits are managed directly on each person and remain separate from the public gallery.</p>
                    </div>
                  </div>
                  <div class="grid gap-2"><Label :for="`person-name-${index}`">Name</Label><Input :id="`person-name-${index}`" v-model="person.name" /></div>
                  <div class="grid gap-2"><Label :for="`person-role-${index}`">Role or label</Label><Input :id="`person-role-${index}`" v-model="person.role" placeholder="Partner" /></div>
                  <div class="grid gap-2"><Label :for="`person-subtitle-${index}`">Short subtitle</Label><Input :id="`person-subtitle-${index}`" v-model="person.subtitle" placeholder="Daughter of" /></div>
                  <div class="grid gap-2"><Label :for="`person-family-${index}`">Family or supporting text</Label><Input :id="`person-family-${index}`" v-model="person.family_text" /></div>
                  <div class="sm:col-span-2 flex justify-end">
                    <Button type="button" size="sm" variant="ghost" class="text-destructive" @click="removeParticipant(index)">
                      <Trash2 class="h-4 w-4" aria-hidden="true" />
                      Remove
                    </Button>
                  </div>
                </div>
                <p v-if="!form.participants.length" class="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">No participants added yet.</p>
              </div>
            </section>

            <Separator />

            <section>
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="font-bold">Event schedule</h3>
                  <p class="mt-1 text-sm text-muted-foreground">Add the ceremony, reception, dinner, or any other ordered moment.</p>
                </div>
                <Button type="button" size="sm" variant="outline" @click="addSchedule">
                  <Plus class="h-4 w-4" aria-hidden="true" />
                  Add schedule
                </Button>
              </div>
              <div class="mt-4 space-y-4">
                <div v-for="(entry, index) in form.schedule_entries" :key="entry.key" class="space-y-4 rounded-xl border p-4">
                  <div class="flex items-center justify-between gap-3">
                    <p class="font-semibold">Schedule {{ index + 1 }}</p>
                    <Button type="button" size="icon" variant="ghost" :aria-label="`Remove schedule ${index + 1}`" @click="removeSchedule(index)">
                      <Trash2 class="h-4 w-4 text-destructive" aria-hidden="true" />
                    </Button>
                  </div>
                  <div class="grid gap-3 sm:grid-cols-2">
                    <div class="grid gap-2"><Label :for="`schedule-title-${index}`">Title</Label><Input :id="`schedule-title-${index}`" v-model="entry.title" placeholder="Ceremony" /></div>
                    <div class="grid gap-2"><Label :for="`schedule-venue-${index}`">Venue</Label><Input :id="`schedule-venue-${index}`" v-model="entry.venue_name" /></div>
                    <div class="grid gap-2"><Label :for="`schedule-start-${index}`">Starts</Label><Input :id="`schedule-start-${index}`" v-model="entry.starts_at" type="datetime-local" /></div>
                    <div class="grid gap-2"><Label :for="`schedule-end-${index}`">Ends</Label><Input :id="`schedule-end-${index}`" v-model="entry.ends_at" type="datetime-local" /></div>
                    <div class="grid gap-2 sm:col-span-2">
                      <Label :for="`schedule-address-${index}`">Address and map pin</Label>
                      <MapboxAddressPicker
                        :id="`schedule-address-${index}`"
                        v-model="entry.address"
                        :latitude="entry.latitude"
                        :longitude="entry.longitude"
                        :venue-name="entry.venue_name"
                        @selected="setScheduleLocation(entry, $event)"
                      />
                    </div>
                  </div>
                </div>
                <p v-if="!form.schedule_entries.length" class="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">No schedule entries yet. The main event date will be used as a fallback.</p>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="story" class="m-0 space-y-8 p-5">
            <section>
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="font-bold">Our story</h3>
                  <p class="mt-1 text-sm text-muted-foreground">Each block becomes a large editorial passage between photographs.</p>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <Button type="button" size="sm" variant="outline" @click="addStoryBlock">
                    <Plus class="h-4 w-4" aria-hidden="true" />
                    Add passage
                  </Button>
                </div>
              </div>
              <div class="mt-4 space-y-4">
                <div v-for="(block, index) in form.story_blocks" :key="block.key" class="space-y-3 rounded-xl border p-4">
                  <div class="grid gap-3 sm:grid-cols-[1fr_12rem_auto] sm:items-end">
                    <div class="grid gap-2"><Label :for="`story-title-${index}`">Title</Label><Input :id="`story-title-${index}`" v-model="block.title" placeholder="How we met" /></div>
                    <div class="grid gap-2"><Label :for="`story-date-${index}`">Date label</Label><Input :id="`story-date-${index}`" v-model="block.date_label" placeholder="June 2022" /></div>
                    <div class="flex items-center justify-end gap-1">
                      <Button type="button" size="icon" variant="ghost" :disabled="index === 0" :aria-label="`Move story passage ${index + 1} earlier`" @click="moveStoryBlock(index, -1)">
                        <ArrowUp class="h-4 w-4" aria-hidden="true" />
                      </Button>
                      <Button type="button" size="icon" variant="ghost" :disabled="index === form.story_blocks.length - 1" :aria-label="`Move story passage ${index + 1} later`" @click="moveStoryBlock(index, 1)">
                        <ArrowDown class="h-4 w-4" aria-hidden="true" />
                      </Button>
                      <Button type="button" size="icon" variant="ghost" :aria-label="`Remove story passage ${index + 1}`" @click="removeStoryBlock(index)">
                        <Trash2 class="h-4 w-4 text-destructive" aria-hidden="true" />
                      </Button>
                    </div>
                  </div>
                  <div class="grid gap-2"><Label :for="`story-body-${index}`">Story</Label><Textarea :id="`story-body-${index}`" v-model="block.body" rows="5" /></div>
                  <div class="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_8rem] lg:items-end">
                    <div class="grid gap-2">
                      <Label :for="`story-image-${index}`">Choose an existing story image</Label>
                      <Select v-model="block.image_public_id">
                        <SelectTrigger :id="`story-image-${index}`">
                          <SelectValue placeholder="Choose an uploaded story image" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">No image</SelectItem>
                          <SelectItem v-for="image in storyMediaOptions" :key="image.public_id" :value="image.public_id">
                            {{ image.alt_text }}
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div class="grid gap-2">
                      <Label :for="`story-upload-${index}`">Upload a new story image</Label>
                      <div class="flex min-w-0 items-center gap-2">
                        <Input
                          :key="inlineUploadVersion('story', block.key)"
                          :id="`story-upload-${index}`"
                          class="min-w-0 flex-1"
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          @change="selectInlineUpload('story', block.key, $event)"
                        />
                        <Button
                          type="button"
                          class="h-10 shrink-0"
                          :disabled="!inlineUploadFile('story', block.key) || inlineUploadState === inlineUploadId('story', block.key)"
                          @click="uploadInlineMedia('story', block)"
                        >
                          <Loader2 v-if="inlineUploadState === inlineUploadId('story', block.key)" class="h-4 w-4 animate-spin" aria-hidden="true" />
                          <Upload v-else class="h-4 w-4" aria-hidden="true" />
                          Upload
                        </Button>
                      </div>
                    </div>
                    <div v-if="storyImageFor(block)" class="aspect-[4/3] overflow-hidden rounded-xl border bg-muted">
                      <img :src="storyImageFor(block).image_url" :alt="storyImageFor(block).alt_text" class="h-full w-full object-cover" />
                    </div>
                  </div>
                </div>
                <p v-if="!form.story_blocks.length" class="rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground">No story passages yet.</p>
              </div>
            </section>

            <Separator />

            <section class="space-y-4">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h3 class="font-bold">Quote or reading</h3>
                  <p class="mt-1 text-sm text-muted-foreground">Use this for a scripture, poem excerpt, or meaningful passage.</p>
                </div>
                <Switch v-model:checked="form.quote.is_enabled" aria-label="Show quote section" />
              </div>
              <div v-if="form.quote.is_enabled" class="grid gap-4">
                <div class="grid gap-2"><Label for="quote-original">Original text</Label><Textarea id="quote-original" v-model="form.quote.original_text" rows="4" /></div>
                <div class="grid gap-2"><Label for="quote-translation">Translation or explanation</Label><Textarea id="quote-translation" v-model="form.quote.translation" rows="4" /></div>
                <div class="grid gap-2"><Label for="quote-citation">Citation</Label><Input id="quote-citation" v-model="form.quote.citation" /></div>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="gallery" class="m-0 space-y-6 p-5">
            <section>
              <h3 class="font-bold">Page image slots</h3>
              <p class="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
                Hero, welcome popup, and closing each use one image. Uploading to an occupied slot replaces only that slot.
              </p>
              <div class="mt-4 grid gap-4 md:grid-cols-3">
                <article v-for="slot in singleMediaSlots" :key="slot.value" class="overflow-hidden rounded-xl border bg-background">
                  <div class="aspect-[16/10] bg-muted">
                    <img v-if="slot.image" :src="slot.image.image_url" :alt="slot.image.alt_text" class="h-full w-full object-cover" />
                    <div v-else class="grid h-full place-items-center text-muted-foreground">
                      <Images class="h-7 w-7" aria-hidden="true" />
                    </div>
                  </div>
                  <div class="flex items-start justify-between gap-3 p-4">
                    <div>
                      <p class="font-semibold">{{ slot.label }}</p>
                      <p class="mt-1 text-xs leading-5 text-muted-foreground">{{ slot.detail }}</p>
                    </div>
                    <Button type="button" size="sm" variant="outline" class="shrink-0" @click="prepareMediaSlot(slot.value)">
                      {{ slot.image ? 'Replace' : 'Add' }}
                    </Button>
                  </div>
                </article>
              </div>
            </section>

            <div class="rounded-xl border bg-muted/20 p-4">
              <div class="mb-4">
                <h3 class="font-bold">Upload an event image</h3>
                <p class="mt-1 text-sm leading-6 text-muted-foreground">
                  Story and gallery libraries keep multiple images. Participant portraits are uploaded directly in the People tab.
                </p>
              </div>
              <div class="grid gap-4 sm:grid-cols-[minmax(0,1fr)_10rem_8rem_auto] sm:items-end">
                <div class="grid gap-2">
                  <Label for="event-media">Event photograph</Label>
                  <Input :key="mediaInputKey" id="event-media" type="file" accept="image/jpeg,image/png,image/webp" @change="selectMedia" />
                </div>
                <div class="grid gap-2">
                  <Label>Destination</Label>
                  <Select v-if="!isSingleMediaPlacement(mediaForm.placement)" v-model="mediaForm.placement">
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="story">Story image library</SelectItem>
                      <SelectItem value="gallery">Public gallery</SelectItem>
                    </SelectContent>
                  </Select>
                  <div v-else class="flex h-10 items-center justify-between gap-2 rounded-md border bg-background px-3">
                    <span class="truncate text-sm font-medium">{{ activeSingleMediaSlot?.label }}</span>
                    <Button type="button" size="sm" variant="ghost" class="h-7 px-2" @click="useMediaLibrary">
                      Change
                    </Button>
                  </div>
                </div>
                <div class="grid gap-2">
                  <Label for="media-order">Order</Label>
                  <Input id="media-order" v-model.number="mediaForm.sort_order" type="number" min="0" />
                </div>
                <Button type="button" :disabled="!mediaForm.image || savingMedia" @click="uploadMedia">
                  <Loader2 v-if="savingMedia" class="h-4 w-4 animate-spin" aria-hidden="true" />
                  <Upload v-else class="h-4 w-4" aria-hidden="true" />
                  Upload
                </Button>
              </div>
              <div class="mt-4 grid gap-2">
                <Label for="media-alt">Alternative text</Label>
                <Input id="media-alt" v-model="mediaForm.alt_text" placeholder="Describe the people and setting in this photograph" />
              </div>
            </div>

            <div v-if="form.media.length" class="grid gap-4 sm:grid-cols-2">
              <article v-for="(item, index) in form.media" :key="item.public_id" class="group overflow-hidden rounded-xl border bg-background">
                <div class="relative aspect-[4/3] overflow-hidden bg-slate-950">
                  <img :src="item.image_url" :alt="item.alt_text" class="h-full w-full object-cover grayscale transition duration-500 group-hover:grayscale-0" />
                  <Badge class="absolute left-3 top-3 bg-black/70 text-white hover:bg-black/70">{{ item.placement }}</Badge>
                  <Badge v-if="item.is_featured" class="absolute right-3 top-3 bg-white text-black hover:bg-white">Featured</Badge>
                </div>
                <div class="flex items-start justify-between gap-3 p-4">
                  <div><p class="font-semibold">{{ item.alt_text }}</p><p class="mt-1 text-xs text-muted-foreground">Position {{ item.sort_order }}</p></div>
                  <div class="flex shrink-0 gap-1">
                    <Button type="button" size="icon" variant="ghost" :disabled="index === 0" :aria-label="`Move ${item.alt_text} earlier`" @click="moveMedia(index, -1)"><ArrowUp class="h-4 w-4" aria-hidden="true" /></Button>
                    <Button type="button" size="icon" variant="ghost" :disabled="index === form.media.length - 1" :aria-label="`Move ${item.alt_text} later`" @click="moveMedia(index, 1)"><ArrowDown class="h-4 w-4" aria-hidden="true" /></Button>
                    <Button v-if="!isSingleMediaPlacement(item.placement) && !item.is_featured" type="button" size="icon" variant="ghost" :aria-label="`Feature ${item.alt_text}`" @click="featureMedia(item)"><Star class="h-4 w-4" aria-hidden="true" /></Button>
                    <Button type="button" size="icon" variant="ghost" :aria-label="`Remove ${item.alt_text}`" @click="removeMedia(item)"><Trash2 class="h-4 w-4 text-destructive" aria-hidden="true" /></Button>
                  </div>
                </div>
              </article>
            </div>
            <p v-else class="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">No event photographs uploaded yet. The event thumbnail is used as the hero fallback.</p>
          </TabsContent>

          <TabsContent value="theme" class="m-0 space-y-6 p-5">
            <div class="grid gap-4 sm:grid-cols-3">
              <div v-for="color in colorFields" :key="color.key" class="grid gap-2">
                <Label :for="`theme-${color.key}`">{{ color.label }}</Label>
                <div class="flex gap-2">
                  <Input :id="`theme-${color.key}`" v-model="form[color.key]" class="font-mono uppercase" maxlength="7" />
                  <Input v-model="form[color.key]" class="h-10 w-12 shrink-0 p-1" type="color" :aria-label="`${color.label} picker`" />
                </div>
              </div>
            </div>
            <div class="grid gap-4 sm:grid-cols-2">
              <div class="grid gap-2">
                <Label>Display font</Label>
                <Select v-model="form.heading_font"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="font in headingFonts" :key="font" :value="font">{{ font }}</SelectItem></SelectContent></Select>
              </div>
              <div class="grid gap-2">
                <Label>Body font</Label>
                <Select v-model="form.body_font"><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem v-for="font in bodyFonts" :key="font" :value="font">{{ font }}</SelectItem></SelectContent></Select>
              </div>
            </div>
            <div class="overflow-hidden rounded-xl border" :style="themePreviewStyle">
              <div class="min-h-64 p-8 sm:p-12">
                <p class="text-sm opacity-70" :style="{ fontFamily: bodyFontStack }">A private invitation</p>
                <p class="mt-6 max-w-xl text-5xl leading-none" :style="{ fontFamily: headingFontStack }">{{ participantNames || form.title }}</p>
                <p class="mt-8 max-w-lg leading-7 opacity-75" :style="{ fontFamily: bodyFontStack }">{{ form.invitation_text }}</p>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <div class="flex flex-col gap-3 border-t bg-muted/15 p-5 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-xs leading-5 text-muted-foreground">Changes affect the public event page and every personalized invitation.</p>
          <Button type="button" :disabled="saving" @click="saveWebsite">
            <Loader2 v-if="saving" class="h-4 w-4 animate-spin" aria-hidden="true" />
            <Save v-else class="h-4 w-4" aria-hidden="true" />
            Save website
          </Button>
        </div>
      </CardContent>
    </Card>

    <aside class="space-y-4 xl:sticky xl:top-4 xl:h-fit">
      <Card>
        <CardHeader class="p-5">
          <CardTitle class="text-base">Website identity</CardTitle>
          <CardDescription>{{ eventTypeLabel(form.event_type) }} · {{ selectedTemplate.label }}</CardDescription>
        </CardHeader>
        <CardContent class="p-5 pt-0">
          <div class="overflow-hidden rounded-xl border" :style="themePreviewStyle">
            <div class="aspect-[4/3] p-5">
              <p class="text-xs opacity-65">{{ selectedTemplate.label }}</p>
              <p class="mt-12 text-3xl leading-none" :style="{ fontFamily: headingFontStack }">{{ participantNames || form.title || 'Your event' }}</p>
            </div>
          </div>
          <p class="mt-3 text-xs leading-5 text-muted-foreground">{{ selectedTemplate.description }}</p>
          <div class="mt-4 space-y-2 border-t pt-4 text-xs text-muted-foreground">
            <p class="flex items-center justify-between gap-3"><span>Welcome popup</span><span class="font-medium text-foreground">{{ form.popup_enabled ? 'On' : 'Off' }}</span></p>
            <p class="flex items-center justify-between gap-3"><span>Background music</span><span class="font-medium text-foreground">{{ form.music_enabled && form.background_music_url ? 'On' : 'Off' }}</span></p>
          </div>
        </CardContent>
      </Card>
      <Alert>
        <ShieldCheck class="h-4 w-4" aria-hidden="true" />
        <AlertTitle>Guest privacy stays intact</AlertTitle>
        <AlertDescription>The public page never exposes the guest list. RSVP updates remain tied to each invitation token.</AlertDescription>
      </Alert>
    </aside>
  </div>
</template>

<script setup>
import {
  ArrowDown,
  ArrowUp,
  BookOpenText,
  CalendarDays,
  ExternalLink,
  Heart,
  ImagePlus,
  Images,
  Info,
  LetterText,
  Loader2,
  Palette,
  PanelsTopLeft,
  Plus,
  Save,
  ShieldCheck,
  Shirt,
  Star,
  Trash2,
  TimerReset,
  Upload,
  UserRound,
  Volume2,
} from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ButtonAnchor } from '@/components/ui/button-anchor'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import MapboxAddressPicker from '@/components/scheduling/MapboxAddressPicker.vue'
import {
  eventTemplate,
  eventTypeLabel,
  eventTypeOptions,
  templatesForEventType,
} from '@/utils/eventTemplates'
import {
  cloneEventSectionsConfig,
  normalizeEventSectionsConfig,
} from '@/utils/eventRsvpConfig'

const props = defineProps({
  businessId: { type: String, required: true },
  eventId: { type: String, required: true },
})

const emit = defineEmits(['updated'])
const { apiFetch } = useApiClient()
const activeTab = ref('invitation')
const loading = ref(true)
const saving = ref(false)
const savingMedia = ref(false)
const savingMusic = ref(false)
const musicFile = ref(null)
const musicInputKey = ref(0)
const mediaInputKey = ref(0)
const inlineUploadState = ref('')
const inlineUploadFiles = reactive({})
const inlineUploadVersions = reactive({})
const singleMediaPlacements = ['hero', 'popup', 'closing']
const headingFonts = ['Bodoni Moda', 'Cormorant Garamond', 'Newsreader', 'Italiana']
const bodyFonts = ['Manrope', 'Newsreader']
const sectionOptions = [
  { value: 'event_detail', label: 'Event details', detail: 'Schedule and venue information' },
  { value: 'participants', label: 'Participants', detail: 'Names and family introductions' },
  { value: 'story', label: 'Story', detail: 'Editorial story passages' },
  { value: 'quote', label: 'Quote', detail: 'Optional reading or scripture' },
  { value: 'wish', label: 'Guest wishes', detail: 'Approved messages shown on the landing page' },
  { value: 'gallery', label: 'Gallery & closing', detail: 'A photographic collection and final image' },
]
const colorFields = [
  { key: 'theme_background', label: 'Background' },
  { key: 'theme_text', label: 'Text' },
  { key: 'theme_accent', label: 'Accent' },
]

const form = reactive({
  title: '',
  event_type: 'wedding',
  website_enabled: false,
  website_template: 'wedding_editorial',
  invitation_text: 'You are invited to celebrate with us.',
  closing_message: 'With love',
  hero_date_text: '',
  header_mark_type: 'text',
  header_mark_text: '',
  countdown_enabled: false,
  countdown_label: 'Until we celebrate',
  wish_display_mode: 'realtime',
  theme_background: '#000000',
  theme_text: '#F5F3EE',
  theme_accent: '#D6D1C8',
  heading_font: 'Bodoni Moda',
  body_font: 'Manrope',
  sections_config: normalizeEventSectionsConfig(),
  participants: [],
  schedule_entries: [],
  story_blocks: [],
  quote: { is_enabled: false, original_text: '', translation: '', citation: '' },
  popup_enabled: false,
  popup_title: '',
  popup_message: '',
  popup_button_label: 'Enter event',
  music_enabled: false,
  background_music_url: '',
  background_music_title: '',
  music_volume: 35,
  media: [],
})
const mediaForm = reactive({ image: null, placement: 'gallery', alt_text: '', sort_order: 0 })

const endpoint = computed(() => `businesses/${props.businessId}/venue-events/${props.eventId}/website/`)
const musicEndpoint = computed(() => `${endpoint.value}music/`)
const previewUrl = computed(() => `/event/${props.eventId}`)
const availableTemplates = computed(() => templatesForEventType(form.event_type))
const selectedTemplate = computed(() => eventTemplate(form.website_template))
const participantNames = computed(() => form.participants.map(item => item.name).filter(Boolean).join(' & '))
const dressCodeMedia = computed({
  get: () => form.sections_config.dress_code.media_public_id || 'none',
  set: value => {
    form.sections_config.dress_code.media_public_id = value === 'none' ? null : value
  },
})
const storyMediaOptions = computed(() => form.media.filter(item => item.placement === 'story'))
const singleMediaSlots = computed(() => [
  {
    value: 'hero',
    label: 'Hero image',
    detail: 'The single opening image for the page.',
    image: form.media.find(item => item.placement === 'hero') || null,
  },
  {
    value: 'popup',
    label: 'Welcome popup',
    detail: 'Shown before guests enter the experience.',
    image: form.media.find(item => item.placement === 'popup') || null,
  },
  {
    value: 'closing',
    label: 'Closing image',
    detail: 'The final photograph before the footer.',
    image: form.media.find(item => item.placement === 'closing') || null,
  },
])
const activeSingleMediaSlot = computed(() => (
  singleMediaSlots.value.find(slot => slot.value === mediaForm.placement) || null
))
const headingFontStack = computed(() => `'${form.heading_font}', Georgia, serif`)
const bodyFontStack = computed(() => `'${form.body_font}', Arial, sans-serif`)
const themePreviewStyle = computed(() => ({
  backgroundColor: form.theme_background,
  color: form.theme_text,
  borderColor: form.theme_accent,
}))

const noteIconOptions = [
  { value: 'info', label: 'Information' },
  { value: 'calendar', label: 'Schedule' },
  { value: 'car', label: 'Parking or travel' },
  { value: 'gift', label: 'Gifts' },
  { value: 'heart', label: 'Celebration' },
  { value: 'hotel', label: 'Accommodation' },
  { value: 'sparkles', label: 'Special detail' },
  { value: 'utensils', label: 'Food and drinks' },
]

onMounted(loadWebsite)

async function loadWebsite() {
  loading.value = true
  try {
    const response = await apiFetch(endpoint.value)
    assignResponse(response)
  } catch (error) {
    failedToast(error, 'The event website settings could not be loaded.')
  } finally {
    loading.value = false
  }
}

function assignResponse(response) {
  const eventType = response.event_type || 'general'
  const compatibleTemplates = templatesForEventType(eventType)
  const websiteTemplate = compatibleTemplates.some(template => template.value === response.website_template)
    ? response.website_template
    : compatibleTemplates[0].value
  const sectionsConfig = normalizeEventSectionsConfig(response.sections_config)
  sectionsConfig.event_notes.items = sectionsConfig.event_notes.items.map(withKey)
  Object.assign(form, {
    ...response,
    event_type: eventType,
    website_template: websiteTemplate,
    wish_display_mode: response.wish_display_mode || 'realtime',
    sections_config: sectionsConfig,
    participants: (response.participants || []).map(item => withKey({
      ...item,
      image_public_id: item.image_public_id || 'none',
    })),
    schedule_entries: (response.schedule_entries || []).map(entry => ({ ...entry, key: crypto.randomUUID(), starts_at: localDateTime(entry.starts_at), ends_at: localDateTime(entry.ends_at) })),
    story_blocks: (response.story_blocks || []).map(item => withKey({
      ...item,
      image_public_id: item.image_public_id || 'none',
    })),
    quote: response.quote || { is_enabled: false, original_text: '', translation: '', citation: '' },
    media: response.media || [],
  })
}

function changeEventType(value) {
  form.event_type = value
  selectTemplate(templatesForEventType(value)[0])
}

function selectTemplate(template) {
  form.website_template = template.value
  Object.assign(form, template.preset)
}

function templatePreviewStyle(template) {
  return {
    backgroundColor: template.preset.theme_background,
    color: template.preset.theme_text,
    borderColor: template.preset.theme_accent,
  }
}

function withKey(item) {
  return { ...item, key: crypto.randomUUID() }
}

function addDressColor() {
  if (form.sections_config.dress_code.colors.length >= 8) return
  form.sections_config.dress_code.colors.push('#D7C7A3')
}

function updateDressColor(index, value) {
  form.sections_config.dress_code.colors[index] = String(value || '').toUpperCase()
}

function addEventNote() {
  if (form.sections_config.event_notes.items.length >= 8) return
  form.sections_config.event_notes.items.push(withKey({
    icon: 'info',
    title: '',
    body: '',
  }))
}

function moveEventNote(index, direction) {
  const target = index + direction
  if (target < 0 || target >= form.sections_config.event_notes.items.length) return
  const [item] = form.sections_config.event_notes.items.splice(index, 1)
  form.sections_config.event_notes.items.splice(target, 0, item)
}

function addParticipant() {
  form.participants.push(withKey({ name: '', role: 'Partner', subtitle: '', family_text: '', image_public_id: 'none', sort_order: form.participants.length }))
}

function removeParticipant(index) {
  form.participants.splice(index, 1)
}

function addSchedule() {
  form.schedule_entries.push(withKey({ title: '', starts_at: '', ends_at: '', end_time_label: '', venue_name: '', address: '', latitude: null, longitude: null, map_url: '', sort_order: form.schedule_entries.length }))
}

function removeSchedule(index) {
  form.schedule_entries.splice(index, 1)
}

function setScheduleLocation(entry, location) {
  Object.assign(entry, {
    address: location.address,
    latitude: location.latitude,
    longitude: location.longitude,
    map_url: location.mapUrl,
  })
}

function addStoryBlock() {
  form.story_blocks.push(withKey({
    title: '',
    body: '',
    date_label: '',
    image_public_id: 'none',
    sort_order: form.story_blocks.length,
  }))
}

function removeStoryBlock(index) {
  form.story_blocks.splice(index, 1)
}

function moveStoryBlock(index, direction) {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= form.story_blocks.length) return
  const [block] = form.story_blocks.splice(index, 1)
  form.story_blocks.splice(targetIndex, 0, block)
}

async function saveWebsite() {
  saving.value = true
  try {
    const sectionsConfig = cloneEventSectionsConfig(form.sections_config)
    delete sectionsConfig.dress_code.media_url
    const payload = {
      title: form.title,
      event_type: form.event_type,
      website_enabled: form.website_enabled,
      website_template: form.website_template,
      invitation_text: form.invitation_text,
      closing_message: form.closing_message,
      hero_date_text: form.hero_date_text,
      header_mark_type: form.header_mark_type,
      header_mark_text: form.header_mark_text,
      countdown_enabled: form.countdown_enabled,
      countdown_label: form.countdown_label,
      wish_display_mode: form.wish_display_mode,
      theme_background: form.theme_background,
      theme_text: form.theme_text,
      theme_accent: form.theme_accent,
      heading_font: form.heading_font,
      body_font: form.body_font,
      sections_config: sectionsConfig,
      popup_enabled: form.popup_enabled,
      popup_title: form.popup_title,
      popup_message: form.popup_message,
      popup_button_label: form.popup_button_label,
      music_enabled: form.music_enabled,
      background_music_title: form.background_music_title,
      music_volume: Number(form.music_volume),
      participants: form.participants.map((item, index) => ({
        ...withoutKey(item),
        image_public_id: item.image_public_id === 'none' ? null : item.image_public_id,
        sort_order: index,
      })),
      schedule_entries: form.schedule_entries.map((item, index) => ({
        ...withoutKey(item),
        starts_at: new Date(item.starts_at).toISOString(),
        ends_at: item.ends_at ? new Date(item.ends_at).toISOString() : null,
        sort_order: index,
      })),
      story_blocks: form.story_blocks.map((item, index) => ({
        ...withoutKey(item),
        image_public_id: item.image_public_id === 'none' ? null : item.image_public_id,
        sort_order: index,
      })),
      quote: form.quote,
    }
    const response = await apiFetch(endpoint.value, { method: 'PATCH', body: payload })
    assignResponse(response)
    emit('updated', response)
    toast({ title: form.website_enabled ? 'Event website published' : 'Event website saved as draft', description: 'The invitation content and styling are up to date.' })
  } catch (error) {
    failedToast(error, 'Review the event website fields and try again.')
  } finally {
    saving.value = false
  }
}

function selectMusic(event) {
  musicFile.value = event.target.files?.[0] || null
}

async function uploadMusic() {
  if (!musicFile.value) return
  savingMusic.value = true
  try {
    const body = new FormData()
    body.append('file', musicFile.value)
    body.append('title', form.background_music_title || '')
    const response = await apiFetch(musicEndpoint.value, { method: 'POST', body })
    assignResponse(response)
    musicFile.value = null
    musicInputKey.value += 1
    toast({ title: 'Background audio uploaded', description: 'Music is enabled and will begin after the guest enters the page.' })
  } catch (error) {
    failedToast(error, 'The background audio could not be uploaded.')
  } finally {
    savingMusic.value = false
  }
}

async function removeMusic() {
  try {
    await apiFetch(musicEndpoint.value, { method: 'DELETE' })
    form.background_music_url = ''
    form.background_music_title = ''
    form.music_enabled = false
    musicFile.value = null
    musicInputKey.value += 1
    toast({ title: 'Background audio removed' })
  } catch (error) {
    failedToast(error, 'The background audio could not be removed.')
  }
}

function withoutKey(item) {
  const { key, ...value } = item
  return value
}

function selectMedia(event) {
  mediaForm.image = event.target.files?.[0] || null
}

async function goToMediaSlot(placement) {
  activeTab.value = 'gallery'
  await nextTick()
  prepareMediaSlot(placement)
}

async function prepareMediaSlot(placement) {
  mediaForm.placement = placement
  mediaForm.image = null
  mediaInputKey.value += 1
  await nextTick()
  document.getElementById('event-media')?.click()
}

function useMediaLibrary() {
  mediaForm.placement = 'gallery'
  mediaForm.image = null
  mediaInputKey.value += 1
}

function isSingleMediaPlacement(placement) {
  return singleMediaPlacements.includes(placement)
}

function storyImageFor(block) {
  if (!block.image_public_id || block.image_public_id === 'none') return null
  return storyMediaOptions.value.find(item => item.public_id === block.image_public_id) || null
}

function participantImageFor(person) {
  if (!person.image_public_id || person.image_public_id === 'none') return null
  return form.media.find(item => item.public_id === person.image_public_id) || null
}

function inlineUploadId(placement, key) {
  return `${placement}:${key}`
}

function inlineUploadFile(placement, key) {
  return inlineUploadFiles[inlineUploadId(placement, key)] || null
}

function inlineUploadVersion(placement, key) {
  return inlineUploadVersions[inlineUploadId(placement, key)] || 0
}

function selectInlineUpload(placement, key, event) {
  inlineUploadFiles[inlineUploadId(placement, key)] = event.target.files?.[0] || null
}

async function uploadInlineMedia(placement, item) {
  const uploadId = inlineUploadId(placement, item.key)
  const file = inlineUploadFiles[uploadId]
  if (!file) return
  inlineUploadState.value = uploadId
  try {
    const altText = placement === 'participant'
      ? `Portrait of ${item.name || 'event participant'}`
      : `Story photograph for ${item.title || 'event story'}`
    const body = new FormData()
    body.append('image', file)
    body.append('placement', placement)
    body.append('alt_text', altText)
    body.append('sort_order', String(form.media.filter(media => media.placement === placement).length))
    body.append('is_featured', 'false')
    const created = await apiFetch(`${endpoint.value}media/`, { method: 'POST', body })
    form.media.push(created)
    item.image_public_id = created.public_id
    delete inlineUploadFiles[uploadId]
    inlineUploadVersions[uploadId] = inlineUploadVersion(placement, item.key) + 1
    toast({
      title: placement === 'participant' ? 'Portrait uploaded' : 'Story image uploaded',
      description: 'The new image is selected and will be published when you save the event website.',
    })
  } catch (error) {
    failedToast(error, placement === 'participant' ? 'The portrait could not be uploaded.' : 'The story image could not be uploaded.')
  } finally {
    inlineUploadState.value = ''
  }
}

async function uploadMedia() {
  savingMedia.value = true
  try {
    const body = new FormData()
    body.append('image', mediaForm.image)
    body.append('placement', mediaForm.placement)
    body.append('alt_text', mediaForm.alt_text || 'Event photograph')
    body.append('sort_order', String(Number(mediaForm.sort_order || 0)))
    body.append('is_featured', String(!form.media.some(item => item.placement === mediaForm.placement && item.is_featured)))
    const created = await apiFetch(`${endpoint.value}media/`, { method: 'POST', body })
    if (isSingleMediaPlacement(created.placement)) {
      form.media = form.media.filter(item => item.placement !== created.placement)
    }
    form.media.push(created)
    Object.assign(mediaForm, {
      image: null,
      placement: 'gallery',
      alt_text: '',
      sort_order: form.media.length,
    })
    mediaInputKey.value += 1
    toast({
      title: isSingleMediaPlacement(created.placement) ? `${singleMediaSlots.value.find(slot => slot.value === created.placement)?.label} updated` : 'Photograph uploaded',
      description: 'The image is now available on the public event page.',
    })
  } catch (error) {
    failedToast(error, 'The photograph could not be uploaded.')
  } finally {
    savingMedia.value = false
  }
}

async function featureMedia(item) {
  try {
    const updated = await apiFetch(`${endpoint.value}media/${item.public_id}/`, { method: 'PATCH', body: { is_featured: true } })
    form.media = form.media.map(media => media.placement === updated.placement ? { ...media, is_featured: media.public_id === updated.public_id } : media)
    toast({ title: 'Featured image updated' })
  } catch (error) {
    failedToast(error, 'The featured image could not be changed.')
  }
}

async function moveMedia(index, direction) {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= form.media.length) return
  const current = form.media[index]
  const target = form.media[targetIndex]
  try {
    await Promise.all([
      apiFetch(`${endpoint.value}media/${current.public_id}/`, { method: 'PATCH', body: { sort_order: targetIndex } }),
      apiFetch(`${endpoint.value}media/${target.public_id}/`, { method: 'PATCH', body: { sort_order: index } }),
    ])
    const reordered = [...form.media]
    reordered[index] = { ...target, sort_order: index }
    reordered[targetIndex] = { ...current, sort_order: targetIndex }
    form.media = reordered
    toast({ title: 'Gallery order updated' })
  } catch (error) {
    failedToast(error, 'The gallery order could not be changed.')
  }
}

async function removeMedia(item) {
  try {
    await apiFetch(`${endpoint.value}media/${item.public_id}/`, { method: 'DELETE' })
    form.media = form.media.filter(media => media.public_id !== item.public_id)
    toast({ title: 'Photograph removed' })
  } catch (error) {
    failedToast(error, 'The photograph could not be removed.')
  }
}

function localDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60 * 1000).toISOString().slice(0, 16)
}

function failedToast(error, fallback) {
  toast({
    title: 'Could not save event website',
    description: error?.data?.error?.message || error?.data?.detail || error?.message || fallback,
    variant: 'destructive',
  })
}
</script>
