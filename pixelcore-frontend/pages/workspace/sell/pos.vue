<template>
  <section class="workspace-page space-y-5">
    <div class="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
      <div>
        <h1 class="text-3xl font-extrabold tracking-[-0.025em]">
          Point of sale
        </h1>
        <p class="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
          Set up separate screens for checkout, customers, fulfillment, and
          delivery. Each device receives only the information its role needs.
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <Button
          v-if="!showFlowGuide"
          variant="outline"
          type="button"
          @click="restoreFlowGuide"
          ><CircleHelp class="h-4 w-4" aria-hidden="true" /> How it
          works</Button
        ><ButtonAnchor
          variant="outline"
          :href="activeSurface.path"
          target="_blank"
          rel="noopener"
          ><ExternalLink class="h-4 w-4" aria-hidden="true" /> Open
          {{ activeSurface.shortTitle }}</ButtonAnchor
        ><Button type="button" @click="openCreate"
          ><Plus class="h-4 w-4" aria-hidden="true" /> Add device</Button
        >
      </div>
    </div>

    <Alert
      ><ShieldCheck class="h-4 w-4" aria-hidden="true" /><AlertTitle
        >Role-specific screens</AlertTitle
      ><AlertDescription
        >Checkout happens at the counter. Customers see only their linked order.
        Fulfillment and delivery teams receive confirmed orders through their
        own queues.</AlertDescription
      ></Alert
    >

    <section
      v-if="showFlowGuide"
      class="relative overflow-hidden rounded-xl border bg-card p-5"
      aria-labelledby="screen-flow-title"
    >
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 id="screen-flow-title" class="font-extrabold">
            How an order moves
          </h2>
          <p class="mt-1 text-sm leading-6 text-muted-foreground">
            Each screen has one audience and receives only the information
            needed for that handoff.
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          type="button"
          aria-label="Dismiss screen guide"
          @click="dismissFlowGuide"
          ><X class="h-4 w-4" aria-hidden="true"
        /></Button>
      </div>
      <div class="relative mt-5">
        <div
          class="absolute left-[12.5%] right-[12.5%] top-5 hidden h-px bg-border md:block"
          aria-hidden="true"
        />
        <ol class="relative grid gap-4 md:grid-cols-4">
          <li
            v-for="step in flowSteps"
            :key="step.title"
            class="flex gap-3 md:block md:text-center"
          >
            <span
              class="relative z-10 grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-secondary text-primary md:mx-auto"
              ><component :is="step.icon" class="h-5 w-5" aria-hidden="true"
            /></span>
            <div class="md:mt-3">
              <strong class="block text-sm">{{ step.title }}</strong
              ><span
                class="mt-1 block text-xs leading-5 text-muted-foreground"
                >{{ step.detail }}</span
              >
            </div>
          </li>
        </ol>
      </div>
    </section>

    <div class="grid items-start gap-5 lg:grid-cols-[17rem_minmax(0,1fr)]">
      <aside
        class="overflow-hidden rounded-xl bg-[var(--brand-secondary)] text-white lg:sticky lg:top-16"
        aria-label="POS screen types"
      >
        <div class="border-b border-white/10 px-4 py-4">
          <h2 class="font-extrabold">Operational screens</h2>
          <p class="mt-1 text-xs leading-5 text-white/55">
            Choose a role to manage its devices.
          </p>
        </div>
        <nav class="space-y-1 p-2">
          <Button
            v-for="surface in surfaces"
            :key="surface.type"
            variant="ghost"
            type="button"
            class="h-auto w-full justify-start gap-3 px-3 py-3 text-left text-white/65 hover:bg-white/10 hover:text-white"
            :class="
              tab === surface.type ? '!bg-white !text-foreground shadow-sm' : ''
            "
            :aria-current="tab === surface.type ? 'page' : undefined"
            @click="tab = surface.type"
          >
            <span
              class="grid h-9 w-9 shrink-0 place-items-center rounded-lg"
              :class="
                tab === surface.type
                  ? 'bg-secondary text-primary'
                  : 'bg-white/10 text-white/70'
              "
              ><component :is="surface.icon" class="h-4 w-4" aria-hidden="true"
            /></span>
            <span class="min-w-0 flex-1"
              ><strong class="block truncate text-sm">{{
                surface.title
              }}</strong
              ><span
                class="mt-0.5 block truncate text-xs font-normal opacity-65"
                >{{ surface.audienceShort }}</span
              ></span
            >
            <span
              class="grid min-w-7 place-items-center rounded-full px-2 py-1 text-xs font-extrabold tabular-nums"
              :class="
                tab === surface.type
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-white/15 text-white'
              "
              >{{ surface.count }}</span
            >
          </Button>
        </nav>
        <div
          class="border-t border-white/10 p-4 text-xs leading-5 text-white/55"
        >
          <KeyRound
            class="mb-2 h-4 w-4 text-[var(--brand-accent)]"
            aria-hidden="true"
          />Pairing codes are single-use. Revoking a device immediately
          invalidates its saved token.
        </div>
      </aside>

      <section class="min-w-0 overflow-hidden rounded-xl border bg-card">
        <header
          class="flex flex-col justify-between gap-4 border-b p-5 sm:flex-row sm:items-start"
        >
          <div class="flex items-start gap-4">
            <div
              class="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-secondary"
            >
              <component
                :is="activeSurface.icon"
                class="h-5 w-5 text-primary"
                aria-hidden="true"
              />
            </div>
            <div>
              <h2 class="text-xl font-extrabold">{{ activeSurface.title }}</h2>
              <p class="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
                {{ activeSurface.description }}
              </p>
            </div>
          </div>
          <Button size="sm" type="button" @click="openCreate"
            ><Plus class="h-4 w-4" aria-hidden="true" /> Add
            {{ activeSurface.deviceLabel }}</Button
          >
        </header>

        <dl class="grid border-b bg-muted/25 sm:grid-cols-3">
          <div
            class="flex items-center gap-3 border-b px-5 py-4 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0"
          >
            <span
              class="grid h-9 w-9 place-items-center rounded-lg bg-background text-primary"
              ><Activity class="h-4 w-4" aria-hidden="true"
            /></span>
            <div>
              <dt class="text-xs font-semibold text-muted-foreground">
                Active devices
              </dt>
              <dd class="mt-0.5 font-extrabold tabular-nums">
                {{ activeDevices.length }}
              </dd>
            </div>
          </div>
          <div
            class="flex items-center gap-3 border-b px-5 py-4 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0"
          >
            <span
              class="grid h-9 w-9 place-items-center rounded-lg bg-background text-primary"
              ><Wifi class="h-4 w-4" aria-hidden="true"
            /></span>
            <div>
              <dt class="text-xs font-semibold text-muted-foreground">
                Connected before
              </dt>
              <dd class="mt-0.5 font-extrabold tabular-nums">
                {{ activeDevices.filter((item) => item.last_seen_at).length }}
              </dd>
            </div>
          </div>
          <div class="flex min-w-0 items-center gap-3 px-5 py-4">
            <span
              class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-background text-primary"
              ><Route class="h-4 w-4" aria-hidden="true"
            /></span>
            <div class="min-w-0">
              <dt class="text-xs font-semibold text-muted-foreground">
                Screen route
              </dt>
              <dd class="mt-0.5 truncate text-sm font-extrabold">
                {{ activeSurface.path }}
              </dd>
            </div>
          </div>
        </dl>

        <StatePanel
          v-if="loading"
          kind="loading"
          title="Loading devices"
          :message="`Retrieving ${activeSurface.title.toLowerCase()} devices and their current connection state.`"
        />
        <StatePanel
          v-else-if="error"
          kind="error"
          title="Devices unavailable"
          :message="error"
          ><Button variant="outline" type="button" @click="load"
            >Try again</Button
          ></StatePanel
        >
        <StatePanel
          v-else-if="!currentDevices.length"
          :title="`No ${activeSurface.deviceLabel}s yet`"
          :message="`Create a ${activeSurface.deviceLabel}, generate its pairing code, then open the dedicated screen on the device that will use it.`"
          ><Button class="mt-5" type="button" @click="openCreate"
            ><Plus class="h-4 w-4" aria-hidden="true" /> Add
            {{ activeSurface.deviceLabel }}</Button
          ></StatePanel
        >
        <div v-else class="divide-y">
          <article
            v-for="device in currentDevices"
            :key="device.public_id"
            class="group grid gap-4 px-5 py-4 transition-[background-color,transform] duration-200 hover:bg-secondary/45 lg:grid-cols-[minmax(12rem,.8fr)_9rem_minmax(16rem,1.3fr)_auto] lg:items-center"
          >
            <div class="flex min-w-0 items-center gap-3">
              <span
                class="h-2.5 w-2.5 shrink-0 rounded-full"
                :class="
                  device.is_active
                    ? device.last_seen_at
                      ? 'bg-emerald-500'
                      : 'bg-amber-500'
                    : 'bg-muted-foreground/35'
                "
                aria-hidden="true"
              />
              <div class="min-w-0">
                <h3 class="truncate font-extrabold">{{ device.name }}</h3>
                <p class="mt-0.5 text-xs text-muted-foreground">
                  {{
                    device.is_active
                      ? device.last_seen_at
                        ? "Connected before"
                        : "Waiting to pair"
                      : "Inactive"
                  }}
                  · {{ device.public_id.slice(0, 8) }}
                </p>
              </div>
            </div>
            <div>
              <p class="text-xs font-semibold text-muted-foreground lg:hidden">
                Location
              </p>
              <p class="mt-1 text-sm lg:mt-0">
                {{ locationName(device.location_public_id) }}
              </p>
            </div>
            <div v-if="activeSurface.type === 'customer_display'">
              <p class="text-sm font-semibold">
                {{ linkedStationName(device.public_id) }}
              </p>
              <p class="mt-1 text-xs text-muted-foreground">
                {{ contentSummary(device) }} ·
                {{ device.configuration?.ad_rotation_seconds || 10 }}s rotation
              </p>
            </div>
            <div v-else>
              <p class="text-sm leading-5 text-muted-foreground">
                {{ activeSurface.audience }}
              </p>
              <div
                v-if="activeSurface.type === 'pos'"
                class="mt-2 flex flex-wrap gap-2"
              >
                <Badge variant="outline"
                  >{{ linkedDisplays(device.public_id) }} customer display{{
                    linkedDisplays(device.public_id) === 1 ? "" : "s"
                  }}</Badge
                ><Badge
                  :variant="
                    device.configuration?.strict_mode ? 'secondary' : 'outline'
                  "
                  >{{
                    device.configuration?.strict_mode
                      ? "Strict controls"
                      : "Standard controls"
                  }}</Badge
                >
              </div>
            </div>
            <div
              class="flex justify-end transition-transform duration-200 group-hover:-translate-x-1"
            >
              <Button
                variant="outline"
                size="sm"
                type="button"
                :disabled="!device.is_active"
                @click="openManage(device)"
                ><Settings2 class="h-3.5 w-3.5" aria-hidden="true" />
                Manage</Button
              >
            </div>
          </article>
        </div>
      </section>
    </div>

    <Dialog v-model:open="createOpen"
      ><DialogContent class="sm:max-w-lg"
        ><form @submit.prevent="createDevice">
          <DialogHeader
            ><div
              class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
            >
              <component
                :is="creatingSurface.icon"
                class="h-5 w-5"
                aria-hidden="true"
              />
            </div>
            <DialogTitle>Add {{ creatingSurface.deviceLabel }}</DialogTitle
            ><DialogDescription
              >{{ creatingSurface.description }} Give this screen a recognizable
              name and optional location.</DialogDescription
            ></DialogHeader
          >
          <div class="mt-6 space-y-4">
            <label
              ><span class="field-label">Device name</span
              ><Input
                v-model.trim="deviceName"
                maxlength="120"
                :placeholder="creatingSurface.placeholder"
                required /></label
            ><label
              ><span class="field-label">Location</span
              ><NativeSelect v-model="deviceLocation"
                ><option value="">Any location</option>
                <option
                  v-for="location in locations"
                  :key="location.public_id"
                  :value="location.public_id"
                >
                  {{ location.name }}
                </option></NativeSelect
              ></label
            ><label
              v-if="creatingType === 'pos'"
              class="flex items-start justify-between gap-5 rounded-xl border bg-muted/25 p-4"
              ><span
                ><strong class="block text-sm">Strict register controls</strong
                ><span
                  class="mt-1 block text-xs leading-5 text-muted-foreground"
                  >Require an owner, admin, or manager PIN for item reductions,
                  voids, and promotions.</span
                ></span
              ><Switch
                :checked="strictDevice"
                @update:checked="strictDevice = $event"
            /></label>
          </div>
          <DialogFooter class="mt-6"
            ><Button variant="outline" type="button" @click="createOpen = false"
              >Cancel</Button
            ><Button :disabled="savingDevice">{{
              savingDevice ? "Creating…" : "Create device"
            }}</Button></DialogFooter
          >
        </form></DialogContent
      ></Dialog
    >

    <Dialog v-model:open="manageOpen"
      ><DialogContent class="max-h-[92dvh] overflow-y-auto sm:max-w-4xl"
        ><form v-if="manageTarget" @submit.prevent="saveManagedDevice">
          <DialogHeader
            ><div
              class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
            >
              <Settings2 class="h-5 w-5" aria-hidden="true" />
            </div>
            <DialogTitle>Manage {{ manageTarget.name }}</DialogTitle
            ><DialogDescription
              >Edit this screen, configure its operating controls, and pair it
              without leaving the same workspace.</DialogDescription
            ></DialogHeader
          >
          <div
            class="mt-6 grid overflow-hidden rounded-xl border lg:grid-cols-[minmax(0,1.25fr)_minmax(19rem,.75fr)]"
          >
            <div class="space-y-5 border-b p-5 lg:border-b-0 lg:border-r">
              <div class="grid gap-4 sm:grid-cols-2">
                <label
                  ><span class="field-label">Device name</span
                  ><Input
                    v-model.trim="manageForm.name"
                    maxlength="120"
                    required /></label
                ><label
                  ><span class="field-label">Location</span
                  ><NativeSelect v-model="manageForm.location"
                    ><option value="">Any location</option>
                    <option
                      v-for="location in locations"
                      :key="location.public_id"
                      :value="location.public_id"
                    >
                      {{ location.name }}
                    </option></NativeSelect
                  ></label
                >
              </div>
              <template v-if="manageTarget.device_type === 'pos'"
                ><label
                  class="flex items-start justify-between gap-5 rounded-xl bg-muted/35 p-4"
                  ><span
                    ><strong class="block text-sm"
                      >Strict register controls</strong
                    ><span
                      class="mt-1 block text-xs leading-5 text-muted-foreground"
                      >Require manager approval for item reductions, discounts,
                      voids, and refunds.</span
                    ></span
                  ><Switch
                    :checked="manageForm.strictMode"
                    @update:checked="manageForm.strictMode = $event" /></label
                ><label
                  class="flex items-start justify-between gap-5 rounded-xl bg-muted/35 p-4"
                  ><span
                    ><strong class="block text-sm"
                      >Collect delivery payments</strong
                    ><span
                      class="mt-1 block text-xs leading-5 text-muted-foreground"
                      >Let this counter record payment for incoming delivery
                      orders.</span
                    ></span
                  ><Switch
                    :checked="manageForm.allowDeliveryPayments"
                    @update:checked="manageForm.allowDeliveryPayments = $event"
                /></label>
                <fieldset>
                  <legend class="field-label">
                    Accepted register payments
                  </legend>
                  <div class="mt-2 grid gap-2 sm:grid-cols-3">
                    <label
                      v-for="method in registerPaymentChoices"
                      :key="method.value"
                      class="flex items-center gap-2 rounded-lg border p-3 text-sm font-semibold"
                      ><NativeCheckbox
                        v-model="manageForm.paymentMethods"
                        :value="method.value"
                      />{{ method.label }}</label
                    >
                  </div>
                </fieldset>
                <fieldset>
                  <legend class="field-label">Quick items</legend>
                  <p class="mt-1 text-xs text-muted-foreground">
                    Pin up to 24 published offerings above the catalog.
                  </p>
                  <div
                    class="mt-3 max-h-48 space-y-1 overflow-y-auto rounded-lg border p-2"
                  >
                    <label
                      v-for="offering in offerings"
                      :key="offering.public_id"
                      class="flex items-center gap-2 rounded-md p-2 text-sm hover:bg-secondary/50"
                      ><NativeCheckbox
                        v-model="manageForm.favoriteOfferingIds"
                        :value="offering.public_id"
                        :disabled="
                          !manageForm.favoriteOfferingIds.includes(
                            offering.public_id,
                          ) && manageForm.favoriteOfferingIds.length >= 24
                        "
                      />{{ offering.name }}</label
                    >
                    <p
                      v-if="!offerings.length"
                      class="p-3 text-sm text-muted-foreground"
                    >
                      Publish offerings to configure quick items.
                    </p>
                  </div>
                </fieldset></template
              >
              <template
                v-else-if="manageTarget.device_type === 'customer_display'"
                ><label
                  ><span class="field-label">Linked counter</span
                  ><NativeSelect v-model="manageForm.linkedStation"
                    ><option value="">Choose counter</option>
                    <option
                      v-for="station in devicesFor('pos').filter(
                        (item) => item.is_active,
                      )"
                      :key="station.public_id"
                      :value="station.public_id"
                    >
                      {{ station.name }}
                    </option></NativeSelect
                  ></label
                ><Button
                  variant="outline"
                  type="button"
                  @click="openDisplayContent(manageTarget)"
                  ><Megaphone class="h-4 w-4" aria-hidden="true" /> Edit ads and
                  display content</Button
                ></template
              >
              <template v-else
                ><label
                  ><span class="field-label">Refresh interval</span
                  ><NativeSelect v-model="manageForm.refreshSeconds"
                    ><option value="5">Every 5 seconds</option>
                    <option value="10">Every 10 seconds</option>
                    <option value="15">Every 15 seconds</option>
                    <option value="30">Every 30 seconds</option></NativeSelect
                  ></label
                ><label
                  class="flex items-start justify-between gap-5 rounded-xl bg-muted/35 p-4"
                  ><span
                    ><strong class="block text-sm">Sound for new orders</strong
                    ><span
                      class="mt-1 block text-xs leading-5 text-muted-foreground"
                      >Play an audible cue when confirmed work enters this
                      queue.</span
                    ></span
                  ><Switch
                    :checked="manageForm.soundEnabled"
                    @update:checked="manageForm.soundEnabled = $event" /></label
              ></template>
            </div>
            <aside class="bg-muted/25 p-5">
              <div class="flex items-center gap-3">
                <span
                  class="grid h-10 w-10 place-items-center rounded-xl bg-background text-primary"
                  ><KeyRound class="h-5 w-5" aria-hidden="true"
                /></span>
                <div>
                  <h3 class="font-extrabold">Pair this screen</h3>
                  <p class="text-xs text-muted-foreground">
                    Single-use setup code
                  </p>
                </div>
              </div>
              <div class="mt-5 rounded-xl border bg-background p-5">
                <div
                  v-if="pairingLoading"
                  class="py-5 text-center text-sm text-muted-foreground"
                >
                  Checking current code…
                </div>
                <div v-else-if="pairingCode">
                  <PairingCodeDisplay
                    class="justify-center"
                    :code="pairingCode"
                  />
                  <p
                    class="mt-4 text-center text-xs leading-5 text-muted-foreground"
                  >
                    This code stays here until it is used or replaced.
                  </p>
                </div>
                <div v-else class="py-4 text-center">
                  <KeyRound
                    class="mx-auto h-7 w-7 text-muted-foreground/55"
                    aria-hidden="true"
                  />
                  <p class="mt-3 font-extrabold">No active code</p>
                  <p class="mt-1 text-xs leading-5 text-muted-foreground">
                    Generate one when the dedicated screen is ready.
                  </p>
                </div>
              </div>
              <div class="mt-3 grid gap-2">
                <Button
                  v-if="pairingCode"
                  variant="outline"
                  type="button"
                  @click="copyPairingCode"
                  ><Copy class="h-4 w-4" aria-hidden="true" /> Copy code</Button
                ><Button
                  variant="outline"
                  type="button"
                  :disabled="generatingCode"
                  @click="generatePairingCode"
                  ><RefreshCw class="h-4 w-4" aria-hidden="true" />{{
                    generatingCode
                      ? "Generating…"
                      : pairingCode
                        ? "Replace code"
                        : "Generate code"
                  }}</Button
                ><ButtonAnchor
                  :href="surfaceFor(manageTarget.device_type).path"
                  target="_blank"
                  rel="noopener"
                  ><ExternalLink class="h-4 w-4" aria-hidden="true" /> Open
                  {{
                    surfaceFor(manageTarget.device_type).shortTitle
                  }}</ButtonAnchor
                >
              </div>
            </aside>
          </div>
          <DialogFooter class="mt-6 justify-between sm:justify-between"
            ><Button
              variant="ghost"
              class="text-destructive"
              type="button"
              @click="
                manageOpen = false;
                pendingRevoke = manageTarget;
              "
              ><Power class="h-4 w-4" aria-hidden="true" /> Deactivate</Button
            >
            <div class="flex gap-2">
              <Button
                variant="outline"
                type="button"
                @click="manageOpen = false"
                >Cancel</Button
              ><Button :disabled="savingDevice">{{
                savingDevice ? "Saving…" : "Save controls"
              }}</Button>
            </div></DialogFooter
          >
        </form></DialogContent
      ></Dialog
    >

    <Dialog v-model:open="contentOpen">
      <DialogContent class="max-h-[92dvh] overflow-y-auto sm:max-w-3xl">
        <form @submit.prevent="saveDisplayContent">
          <DialogHeader
            ><div
              class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
            >
              <Megaphone class="h-5 w-5" aria-hidden="true" />
            </div>
            <DialogTitle>Customer display content</DialogTitle
            ><DialogDescription
              >Organize the promotional rotation shown on
              {{ editingDisplay?.name }} while its linked order remains
              visible.</DialogDescription
            ></DialogHeader
          >
          <div
            class="mt-6 overflow-hidden rounded-xl border md:grid md:grid-cols-[minmax(0,1.15fr)_minmax(15rem,.85fr)]"
          >
            <fieldset
              class="border-b bg-muted/25 p-5 md:border-b-0 md:border-r"
            >
              <legend class="font-extrabold">Promotion rotation</legend>
              <p class="mt-1 text-sm leading-6 text-muted-foreground">
                Choose whether this screen follows every published promotion or
                a curated selection.
              </p>
              <div class="mt-4 space-y-2">
                <Button
                  :variant="adConfig.mode === 'all' ? 'default' : 'outline'"
                  class="h-auto w-full justify-start px-4 py-3 text-left"
                  type="button"
                  @click="adConfig.mode = 'all'"
                  ><Layers3 class="h-5 w-5 shrink-0" aria-hidden="true" /><span
                    ><strong class="block">All published promotions</strong
                    ><span class="mt-0.5 block text-xs font-normal opacity-75"
                      >Automatically includes current and future published
                      content.</span
                    ></span
                  ></Button
                ><Button
                  :variant="
                    adConfig.mode === 'selected' ? 'default' : 'outline'
                  "
                  class="h-auto w-full justify-start px-4 py-3 text-left"
                  type="button"
                  @click="adConfig.mode = 'selected'"
                  ><ListChecks
                    class="h-5 w-5 shrink-0"
                    aria-hidden="true"
                  /><span
                    ><strong class="block">Curated selection</strong
                    ><span class="mt-0.5 block text-xs font-normal opacity-75"
                      >Only rotate the promotions selected below.</span
                    ></span
                  ></Button
                >
              </div>
            </fieldset>
            <fieldset class="p-5">
              <legend class="font-extrabold">Playback</legend>
              <p class="mt-1 text-sm leading-6 text-muted-foreground">
                Control the pace and what appears when no promotion is
                available.
              </p>
              <label class="mt-4 block"
                ><span class="field-label">Rotation speed</span
                ><NativeSelect v-model="adConfig.rotationSeconds" class="mt-2"
                  ><option
                    v-for="seconds in [5, 8, 10, 15, 20, 30]"
                    :key="seconds"
                    :value="String(seconds)"
                  >
                    Every {{ seconds }} seconds
                  </option></NativeSelect
                ></label
              ><label class="mt-4 flex items-start gap-3 border-t pt-4"
                ><NativeCheckbox
                  v-model="adConfig.showBrandFallback"
                  class="mt-0.5"
                /><span
                  ><strong class="block text-sm"
                    >Business branding fallback</strong
                  ><span
                    class="mt-1 block text-xs leading-5 text-muted-foreground"
                    >Show the cover image and tagline when the rotation is
                    empty.</span
                  ></span
                ></label
              >
            </fieldset>
          </div>
          <fieldset v-if="adConfig.mode === 'selected'" class="mt-6">
            <legend class="font-extrabold">Published content</legend>
            <div class="mt-1 flex items-center justify-between gap-4">
              <p class="text-sm text-muted-foreground">
                {{ adConfig.selectedIds.length }} selected for this screen
              </p>
              <Button
                variant="ghost"
                size="sm"
                type="button"
                @click="adConfig.selectedIds = []"
                >Clear selection</Button
              >
            </div>
            <div
              v-if="promotionDisplays.length"
              class="mt-3 grid gap-2 sm:grid-cols-2"
            >
              <label
                v-for="publication in promotionDisplays"
                :key="publication.public_id"
                class="flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-secondary/50"
                ><NativeCheckbox
                  v-model="adConfig.selectedIds"
                  :value="publication.public_id"
                /><img
                  v-if="publication.background_asset_url"
                  :src="publication.background_asset_url"
                  alt=""
                  class="h-12 w-12 rounded-md border object-cover"
                />
                <div
                  v-else
                  class="grid h-12 w-12 place-items-center rounded-md bg-secondary"
                >
                  <Megaphone
                    class="h-5 w-5 text-muted-foreground"
                    aria-hidden="true"
                  />
                </div>
                <span class="min-w-0"
                  ><strong class="block truncate text-sm">{{
                    publication.name
                  }}</strong
                  ><span
                    class="mt-1 block text-xs capitalize text-muted-foreground"
                    >{{ publication.kind }}</span
                  ></span
                ></label
              >
            </div>
            <div
              v-else
              class="mt-3 rounded-lg border border-dashed p-5 text-sm text-muted-foreground"
            >
              No published promotions yet.
              <NuxtLink
                class="font-bold text-primary underline underline-offset-4"
                to="/workspace/site/displays"
                >Create one in Display Studio.</NuxtLink
              >
            </div>
          </fieldset>
          <DialogFooter class="mt-6"
            ><Button
              variant="outline"
              type="button"
              @click="contentOpen = false"
              >Cancel</Button
            ><Button :disabled="savingContent">{{
              savingContent ? "Saving…" : "Save display content"
            }}</Button></DialogFooter
          >
        </form>
      </DialogContent>
    </Dialog>

    <Dialog
      :open="Boolean(pendingRevoke)"
      @update:open="pendingRevoke = $event ? pendingRevoke : null"
      ><DialogContent class="sm:max-w-md"
        ><DialogHeader
          ><DialogTitle>Deactivate {{ pendingRevoke?.name }}?</DialogTitle
          ><DialogDescription
            >The saved token and current setup code will stop working
            immediately. Existing orders and audit records remain
            available.</DialogDescription
          ></DialogHeader
        ><DialogFooter
          ><Button variant="outline" type="button" @click="pendingRevoke = null"
            >Keep active</Button
          ><Button
            variant="destructive"
            type="button"
            :disabled="savingDevice"
            @click="revokeDevice"
            >Deactivate</Button
          ></DialogFooter
        ></DialogContent
      ></Dialog
    >
  </section>
</template>

<script setup>
import {
  Activity,
  CircleHelp,
  Copy,
  ExternalLink,
  KeyRound,
  Layers3,
  ListChecks,
  Megaphone,
  Monitor,
  MonitorSmartphone,
  PackageCheck,
  Plus,
  Power,
  RefreshCw,
  Route,
  Settings2,
  ShieldCheck,
  Truck,
  Wifi,
  X,
} from "lucide-vue-next";
import { toast } from "@/components/ui/toast";

const business = useBusinessStore();
const { apiFetch } = useApiClient();
const devices = ref([]);
const links = ref([]);
const locations = ref([]);
const publications = ref([]);
const offerings = ref([]);
const loading = ref(true);
const error = ref("");
const tab = ref("pos");
const createOpen = ref(false);
const creatingType = ref("pos");
const deviceName = ref("");
const deviceLocation = ref("");
const strictDevice = ref(false);
const savingDevice = ref(false);
const updatingControlId = ref("");
const pendingRevoke = ref(null);
const manageOpen = ref(false);
const manageTarget = ref(null);
const pairingCode = ref("");
const pairingLoading = ref(false);
const generatingCode = ref(false);
const contentOpen = ref(false);
const editingDisplay = ref(null);
const savingContent = ref(false);
const showFlowGuide = ref(true);
const adConfig = reactive({
  mode: "all",
  selectedIds: [],
  rotationSeconds: "10",
  showBrandFallback: true,
});
const manageForm = reactive({
  name: "",
  location: "",
  strictMode: false,
  allowDeliveryPayments: true,
  paymentMethods: [],
  favoriteOfferingIds: [],
  linkedStation: "",
  refreshSeconds: "10",
  soundEnabled: true,
});
const registerPaymentChoices = [
  { value: "cash", label: "Cash" },
  { value: "card", label: "Card" },
  { value: "gcash", label: "GCash" },
  { value: "maya", label: "Maya" },
  { value: "pay_later", label: "Pay later" },
];
const definitions = [
  {
    type: "pos",
    title: "Counter checkout",
    shortTitle: "Counter",
    deviceLabel: "counter station",
    path: "/pos-terminal",
    icon: MonitorSmartphone,
    audienceShort: "Sales team",
    audience: "Sales associates create, price, and complete in-person orders.",
    description:
      "Image-led catalog, modifiers, promotions, payment, pickup, in-store, and delivery.",
    placeholder: "Main checkout",
  },
  {
    type: "customer_display",
    title: "Customer display",
    shortTitle: "Customer display",
    deviceLabel: "customer display",
    path: "/customer-display",
    icon: Monitor,
    audienceShort: "Customer-facing",
    audience:
      "Customers see promotions and only the live order from their linked counter.",
    description:
      "A presentation-safe view of promotions, the live basket, totals, and receipt.",
    placeholder: "Front customer screen",
  },
  {
    type: "kitchen_display",
    title: "Order fulfillment",
    shortTitle: "Fulfillment",
    deviceLabel: "fulfillment screen",
    path: "/fulfillment-display",
    icon: PackageCheck,
    audienceShort: "Packing & operations",
    audience:
      "Packing, production, inventory, or service teams prepare confirmed orders.",
    description:
      "Confirmed work moves through new, in progress, ready, and collected.",
    placeholder: "Fulfillment desk",
  },
  {
    type: "dispatch_display",
    title: "Delivery operations",
    shortTitle: "Delivery",
    deviceLabel: "delivery screen",
    path: "/delivery-display",
    icon: Truck,
    audienceShort: "Dispatch team",
    audience:
      "Dispatch teams receive delivery orders and complete the final handoff.",
    description:
      "Delivery orders move through incoming, packing, ready to dispatch, and delivered.",
    placeholder: "Delivery desk",
  },
];
const flowSteps = [
  {
    title: "Counter checkout",
    detail: "Creates and prices the order.",
    icon: MonitorSmartphone,
  },
  {
    title: "Customer display",
    detail: "Mirrors only its linked counter.",
    icon: Monitor,
  },
  {
    title: "Order fulfillment",
    detail: "Receives confirmed work.",
    icon: PackageCheck,
  },
  {
    title: "Delivery operations",
    detail: "Handles delivery-only handoff.",
    icon: Truck,
  },
];
const surfaces = computed(() =>
  definitions.map((item) => ({
    ...item,
    count: devicesFor(item.type).filter((device) => device.is_active).length,
  })),
);
const activeSurface = computed(() => surfaceFor(tab.value));
const creatingSurface = computed(() => surfaceFor(creatingType.value));
const currentDevices = computed(() => devicesFor(tab.value));
const activeDevices = computed(() =>
  currentDevices.value.filter((item) => item.is_active),
);
const promotionDisplays = computed(() =>
  publications.value.filter(
    (item) =>
      item.is_active &&
      item.is_published &&
      ["promotion", "information"].includes(item.kind),
  ),
);

watch(() => business.activeBusiness?.public_id, load);
onMounted(async () => {
  showFlowGuide.value =
    localStorage.getItem("pixelcore_pos_flow_dismissed") !== "1";
  if (!business.activeBusiness) await business.loadBusinesses();
  await load();
});
async function load() {
  if (!business.activeBusiness) return;
  loading.value = true;
  error.value = "";
  try {
    const id = business.activeBusiness.public_id;
    const [
      deviceResponse,
      linkResponse,
      locationResponse,
      publicationResponse,
      offeringResponse,
    ] = await Promise.all([
      apiFetch(`businesses/${id}/devices/`),
      apiFetch(`businesses/${id}/device-links/`),
      apiFetch(`businesses/${id}/locations/`),
      apiFetch(`businesses/${id}/displays/`),
      apiFetch(`businesses/${id}/offerings/?status=published&page_size=100`),
    ]);
    devices.value = (deviceResponse.results || []).filter((item) =>
      definitions.some((definition) => definition.type === item.device_type),
    );
    links.value = linkResponse.results || [];
    locations.value = locationResponse.results || [];
    publications.value = publicationResponse.results || [];
    offerings.value = offeringResponse.results || [];
  } catch (requestError) {
    error.value =
      requestError?.data?.error?.message || "Could not load POS setup.";
  } finally {
    loading.value = false;
  }
}
function surfaceFor(type) {
  return definitions.find((item) => item.type === type) || definitions[0];
}
function devicesFor(type) {
  return devices.value.filter((item) => item.device_type === type);
}
function openCreate() {
  creatingType.value = tab.value;
  deviceName.value = "";
  deviceLocation.value = "";
  strictDevice.value = false;
  createOpen.value = true;
}
async function createDevice() {
  savingDevice.value = true;
  try {
    const created = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/`,
      {
        method: "POST",
        body: {
          name: deviceName.value,
          device_type: creatingType.value,
          location_public_id: deviceLocation.value || null,
          is_active: true,
          configuration:
            creatingType.value === "pos"
              ? {
                  strict_mode: strictDevice.value,
                  allow_delivery_payments: true,
                  payment_methods: [
                    "cash",
                    "card",
                    "gcash",
                    "maya",
                    "pay_later",
                  ],
                  receipt_options: ["print", "digital"],
                }
              : {},
        },
      },
    );
    devices.value.push(created);
    if (
      creatingType.value === "customer_display" &&
      devicesFor("pos").filter((item) => item.is_active).length === 1
    )
      await linkDisplay(
        created,
        devicesFor("pos").find((item) => item.is_active).public_id,
      );
    createOpen.value = false;
    await openManage(created);
    toast({
      title: "Device created",
      description: `${created.name} is ready to configure and pair.`,
    });
  } catch (requestError) {
    failedToast("Device not created", requestError);
  } finally {
    savingDevice.value = false;
  }
}
async function openManage(device) {
  const configuration = device.configuration || {};
  manageTarget.value = device;
  Object.assign(manageForm, {
    name: device.name,
    location: device.location_public_id || "",
    strictMode: Boolean(configuration.strict_mode),
    allowDeliveryPayments: configuration.allow_delivery_payments !== false,
    paymentMethods: [
      ...(configuration.payment_methods || [
        "cash",
        "card",
        "gcash",
        "maya",
        "pay_later",
      ]),
    ],
    favoriteOfferingIds: [...(configuration.favorite_offering_ids || [])],
    linkedStation: linkedStation(device.public_id),
    refreshSeconds: String(configuration.refresh_seconds || 10),
    soundEnabled: configuration.sound_enabled !== false,
  });
  pairingCode.value = "";
  pairingLoading.value = true;
  manageOpen.value = true;
  try {
    const response = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/${device.public_id}/pairing-code/`,
    );
    pairingCode.value = response.pairing_code || "";
  } catch (requestError) {
    failedToast("Current setup code unavailable", requestError);
  } finally {
    pairingLoading.value = false;
  }
}
async function saveManagedDevice() {
  if (!manageTarget.value || savingDevice.value) return;
  if (
    manageTarget.value.device_type === "pos" &&
    !manageForm.paymentMethods.length
  ) {
    toast({
      title: "Choose a payment method",
      description: "A counter needs at least one way to complete a sale.",
      variant: "destructive",
    });
    return;
  }
  savingDevice.value = true;
  try {
    const device = manageTarget.value;
    const configuration = {
      ...(device.configuration || {}),
      strict_mode: manageForm.strictMode,
      allow_delivery_payments: manageForm.allowDeliveryPayments,
      payment_methods: manageForm.paymentMethods,
      receipt_options: ["print", "digital"],
      favorite_offering_ids: manageForm.favoriteOfferingIds,
      refresh_seconds: Number(manageForm.refreshSeconds),
      sound_enabled: manageForm.soundEnabled,
    };
    const updated = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/${device.public_id}/`,
      {
        method: "PATCH",
        body: {
          name: manageForm.name,
          location_public_id: manageForm.location || null,
          configuration,
        },
      },
    );
    Object.assign(device, updated);
    if (device.device_type === "customer_display")
      await linkDisplay(device, manageForm.linkedStation);
    manageOpen.value = false;
    toast({
      title: "Device controls saved",
      description: `${updated.name} will use the updated settings on its next refresh.`,
    });
  } catch (requestError) {
    failedToast("Device controls not saved", requestError);
  } finally {
    savingDevice.value = false;
  }
}
async function generatePairingCode() {
  if (!manageTarget.value || generatingCode.value) return;
  generatingCode.value = true;
  try {
    const response = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/${manageTarget.value.public_id}/pairing-code/`,
      { method: "POST" },
    );
    pairingCode.value = response.pairing_code;
    toast({
      title: "Setup code generated",
      description: `Enter it on ${manageTarget.value.name}.`,
    });
  } catch (requestError) {
    failedToast("Code unavailable", requestError);
  } finally {
    generatingCode.value = false;
  }
}
async function copyPairingCode() {
  await navigator.clipboard.writeText(pairingCode.value);
  toast({
    title: "Setup code copied",
    description: `Paste it into ${manageTarget.value?.name}.`,
  });
}
function openDisplayContent(device) {
  const configuration = device.configuration || {};
  editingDisplay.value = device;
  adConfig.mode = configuration.ad_content_mode || "all";
  adConfig.selectedIds = [...(configuration.promotion_display_ids || [])];
  adConfig.rotationSeconds = String(configuration.ad_rotation_seconds || 10);
  adConfig.showBrandFallback = configuration.show_brand_fallback !== false;
  contentOpen.value = true;
}
async function saveDisplayContent() {
  if (!editingDisplay.value) return;
  savingContent.value = true;
  try {
    const configuration = {
      ...(editingDisplay.value.configuration || {}),
      ad_content_mode: adConfig.mode,
      promotion_display_ids:
        adConfig.mode === "selected" ? adConfig.selectedIds : [],
      ad_rotation_seconds: Number(adConfig.rotationSeconds),
      show_brand_fallback: adConfig.showBrandFallback,
    };
    const updated = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/${editingDisplay.value.public_id}/`,
      { method: "PATCH", body: { configuration } },
    );
    Object.assign(editingDisplay.value, updated);
    contentOpen.value = false;
    toast({
      title: "Customer display updated",
      description: `${updated.name} will use the new content rotation.`,
    });
  } catch (requestError) {
    failedToast("Display content not saved", requestError);
  } finally {
    savingContent.value = false;
  }
}
function linkedStation(displayId) {
  return (
    links.value.find(
      (link) => link.target_device_public_id === displayId && link.is_active,
    )?.source_device_public_id || ""
  );
}
function linkedStationName(displayId) {
  const stationId = linkedStation(displayId);
  return stationId
    ? `Linked to ${devicesFor("pos").find((item) => item.public_id === stationId)?.name || "counter"}`
    : "Not linked to a counter";
}
function linkedDisplays(stationId) {
  return links.value.filter(
    (link) => link.source_device_public_id === stationId && link.is_active,
  ).length;
}
function contentSummary(device) {
  const configuration = device.configuration || {};
  return configuration.ad_content_mode === "selected"
    ? `${(configuration.promotion_display_ids || []).length} selected`
    : "All ads";
}
async function linkDisplay(display, stationId) {
  const existing = links.value.find(
    (link) => link.target_device_public_id === display.public_id,
  );
  try {
    if (!stationId) {
      if (existing) {
        await apiFetch(
          `businesses/${business.activeBusiness.public_id}/device-links/${existing.public_id}/`,
          { method: "DELETE" },
        );
        links.value = links.value.filter(
          (link) => link.public_id !== existing.public_id,
        );
      }
      toast({
        title: "Display unlinked",
        description: `${display.name} no longer follows a counter.`,
      });
      return;
    }
    const body = {
      source_device_public_id: stationId,
      target_device_public_id: display.public_id,
      link_type: "customer_display",
      is_active: true,
    };
    if (existing)
      Object.assign(
        existing,
        await apiFetch(
          `businesses/${business.activeBusiness.public_id}/device-links/${existing.public_id}/`,
          { method: "PATCH", body },
        ),
      );
    else
      links.value.push(
        await apiFetch(
          `businesses/${business.activeBusiness.public_id}/device-links/`,
          { method: "POST", body },
        ),
      );
    toast({
      title: "Display linked",
      description: `${display.name} now follows ${devicesFor("pos").find((item) => item.public_id === stationId)?.name}.`,
    });
  } catch (requestError) {
    failedToast("Display not linked", requestError);
  }
}
async function setStrictMode(device, checked) {
  updatingControlId.value = device.public_id;
  try {
    const configuration = {
      ...(device.configuration || {}),
      strict_mode: checked,
    };
    const updated = await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/${device.public_id}/`,
      { method: "PATCH", body: { configuration } },
    );
    Object.assign(device, updated);
    toast({
      title: checked ? "Strict controls enabled" : "Standard controls enabled",
      description: checked
        ? "Manager approval is now required for voids and promotions."
        : "Cashiers can now adjust the current sale without manager approval.",
    });
  } catch (requestError) {
    failedToast("Register controls not updated", requestError);
  } finally {
    updatingControlId.value = "";
  }
}
async function revokeDevice() {
  if (!pendingRevoke.value) return;
  savingDevice.value = true;
  const device = pendingRevoke.value;
  try {
    await apiFetch(
      `businesses/${business.activeBusiness.public_id}/devices/${device.public_id}/`,
      { method: "DELETE" },
    );
    device.is_active = false;
    pendingRevoke.value = null;
    toast({
      title: "Device deactivated",
      description: `${device.name} can no longer connect.`,
    });
  } catch (requestError) {
    failedToast("Device still active", requestError);
  } finally {
    savingDevice.value = false;
  }
}
function failedToast(title, errorValue) {
  toast({
    title,
    description:
      errorValue?.data?.error?.message ||
      Object.values(errorValue?.data || {})
        .flat()
        .join(" ") ||
      "Check the details and try again.",
    variant: "destructive",
  });
}
function locationName(publicId) {
  return (
    locations.value.find((item) => item.public_id === publicId)?.name ||
    "Any location"
  );
}
function dismissFlowGuide() {
  showFlowGuide.value = false;
  localStorage.setItem("pixelcore_pos_flow_dismissed", "1");
}
function restoreFlowGuide() {
  showFlowGuide.value = true;
  localStorage.removeItem("pixelcore_pos_flow_dismissed");
}
</script>
