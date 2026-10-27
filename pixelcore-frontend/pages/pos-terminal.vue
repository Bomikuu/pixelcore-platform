<template>
  <main class="pos-terminal min-h-dvh bg-muted/25 text-foreground">
    <DevicePairingPanel
      v-if="state === 'unpaired'"
      v-model="code"
      title="Counter checkout"
      description="A focused checkout workspace for any business selling products or services in person."
      :details="[
        'Browse an image-led catalog with variants and options.',
        'Use server-verified pricing, promotions, and payment states.',
        'Send the live basket and receipt to a linked customer screen.',
      ]"
      audience="Cashier or sales associate"
      action-label="Pair counter"
      :working="working"
      :message="message"
      illustration="pos"
      @submit="pair"
    />

    <section
      v-else-if="state === 'loading'"
      class="mx-auto max-w-3xl px-6 py-20"
    >
      <StatePanel
        kind="loading"
        title="Opening counter"
        message="Restoring the catalog and current sale."
      />
    </section>

    <section
      v-else-if="state === 'error'"
      class="fixed inset-0 z-50 grid min-h-dvh place-items-center bg-background px-5 py-10"
    >
      <StatePanel
        class="w-full max-w-2xl border bg-card shadow-xl"
        kind="error"
        title="Counter needs attention"
        :message="message"
      >
        <div class="mt-5 flex flex-wrap gap-2">
          <Button type="button" @click="load">Reconnect</Button
          ><Button variant="outline" type="button" @click="unpair"
            >Use another code</Button
          >
        </div>
      </StatePanel>
    </section>

    <section v-else class="flex min-h-dvh flex-col">
      <header
        class="sticky top-0 z-30 flex min-h-16 flex-wrap items-center justify-between gap-3 border-b bg-background/95 px-4 py-3 backdrop-blur sm:px-6"
      >
        <div class="flex min-w-0 items-center gap-3">
          <img
            v-if="identity.logo_url"
            :src="identity.logo_url"
            alt=""
            class="h-10 w-10 rounded-xl border object-cover"
          />
          <div
            v-else
            class="grid h-10 w-10 place-items-center rounded-xl bg-primary text-sm font-black text-primary-foreground"
          >
            {{ initials }}
          </div>
          <div class="min-w-0">
            <p class="truncate text-sm font-extrabold">
              {{ identity.display_name }}
            </p>
            <p class="truncate text-xs text-muted-foreground">
              {{ session.station_name }} · Counter
            </p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <Badge variant="outline" class="hidden gap-1.5 sm:flex" role="status"
            ><span
              class="h-2 w-2 rounded-full"
              :class="online ? 'bg-emerald-500' : 'bg-amber-500'"
              aria-hidden="true"
            />
            {{ online ? 'Live' : 'Offline' }} · R{{ session.revision }}</Badge
          >
          <span
            class="hidden text-sm font-semibold tabular-nums text-muted-foreground md:inline"
            >{{ currentTime }}</span
          >
          <Button
            variant="outline"
            size="sm"
            type="button"
            :disabled="working"
            @click="load"
            ><RefreshCw class="h-4 w-4" aria-hidden="true" /> Refresh</Button
          >
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="outline" size="sm" type="button" class="gap-2">
                <Settings2 class="h-4 w-4" aria-hidden="true" />
                <span class="hidden sm:inline">{{ strictMode ? 'Strict controls' : 'Standard controls' }}</span>
                <ChevronDown class="h-3.5 w-3.5" aria-hidden="true" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" class="w-64">
              <DropdownMenuLabel>Register controls</DropdownMenuLabel>
              <p class="px-2 pb-3 text-xs leading-5 text-muted-foreground">{{ strictMode ? 'Item reductions, discounts, voids, and refunds require manager approval.' : 'Controls follow this station’s settings in Sell → POS.' }}</p>
              <DropdownMenuSeparator />
              <DropdownMenuItem @select="shortcutsOpen = true"><Keyboard class="h-4 w-4" /> Keyboard shortcuts</DropdownMenuItem>
              <DropdownMenuItem :disabled="working" @select="load"><RefreshCw class="h-4 w-4" /> Refresh counter</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem :disabled="working" class="text-destructive" @select="unpair"><Unplug class="h-4 w-4" /> Disconnect counter</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <nav
        class="flex min-h-14 flex-wrap items-center gap-1 border-b bg-background px-4 py-1.5 sm:px-6"
        aria-label="Register mode"
      >
        <Button
          variant="ghost"
          type="button"
          class="h-10 px-3"
          :class="
            registerMode === 'sale'
              ? 'bg-primary text-primary-foreground hover:bg-primary/90'
              : 'text-muted-foreground'
          "
          :aria-current="registerMode === 'sale' ? 'page' : undefined"
          @click="registerMode = 'sale'"
          ><ScanLine class="h-4 w-4" aria-hidden="true" /> New sale</Button
        >
        <Button
          v-if="stationControls.allow_delivery_payments !== false"
          variant="ghost"
          type="button"
          class="h-10 px-3"
          :class="
            registerMode === 'deliveries'
              ? 'bg-secondary text-primary hover:bg-secondary'
              : 'text-muted-foreground'
          "
          :aria-current="registerMode === 'deliveries' ? 'page' : undefined"
          @click="openDeliveries"
          ><Truck class="h-4 w-4" aria-hidden="true" /> Deliveries
          <span
            class="grid min-w-5 place-items-center rounded-full bg-primary px-1.5 py-0.5 text-[11px] font-extrabold text-primary-foreground tabular-nums"
            >{{ deliveryOrders.length }}</span
          ></Button
        >
        <div class="ml-auto flex items-center gap-1">
          <Button variant="ghost" size="sm" type="button" @click="openHeldSales"
            ><PauseCircle class="h-4 w-4" aria-hidden="true" /> Held
            <span v-if="heldSales.length" class="font-extrabold tabular-nums">{{
              heldSales.length
            }}</span></Button
          ><Button
            variant="ghost"
            size="sm"
            type="button"
            @click="openTransactions"
            ><History class="h-4 w-4" aria-hidden="true" /> Recent</Button
          >
          <div v-if="registerMode === 'sale'" class="ml-2 flex items-center rounded-lg border bg-card p-0.5" role="group" aria-label="Catalog view">
            <Button variant="ghost" size="icon" type="button" class="h-8 w-9" :class="catalogView === 'grid' ? 'bg-primary text-primary-foreground hover:bg-primary/90' : ''" :aria-pressed="catalogView === 'grid'" aria-label="Grid view" @click="setCatalogView('grid')"><LayoutGrid class="h-4 w-4" aria-hidden="true" /></Button>
            <Button variant="ghost" size="icon" type="button" class="h-8 w-9" :class="catalogView === 'list' ? 'bg-primary text-primary-foreground hover:bg-primary/90' : ''" :aria-pressed="catalogView === 'list'" aria-label="List view" @click="setCatalogView('list')"><List class="h-4 w-4" aria-hidden="true" /></Button>
          </div>
        </div>
      </nav>

      <div
        v-if="registerMode === 'sale'"
        class="pos-sale-layout grid min-h-0 flex-1 lg:grid-cols-[minmax(0,1fr)_22rem] xl:grid-cols-[minmax(0,1fr)_26rem] 2xl:grid-cols-[minmax(0,1fr)_28rem]"
      >
        <section class="min-w-0 p-4 sm:p-6" aria-labelledby="catalog-heading">
          <div
            class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between"
          >
            <div>
              <h1
                id="catalog-heading"
                class="display-face text-3xl font-semibold tracking-[-0.025em]"
              >
                Catalog
              </h1>
              <p class="mt-1 text-sm text-muted-foreground">
                Select an item to add it to the live customer order.
              </p>
            </div>
            <div class="relative w-full lg:max-w-md">
              <Search
                class="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-muted-foreground"
                aria-hidden="true"
              /><label class="sr-only" for="terminal-search"
                >Search or scan an item</label
              ><Input
                id="terminal-search"
                ref="searchInput"
                v-model="search"
                class="h-11 bg-card pl-10 pr-24 shadow-none"
                placeholder="Search name, SKU, or scan barcode"
                autocomplete="off"
                @keydown.enter="handleSearchEnter"
              />
              <div class="absolute right-1 top-1 flex items-center">
                <Button v-if="search" variant="ghost" size="icon" class="h-9 w-9" type="button" aria-label="Clear product search" @click="clearSearch"><X class="h-4 w-4" aria-hidden="true" /></Button>
                <Button variant="ghost" size="icon" class="h-9 w-10 border-l rounded-l-none" type="button" aria-label="Open barcode scanner (F4)" title="Scan barcode · F4" :disabled="working || !online" @click="scannerOpen = true"><ScanBarcode class="h-5 w-5" aria-hidden="true" /></Button>
              </div>
              <p class="mt-2 break-words text-xs text-muted-foreground" role="status" aria-live="polite" :class="scanFeedback.tone === 'error' ? 'text-destructive' : scanFeedback.tone === 'success' ? 'text-primary' : ''">
                {{ scanFeedback.text || `${filtered.length} items · Scan a barcode, or press F2 to search` }}
              </p>
            </div>
          </div>


          <div
            class="mt-5 flex gap-2 overflow-x-auto pb-2"
            aria-label="Catalog categories"
          >
            <Button v-if="favoriteOfferings.length" :variant="showFavoritesOnly ? 'default' : 'outline'" size="sm" class="shrink-0 gap-2 rounded-full" type="button" :aria-pressed="showFavoritesOnly" @click="showFavoritesOnly = !showFavoritesOnly"><Star class="h-3.5 w-3.5" aria-hidden="true" /> Quick items</Button>
            <Button
              v-for="category in categories"
              :key="category"
              :variant="activeCategory === category ? 'default' : 'outline'"
              size="sm"
              class="shrink-0 rounded-full"
              type="button"
              @click="activeCategory = category"
              >{{ category }}</Button
            >
          </div>

          <StatePanel
            v-if="!filtered.length"
            class="mt-6"
            :title="
              offerings.length
                ? 'No matching products'
                : 'No published products'
            "
            :message="
              offerings.length
                ? 'Try a different search or category.'
                : 'Publish a product from the workspace before using this counter.'
            "
          />
          <div v-else class="mt-4" :class="catalogView === 'grid' ? 'pos-catalog-grid' : 'grid gap-3'">
            <PosCatalogItem
              v-for="offering in filtered"
              :key="offering.public_id"
              :offering="offering"
              :price="money(offering.base_price)"
              :view="catalogView"
              :favorite="favoriteOfferings.some((favorite) => favorite.public_id === offering.public_id)"
              :disabled="working || !online"
              @add="beginAdd"
            />
          </div>
        </section>

        <aside
          class="pos-current-order m-4 mt-0 flex min-h-[34rem] min-w-0 flex-col overflow-hidden rounded-2xl bg-card shadow-sm sm:mx-6 lg:sticky lg:top-20 lg:ml-0 lg:mt-4 lg:h-[calc(100dvh-9rem)] lg:min-h-0"
          aria-labelledby="sale-heading"
        >
          <div class="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4">
            <div>
              <h2 id="sale-heading" class="display-face text-2xl font-semibold">
                Current order
              </h2>
              <p class="mt-0.5 text-xs text-muted-foreground">
                {{ cartCount }} item{{ cartCount === 1 ? "" : "s" }} · {{ working ? 'Updating order' : 'Server-priced order' }}
              </p>
            </div>
            <div v-if="cart.length" class="flex gap-1">
              <Button variant="ghost" size="sm" type="button" @click="openHold"
                ><PauseCircle class="h-4 w-4" aria-hidden="true" /> Hold</Button
              ><Button
                variant="ghost"
                size="sm"
                class="text-destructive"
                type="button"
                @click="openVoid"
                ><Trash2 class="h-4 w-4" aria-hidden="true" /> Void</Button
              >
            </div>
          </div>

          <div class="min-h-0 flex-1 overflow-y-auto px-5">
            <div v-if="cart.length" class="divide-y">
              <article
                v-for="(item, index) in cart"
                :key="`${item.offering_public_id}-${item.variant_public_id || 'base'}-${index}`"
                class="py-4"
              >
                <div class="flex gap-3">
                  <img
                    v-if="item.image_url"
                    :src="item.image_url"
                    alt=""
                    class="h-16 w-16 shrink-0 rounded-xl border object-cover"
                  />
                  <div
                    v-else
                    class="grid h-16 w-16 shrink-0 place-items-center rounded-xl border bg-secondary"
                  >
                    <Package
                      class="h-6 w-6 text-muted-foreground"
                      aria-hidden="true"
                    />
                  </div>
                  <div class="min-w-0 flex-1">
                    <div class="flex justify-between gap-3">
                      <strong class="line-clamp-2 text-sm leading-5">{{
                        item.name
                      }}</strong
                      ><strong class="shrink-0 text-sm tabular-nums">{{
                        money(item.line_total)
                      }}</strong>
                    </div>
                    <p
                      v-if="item.variant_name || item.options?.length"
                      class="mt-1 line-clamp-2 text-xs leading-4 text-muted-foreground"
                    >
                      {{ itemDetails(item) }}
                    </p>
                  </div>
                </div>
                <p
                  v-if="item.note"
                  class="mt-2 rounded-md bg-muted/50 px-2 py-1.5 text-xs italic text-muted-foreground"
                >
                  “{{ item.note }}”
                </p>
                <div class="mt-3 flex items-center gap-1.5">
                  <Button
                    variant="outline"
                    size="icon"
                    class="h-8 w-8"
                    type="button"
                    :aria-label="`Decrease ${item.name} quantity`"
                    :disabled="working"
                    @click="requestQuantityChange(index, -1)"
                    ><Minus class="h-3.5 w-3.5" aria-hidden="true" /></Button
                  ><span
                    class="min-w-8 text-center text-sm font-extrabold tabular-nums"
                    >{{ item.quantity }}</span
                  ><Button
                    variant="outline"
                    size="icon"
                    class="h-8 w-8"
                    type="button"
                    :aria-label="`Increase ${item.name} quantity`"
                    :disabled="working"
                    @click="requestQuantityChange(index, 1)"
                    ><Plus class="h-3.5 w-3.5" aria-hidden="true" /></Button
                  ><Button
                    variant="ghost"
                    size="sm"
                    type="button"
                    :disabled="working"
                    @click="openItemNote(index)"
                    ><MessageSquareText
                      class="h-3.5 w-3.5"
                      aria-hidden="true"
                    />
                    Note</Button
                  ><Button
                    variant="ghost"
                    size="sm"
                    class="ml-auto text-muted-foreground hover:text-destructive"
                    type="button"
                    :aria-label="`Remove ${item.name}`"
                    :disabled="working"
                    @click="requestRemoveItem(index)"
                    ><Trash2 class="h-4 w-4" aria-hidden="true" /></Button
                  >
                </div>
              </article>
            </div>
            <div
              v-else
              class="grid h-full min-h-64 place-items-center py-10 text-center"
            >
              <div>
                <div
                  class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-secondary"
                >
                  <ShoppingBasket
                    class="h-6 w-6 text-muted-foreground"
                    aria-hidden="true"
                  />
                </div>
                <p class="mt-4 font-extrabold">Ready for the next order</p>
                <p
                  class="mt-1 max-w-56 text-sm leading-6 text-muted-foreground"
                >
                  Select products from the catalog. Prices are verified by the
                  server.
                </p>
              </div>
            </div>
          </div>

          <div class="border-t bg-card p-5">
            <div class="flex gap-2">
              <label class="sr-only" for="terminal-discount"
                >Discount or promotion</label
              ><NativeSelect
                id="terminal-discount"
                v-model="discountCode"
                class="min-w-0 flex-1"
                ><option value="">No discount</option>
                <option
                  v-for="discount in discounts"
                  :key="discount.public_id"
                  :value="discount.code"
                >
                  {{ discount.name }} · {{ discountLabel(discount) }}
                </option></NativeSelect
              ><Button
                variant="outline"
                type="button"
                :disabled="working || !cart.length"
                @click="requestPromotion"
                ><Tag class="h-4 w-4" aria-hidden="true" /> Apply</Button
              >
            </div>
            <dl class="mt-4 space-y-2 text-sm">
              <div class="flex justify-between">
                <dt class="text-muted-foreground">Subtotal</dt>
                <dd class="font-semibold tabular-nums">
                  {{ money(session.cart.subtotal) }}
                </dd>
              </div>
              <div
                v-if="Number(session.cart.discount_total)"
                class="flex justify-between text-emerald-700"
              >
                <dt>Promotion</dt>
                <dd class="font-semibold tabular-nums">
                  −{{ money(session.cart.discount_total) }}
                </dd>
              </div>
              <div
                v-if="Number(session.cart.tax_total)"
                class="flex justify-between"
              >
                <dt class="text-muted-foreground">Tax</dt>
                <dd class="font-semibold tabular-nums">
                  {{ money(session.cart.tax_total) }}
                </dd>
              </div>
              <div
                class="flex justify-between border-t pt-3 text-2xl font-extrabold"
              >
                <dt>Total</dt>
                <dd class="tabular-nums">
                  {{ money(session.cart.grand_total) }}
                </dd>
              </div>
            </dl>
            <Alert
              v-if="message"
              class="mt-4"
              :variant="messageTone === 'error' ? 'destructive' : 'default'"
              ><AlertCircle class="h-4 w-4" aria-hidden="true" /><AlertTitle>{{
                messageTone === "error"
                  ? "Order needs attention"
                  : "Order updated"
              }}</AlertTitle
              ><AlertDescription>{{ message }}</AlertDescription></Alert
            >
            <Button
              class="mt-4 h-12 w-full min-w-0 text-sm sm:text-base"
              type="button"
              :disabled="working || !cart.length || !online"
              @click="openPayment"
              ><CreditCard class="h-5 w-5" aria-hidden="true" />
              <span class="min-w-0 truncate">{{
                working
                  ? "Updating…"
                  : `Take payment · ${money(session.cart.grand_total)}`
              }}</span></Button
            >
            <div class="mt-3 grid grid-cols-2 gap-3">
              <Button variant="outline" type="button" class="h-11 gap-2 px-2 text-xs sm:text-sm" :disabled="working || !cart.length || !online" @click="openHold"><Bookmark class="h-4 w-4" aria-hidden="true" /> Save order</Button>
              <Button variant="outline" type="button" class="h-11 gap-2 px-2 text-xs sm:text-sm" :disabled="working || !online" @click="openTransactions"><Printer class="h-4 w-4" aria-hidden="true" /> Receipts</Button>
            </div>
          </div>
        </aside>
      </div>

      <section
        v-else
        class="flex-1 p-4 sm:p-6"
        aria-labelledby="delivery-mode-heading"
      >
        <div
          class="flex flex-col justify-between gap-4 border-b pb-5 sm:flex-row sm:items-end"
        >
          <div>
            <h1
              id="delivery-mode-heading"
              class="text-2xl font-extrabold tracking-[-0.025em]"
            >
              Delivery orders
            </h1>
            <p class="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">
              Review delivery details and collect outstanding payments.
              Fulfillment progress remains controlled by the operations screens.
            </p>
          </div>
          <Button
            variant="outline"
            type="button"
            :disabled="deliveriesLoading"
            @click="loadDeliveries()"
            ><RefreshCw
              class="h-4 w-4"
              :class="deliveriesLoading ? 'animate-spin' : ''"
              aria-hidden="true"
            />
            Refresh orders</Button
          >
        </div>
        <StatePanel
          v-if="deliveriesLoading && !deliveryOrders.length"
          kind="loading"
          title="Loading deliveries"
          message="Retrieving confirmed delivery orders for this location."
        />
        <StatePanel
          v-else-if="deliveryError && !deliveryOrders.length"
          kind="error"
          title="Deliveries unavailable"
          :message="deliveryError"
          ><Button variant="outline" type="button" @click="loadDeliveries()"
            >Try again</Button
          ></StatePanel
        >
        <StatePanel
          v-else-if="!deliveryOrders.length"
          title="No active deliveries"
          message="Delivery orders appear here after counter checkout or storefront confirmation."
        />
        <div
          v-else
          class="mt-5 grid items-start gap-4 lg:grid-cols-2 2xl:grid-cols-3"
        >
          <article
            v-for="order in deliveryOrders"
            :key="order.public_id"
            class="rounded-xl border bg-card p-5 transition-[border-color,transform,box-shadow] duration-200 hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-md"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <strong>{{ order.number }}</strong
                  ><Badge variant="outline">{{ deliveryStage(order) }}</Badge
                  ><Badge
                    :variant="
                      order.payment_status === 'paid'
                        ? 'secondary'
                        : 'destructive'
                    "
                    >{{
                      order.payment_status === "paid" ? "Paid" : "Payment due"
                    }}</Badge
                  >
                </div>
                <p class="mt-1 text-xs text-muted-foreground">
                  {{ elapsed(order.placed_at) }}
                </p>
              </div>
              <strong class="shrink-0 text-lg tabular-nums">{{
                money(order.grand_total)
              }}</strong>
            </div>
            <div class="mt-4 grid gap-3 rounded-xl bg-muted/45 p-4 text-sm">
              <div class="flex items-start gap-3">
                <MapPin
                  class="mt-0.5 h-4 w-4 shrink-0 text-primary"
                  aria-hidden="true"
                /><span class="leading-5">{{ shippingAddress(order) }}</span>
              </div>
              <div class="flex items-start gap-3">
                <UserRound
                  class="mt-0.5 h-4 w-4 shrink-0 text-primary"
                  aria-hidden="true"
                /><span
                  ><strong class="block">{{ orderCustomerName(order) }}</strong
                  ><span class="mt-0.5 block text-xs text-muted-foreground">{{
                    order.customer_snapshot?.phone ||
                    order.customer_snapshot?.email ||
                    "No contact supplied"
                  }}</span></span
                >
              </div>
            </div>
            <ul class="mt-4 space-y-2">
              <li
                v-for="item in order.items"
                :key="item.public_id"
                class="flex justify-between gap-3 text-sm"
              >
                <span class="min-w-0 truncate"
                  ><strong>{{ item.quantity }}×</strong> {{ item.name }}</span
                ><span class="shrink-0 text-muted-foreground tabular-nums">{{
                  money(item.line_total)
                }}</span>
              </li>
            </ul>
            <Button
              v-if="order.payment_status !== 'paid'"
              class="mt-5 w-full"
              type="button"
              @click="openDeliveryPayment(order)"
              ><CreditCard class="h-4 w-4" aria-hidden="true" /> Collect
              {{ money(order.grand_total) }}</Button
            >
            <p
              v-else
              class="mt-5 flex items-center justify-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm font-bold text-emerald-700"
            >
              <Check class="h-4 w-4" aria-hidden="true" /> Payment recorded
            </p>
          </article>
        </div>
      </section>

      <Dialog :open="Boolean(configuring)" @update:open="handleConfiguringOpen">
        <DialogContent class="max-h-[92dvh] overflow-y-auto p-0 sm:max-w-xl">
          <form v-if="configuring" @submit.prevent="addConfigured">
            <ProductArtwork
              :name="configuring.name"
              :type="configuring.offering_type"
              :media="configuring.media"
            />
            <div class="p-6">
              <DialogHeader
                ><DialogTitle class="text-2xl font-extrabold">{{
                  configuring.name
                }}</DialogTitle
                ><DialogDescription
                  >Choose a variant and available options. The final price is
                  verified when added.</DialogDescription
                ></DialogHeader
              >
              <label
                v-if="activeVariants.length"
                class="field-label mt-5"
                for="terminal-variant"
                >Variant<NativeSelect
                  id="terminal-variant"
                  v-model="selectedVariantId"
                  class="mt-2"
                  required
                  ><option
                    v-for="variant in activeVariants"
                    :key="variant.public_id"
                    :value="variant.public_id"
                  >
                    {{ variant.name }} · {{ money(variant.price) }}
                  </option></NativeSelect
                ></label
              >
              <fieldset
                v-for="group in configuring.option_groups"
                :key="group.public_id"
                class="mt-5 border-t pt-4"
              >
                <legend class="font-extrabold">
                  {{ group.name }}
                  <span class="ml-2 text-xs font-normal text-muted-foreground"
                    >Choose {{ group.minimum_choices }}–{{
                      group.maximum_choices
                    }}</span
                  >
                </legend>
                <label
                  v-for="option in group.options.filter(
                    (item) => item.is_active,
                  )"
                  :key="option.public_id"
                  class="mt-3 flex cursor-pointer items-center justify-between gap-4 rounded-lg border px-3 py-2.5 text-sm"
                  ><span class="flex items-center gap-3"
                    ><NativeCheckbox
                      v-model="selectedOptionIds"
                      :value="option.public_id"
                      :disabled="
                        !selectedOptionIds.includes(option.public_id) &&
                        selectedCount(group) >= group.maximum_choices
                      "
                    />
                    {{ option.name }}</span
                  ><span class="font-semibold tabular-nums">{{
                    Number(option.price_delta)
                      ? `+${money(option.price_delta)}`
                      : "Included"
                  }}</span></label
                >
              </fieldset>
              <p
                v-if="configurationError"
                class="mt-4 text-sm font-semibold text-destructive"
                role="alert"
              >
                {{ configurationError }}
              </p>
              <DialogFooter class="mt-6"
                ><Button
                  variant="outline"
                  type="button"
                  @click="configuring = null"
                  >Cancel</Button
                ><Button
                  >Add to order · {{ money(configuredPrice) }}</Button
                ></DialogFooter
              >
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog v-model:open="paymentOpen">
        <DialogContent class="max-h-[92dvh] overflow-y-auto sm:max-w-lg">
          <form @submit.prevent="checkout">
            <DialogHeader
              ><DialogTitle class="text-2xl font-extrabold"
                >Complete payment</DialogTitle
              ><DialogDescription
                >Confirm how this order is being paid. The paired customer
                display will show the receipt immediately.</DialogDescription
              ></DialogHeader
            >
            <div class="mt-6 rounded-xl bg-secondary/60 p-4">
              <div class="flex items-center justify-between">
                <span class="text-sm font-semibold text-muted-foreground"
                  >Amount due</span
                ><strong class="text-3xl tabular-nums">{{
                  money(session.cart.grand_total)
                }}</strong>
              </div>
            </div>
            <fieldset class="mt-5">
              <legend class="field-label">Payment</legend>
              <div class="mt-2 grid grid-cols-3 gap-2">
                <Button
                  v-for="method in paymentMethods"
                  :key="method.value"
                  :variant="tenderType === method.value ? 'default' : 'outline'"
                  class="h-auto flex-col gap-1 py-3"
                  type="button"
                  :aria-pressed="tenderType === method.value"
                  @click="tenderType = method.value"
                  ><component
                    :is="method.icon"
                    class="h-5 w-5"
                    aria-hidden="true"
                  /><span>{{ method.label }}</span></Button
                >
              </div>
            </fieldset>
            <div v-if="tenderType === 'cash'" class="mt-5">
              <label class="field-label" for="amount-tendered"
                >Cash received</label
              ><Input
                id="amount-tendered"
                v-model="amountTendered"
                class="mt-2 text-lg font-bold tabular-nums"
                type="number"
                min="0"
                step="0.01"
                inputmode="decimal"
                required
              />
              <div class="mt-2 flex justify-between text-sm">
                <span class="text-muted-foreground">Change</span
                ><strong
                  class="tabular-nums"
                  :class="changeDue < 0 ? 'text-destructive' : ''"
                  >{{
                    changeDue < 0 ? "Insufficient cash" : money(changeDue)
                  }}</strong
                >
              </div>
            </div>
            <div class="mt-5 grid gap-4 sm:grid-cols-2">
              <label
                ><span class="field-label">Customer name</span
                ><Input
                  v-model.trim="customerName"
                  placeholder="Optional"
                  autocomplete="name" /></label
              ><label
                ><span class="field-label"
                  >Phone or email{{
                    fulfillmentType === "delivery" ? " (required)" : ""
                  }}</span
                ><Input
                  v-model.trim="customerContact"
                  :placeholder="
                    fulfillmentType === 'delivery'
                      ? 'Required for delivery updates'
                      : 'Optional'
                  "
                  autocomplete="email"
                  :required="fulfillmentType === 'delivery'"
              /></label>
            </div>
            <fieldset class="mt-5">
              <legend class="field-label">Fulfillment</legend>
              <div class="mt-2 grid grid-cols-3 gap-2">
                <Button
                  :variant="
                    fulfillmentType === 'pickup' ? 'default' : 'outline'
                  "
                  class="h-auto flex-col gap-1 py-3"
                  type="button"
                  :aria-pressed="fulfillmentType === 'pickup'"
                  @click="fulfillmentType = 'pickup'"
                  ><ShoppingBag class="h-4 w-4" aria-hidden="true" />
                  Pickup</Button
                ><Button
                  :variant="fulfillmentType === 'none' ? 'default' : 'outline'"
                  class="h-auto flex-col gap-1 py-3"
                  type="button"
                  :aria-pressed="fulfillmentType === 'none'"
                  @click="fulfillmentType = 'none'"
                  ><Store class="h-4 w-4" aria-hidden="true" /> In store</Button
                ><Button
                  :variant="
                    fulfillmentType === 'delivery' ? 'default' : 'outline'
                  "
                  class="h-auto flex-col gap-1 py-3"
                  type="button"
                  :aria-pressed="fulfillmentType === 'delivery'"
                  @click="fulfillmentType = 'delivery'"
                  ><Truck class="h-4 w-4" aria-hidden="true" /> Delivery</Button
                >
              </div>
            </fieldset>
            <fieldset
              v-if="fulfillmentType === 'delivery'"
              class="mt-5 rounded-xl border bg-muted/40 p-4"
            >
              <legend class="px-1 text-sm font-extrabold">
                Delivery details
              </legend>
              <div class="grid gap-4 sm:grid-cols-2">
                <label class="sm:col-span-2"
                  ><span class="field-label">Street address</span
                  ><Input
                    v-model.trim="deliveryAddress.line1"
                    autocomplete="street-address"
                    required /></label
                ><label
                  ><span class="field-label">City</span
                  ><Input
                    v-model.trim="deliveryAddress.city"
                    autocomplete="address-level2"
                    required /></label
                ><label
                  ><span class="field-label">Region</span
                  ><Input
                    v-model.trim="deliveryAddress.region"
                    autocomplete="address-level1"
                    required
                /></label>
              </div>
            </fieldset>
            <p
              v-if="paymentError"
              class="mt-4 text-sm font-semibold text-destructive"
              role="alert"
            >
              {{ paymentError }}
            </p>
            <DialogFooter class="mt-6"
              ><Button
                variant="outline"
                type="button"
                @click="paymentOpen = false"
                >Back</Button
              ><Button
                :disabled="working || (tenderType === 'cash' && changeDue < 0)"
                >{{ working ? "Completing…" : "Complete sale" }}</Button
              ></DialogFooter
            >
          </form>
        </DialogContent>
      </Dialog>

      <Dialog v-model:open="receiptOpen">
        <DialogContent class="sm:max-w-md"
          ><div v-if="receipt" class="print-receipt">
            <DialogHeader
              ><div
                class="mx-auto grid h-14 w-14 place-items-center rounded-full bg-emerald-100 text-emerald-700"
              >
                <Check class="h-7 w-7" aria-hidden="true" />
              </div>
              <DialogTitle class="mt-3 text-center text-2xl font-extrabold"
                >Sale complete</DialogTitle
              ><DialogDescription class="text-center"
                >{{ receipt.number }} is now visible on the paired customer
                display.</DialogDescription
              ></DialogHeader
            ><OrderTotals class="mt-6" :order="receipt" />
            <div
              v-if="tenderType === 'cash'"
              class="mt-4 flex justify-between rounded-xl bg-secondary p-4"
            >
              <span class="font-semibold text-muted-foreground"
                >Change given</span
              ><strong class="tabular-nums">{{ money(lastChange) }}</strong>
            </div>
            <div class="mt-5 grid grid-cols-2 gap-2 print:hidden">
              <Button
                v-if="receiptOptions.includes('print')"
                variant="outline"
                type="button"
                @click="printReceipt"
                ><Printer class="h-4 w-4" aria-hidden="true" /> Print
                receipt</Button
              ><Button
                v-if="receiptOptions.includes('digital')"
                variant="outline"
                type="button"
                @click="openDigitalReceipt(receipt)"
                ><Mail class="h-4 w-4" aria-hidden="true" /> Email
                receipt</Button
              >
            </div>
            <Button
              class="mt-3 w-full print:hidden"
              type="button"
              @click="startNextSale"
              >Start next order</Button
            >
          </div></DialogContent
        >
      </Dialog>

      <Dialog v-model:open="holdOpen"
        ><DialogContent class="sm:max-w-md"
          ><form @submit.prevent="holdCurrentSale">
            <DialogHeader
              ><div
                class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
              >
                <PauseCircle class="h-5 w-5" aria-hidden="true" />
              </div>
              <DialogTitle>Hold current sale</DialogTitle
              ><DialogDescription
                >Save this priced cart and clear the counter for the next
                customer.</DialogDescription
              ></DialogHeader
            ><label class="mt-6 block"
              ><span class="field-label">Reference</span
              ><Input
                v-model.trim="holdLabel"
                class="mt-2"
                maxlength="80"
                placeholder="Customer name or queue number" /></label
            ><DialogFooter class="mt-6"
              ><Button variant="outline" type="button" @click="holdOpen = false"
                >Cancel</Button
              ><Button :disabled="working">{{
                working ? "Holding…" : "Hold sale"
              }}</Button></DialogFooter
            >
          </form></DialogContent
        ></Dialog
      >

      <Dialog v-model:open="heldOpen"
        ><DialogContent class="max-h-[90dvh] overflow-y-auto sm:max-w-2xl"
          ><DialogHeader
            ><div
              class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
            >
              <PauseCircle class="h-5 w-5" aria-hidden="true" />
            </div>
            <DialogTitle>Held sales</DialogTitle
            ><DialogDescription
              >Resume a paused transaction when the current cart is
              empty.</DialogDescription
            ></DialogHeader
          >
          <div v-if="heldSales.length" class="mt-5 divide-y rounded-xl border">
            <article
              v-for="hold in heldSales"
              :key="hold.public_id"
              class="flex items-center justify-between gap-4 p-4"
            >
              <div>
                <strong>{{ hold.label }}</strong>
                <p class="mt-1 text-xs text-muted-foreground">
                  {{ hold.cart.items.length }} line items ·
                  {{ money(hold.cart.grand_total) }} ·
                  {{ elapsed(hold.held_at) }}
                </p>
              </div>
              <Button
                size="sm"
                type="button"
                :disabled="working || cart.length > 0"
                @click="resumeHeldSale(hold)"
                ><Play class="h-4 w-4" aria-hidden="true" /> Resume</Button
              >
            </article>
          </div>
          <StatePanel
            v-else
            title="No held sales"
            message="Paused transactions will appear here until they are resumed." /></DialogContent
      ></Dialog>

      <Dialog v-model:open="noteOpen"
        ><DialogContent class="sm:max-w-md"
          ><form @submit.prevent="saveItemNote">
            <DialogHeader
              ><div
                class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
              >
                <MessageSquareText class="h-5 w-5" aria-hidden="true" />
              </div>
              <DialogTitle>Item note</DialogTitle
              ><DialogDescription
                >Add a preparation, packing, customization, or customer note to
                this line item.</DialogDescription
              ></DialogHeader
            ><label class="mt-6 block"
              ><span class="field-label">Note</span
              ><Textarea
                v-model="itemNote"
                class="mt-2"
                maxlength="300"
                rows="4"
                placeholder="Example: gift wrap, no substitutions, call on arrival" /></label
            ><DialogFooter class="mt-6"
              ><Button variant="outline" type="button" @click="noteOpen = false"
                >Cancel</Button
              ><Button>Save note</Button></DialogFooter
            >
          </form></DialogContent
        ></Dialog
      >

      <Dialog v-model:open="voidOpen"
        ><DialogContent class="sm:max-w-md"
          ><form @submit.prevent="voidCurrentSale">
            <DialogHeader
              ><div
                class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-destructive/10 text-destructive"
              >
                <Trash2 class="h-5 w-5" aria-hidden="true" />
              </div>
              <DialogTitle>Void current sale</DialogTitle
              ><DialogDescription
                >This clears the live cart and records the reason in the audit
                trail. Strict counters also require manager
                approval.</DialogDescription
              ></DialogHeader
            ><label class="mt-6 block"
              ><span class="field-label">Reason</span
              ><Textarea
                v-model.trim="voidReason"
                class="mt-2"
                maxlength="300"
                rows="3"
                placeholder="Why is this sale being voided?"
                required
            /></label>
            <p
              v-if="voidError"
              class="mt-3 text-sm font-semibold text-destructive"
              role="alert"
            >
              {{ voidError }}
            </p>
            <DialogFooter class="mt-6"
              ><Button variant="outline" type="button" @click="voidOpen = false"
                >Keep sale</Button
              ><Button variant="destructive" :disabled="voidReason.length < 3"
                >Continue</Button
              ></DialogFooter
            >
          </form></DialogContent
        ></Dialog
      >

      <Dialog v-model:open="transactionsOpen"
        ><DialogContent class="max-h-[92dvh] overflow-y-auto sm:max-w-3xl"
          ><DialogHeader
            ><div
              class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
            >
              <History class="h-5 w-5" aria-hidden="true" />
            </div>
            <DialogTitle>Recent transactions</DialogTitle
            ><DialogDescription
              >Review this station’s last 30 sales, reprint or email a receipt,
              and request a controlled refund.</DialogDescription
            ></DialogHeader
          ><StatePanel
            v-if="transactionsLoading"
            kind="loading"
            title="Loading transactions"
            message="Retrieving this station’s sales."
          /><StatePanel
            v-else-if="!transactions.length"
            title="No transactions yet"
            message="Completed sales from this counter will appear here."
          />
          <div v-else class="mt-5 divide-y rounded-xl border">
            <article
              v-for="order in transactions"
              :key="order.public_id"
              class="p-4 transition-colors hover:bg-secondary/40"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <div class="flex items-center gap-2">
                    <strong>{{ order.number }}</strong
                    ><Badge
                      :variant="
                        order.payment_status === 'refunded'
                          ? 'outline'
                          : 'secondary'
                      "
                      >{{ order.payment_status }}</Badge
                    >
                  </div>
                  <p class="mt-1 text-xs text-muted-foreground">
                    {{ new Date(order.placed_at).toLocaleString("en-PH") }} ·
                    {{ order.payment_method }}
                  </p>
                </div>
                <strong class="tabular-nums">{{
                  money(order.grand_total)
                }}</strong>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  type="button"
                  @click="printTransaction(order)"
                  ><Printer class="h-3.5 w-3.5" aria-hidden="true" />
                  Reprint</Button
                ><Button
                  variant="outline"
                  size="sm"
                  type="button"
                  @click="openDigitalReceipt(order)"
                  ><Mail class="h-3.5 w-3.5" aria-hidden="true" /> Email</Button
                ><Button
                  v-if="order.payment_status === 'paid'"
                  variant="ghost"
                  size="sm"
                  class="text-destructive"
                  type="button"
                  @click="openRefund(order)"
                  ><RotateCcw class="h-3.5 w-3.5" aria-hidden="true" />
                  Refund</Button
                >
              </div>
            </article>
          </div></DialogContent
        ></Dialog
      >

      <Dialog v-model:open="digitalReceiptOpen"
        ><DialogContent class="sm:max-w-md"
          ><form @submit.prevent="sendDigitalReceipt">
            <DialogHeader
              ><div
                class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
              >
                <Mail class="h-5 w-5" aria-hidden="true" />
              </div>
              <DialogTitle>Email receipt</DialogTitle
              ><DialogDescription
                >Send {{ receiptTarget?.number }} to the customer without
                exposing the admin workspace.</DialogDescription
              ></DialogHeader
            ><label class="mt-6 block"
              ><span class="field-label">Customer email</span
              ><Input
                v-model.trim="receiptEmail"
                class="mt-2"
                type="email"
                autocomplete="email"
                required
            /></label>
            <p
              v-if="receiptActionError"
              class="mt-3 text-sm font-semibold text-destructive"
              role="alert"
            >
              {{ receiptActionError }}
            </p>
            <DialogFooter class="mt-6"
              ><Button
                variant="outline"
                type="button"
                @click="digitalReceiptOpen = false"
                >Cancel</Button
              ><Button :disabled="receiptActionWorking">{{
                receiptActionWorking ? "Sending…" : "Send receipt"
              }}</Button></DialogFooter
            >
          </form></DialogContent
        ></Dialog
      >

      <Dialog v-model:open="refundOpen"
        ><DialogContent class="sm:max-w-md"
          ><form @submit.prevent="requestRefundAuthorization">
            <DialogHeader
              ><div
                class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-destructive/10 text-destructive"
              >
                <RotateCcw class="h-5 w-5" aria-hidden="true" />
              </div>
              <DialogTitle>Record full refund</DialogTitle
              ><DialogDescription
                >Refund {{ refundTarget?.number }} for
                {{ money(refundTarget?.grand_total) }}. This records an
                in-person refund; return funds through the original external
                terminal or wallet separately.</DialogDescription
              ></DialogHeader
            ><label class="mt-6 block"
              ><span class="field-label">Reason</span
              ><Textarea
                v-model.trim="refundReason"
                class="mt-2"
                maxlength="300"
                rows="3"
                required
            /></label>
            <p
              v-if="refundError"
              class="mt-3 text-sm font-semibold text-destructive"
              role="alert"
            >
              {{ refundError }}
            </p>
            <DialogFooter class="mt-6"
              ><Button
                variant="outline"
                type="button"
                @click="refundOpen = false"
                >Cancel</Button
              ><Button variant="destructive" :disabled="refundReason.length < 3"
                >Manager approval</Button
              ></DialogFooter
            >
          </form></DialogContent
        ></Dialog
      >

      <Dialog v-model:open="strictAuthOpen">
        <DialogContent class="sm:max-w-md"
          ><form @submit.prevent="authorizeStrictAction">
            <DialogHeader
              ><div
                class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-amber-100 text-amber-800"
              >
                <ShieldCheck class="h-5 w-5" aria-hidden="true" />
              </div>
              <DialogTitle>Manager approval</DialogTitle
              ><DialogDescription
                >{{ strictPending?.label }} Strict register controls require an
                active owner, admin, or manager PIN.</DialogDescription
              ></DialogHeader
            ><label class="mt-6 block"
              ><span class="field-label">Six-digit manager PIN</span
              ><Input
                v-model="managerPin"
                class="mt-2 text-center text-xl font-extrabold tracking-[.35em] tabular-nums"
                type="password"
                inputmode="numeric"
                pattern="[0-9]{6}"
                maxlength="6"
                autocomplete="off"
                required
            /></label>
            <p
              v-if="strictError"
              class="mt-3 text-sm font-semibold text-destructive"
              role="alert"
            >
              {{ strictError }}
            </p>
            <DialogFooter class="mt-6"
              ><Button
                variant="outline"
                type="button"
                @click="cancelStrictAction"
                >Cancel</Button
              ><Button
                :disabled="strictAuthorizing || managerPin.length !== 6"
                >{{
                  strictAuthorizing ? "Checking…" : "Approve action"
                }}</Button
              ></DialogFooter
            >
          </form></DialogContent
        >
      </Dialog>

      <Dialog
        :open="Boolean(deliveryPaymentOrder)"
        @update:open="
          deliveryPaymentOrder = $event ? deliveryPaymentOrder : null
        "
      >
        <DialogContent class="sm:max-w-md"
          ><form
            v-if="deliveryPaymentOrder"
            @submit.prevent="collectDeliveryPayment"
          >
            <DialogHeader
              ><div
                class="mb-3 grid h-11 w-11 place-items-center rounded-xl bg-secondary text-primary"
              >
                <CreditCard class="h-5 w-5" aria-hidden="true" />
              </div>
              <DialogTitle>Collect delivery payment</DialogTitle
              ><DialogDescription
                >Record payment for {{ deliveryPaymentOrder.number }}. Card
                means the payment was completed on an external card
                terminal.</DialogDescription
              ></DialogHeader
            >
            <div
              class="mt-6 flex items-center justify-between rounded-xl bg-secondary/60 p-4"
            >
              <span class="text-sm font-semibold text-muted-foreground"
                >Amount due</span
              ><strong class="text-2xl tabular-nums">{{
                money(deliveryPaymentOrder.grand_total)
              }}</strong>
            </div>
            <fieldset class="mt-5">
              <legend class="field-label">Payment method</legend>
              <div class="mt-2 grid grid-cols-3 gap-2">
                <Button
                  v-for="method in deliveryPaymentMethods"
                  :key="method.value"
                  :variant="
                    deliveryTender === method.value ? 'default' : 'outline'
                  "
                  class="h-auto flex-col gap-1 py-3"
                  type="button"
                  :aria-pressed="deliveryTender === method.value"
                  @click="deliveryTender = method.value"
                  ><component
                    :is="method.icon"
                    class="h-5 w-5"
                    aria-hidden="true"
                  />{{ method.label }}</Button
                >
              </div>
            </fieldset>
            <div v-if="deliveryTender === 'cash'" class="mt-5">
              <label class="field-label" for="delivery-cash"
                >Cash received</label
              ><Input
                id="delivery-cash"
                v-model="deliveryCashReceived"
                class="mt-2 text-lg font-bold tabular-nums"
                type="number"
                min="0"
                step="0.01"
                inputmode="decimal"
                required
              />
              <div class="mt-2 flex justify-between text-sm">
                <span class="text-muted-foreground">Change</span
                ><strong
                  class="tabular-nums"
                  :class="deliveryChange < 0 ? 'text-destructive' : ''"
                  >{{
                    deliveryChange < 0
                      ? "Insufficient cash"
                      : money(deliveryChange)
                  }}</strong
                >
              </div>
            </div>
            <p
              v-if="deliveryPaymentError"
              class="mt-4 text-sm font-semibold text-destructive"
              role="alert"
            >
              {{ deliveryPaymentError }}
            </p>
            <DialogFooter class="mt-6"
              ><Button
                variant="outline"
                type="button"
                @click="deliveryPaymentOrder = null"
                >Cancel</Button
              ><Button
                :disabled="
                  deliveryPaymentWorking ||
                  (deliveryTender === 'cash' && deliveryChange < 0)
                "
                >{{
                  deliveryPaymentWorking ? "Recording…" : "Record payment"
                }}</Button
              ></DialogFooter
            >
          </form></DialogContent
        >
      </Dialog>
      <PosScannerDialog v-model:open="scannerOpen" @scan="scanCode" />
      <Dialog v-model:open="shortcutsOpen">
        <DialogContent class="sm:max-w-md">
          <DialogHeader><DialogTitle>Register shortcuts</DialogTitle><DialogDescription>Use these while the catalog is open. Product search also accepts USB and Bluetooth barcode readers.</DialogDescription></DialogHeader>
          <dl class="divide-y">
            <div v-for="shortcut in shortcuts" :key="shortcut.key" class="flex items-center justify-between gap-4 py-3 text-sm"><dt>{{ shortcut.label }}</dt><dd class="rounded-md border bg-muted px-2 py-1 font-semibold">{{ shortcut.key }}</dd></div>
          </dl>
        </DialogContent>
      </Dialog>
    </section>
  </main>
</template>

<script setup>
import {
  AlertCircle,
  Banknote,
  Bookmark,
  Check,
  ChevronDown,
  CreditCard,
  History,
  Keyboard,
  Landmark,
  LayoutGrid,
  List,
  Mail,
  MapPin,
  MessageSquareText,
  Minus,
  Package,
  PauseCircle,
  Play,
  Plus,
  Printer,
  RefreshCw,
  RotateCcw,
  ScanBarcode,
  ScanLine,
  Search,
  Settings2,
  ShieldCheck,
  ShoppingBag,
  ShoppingBasket,
  Star,
  Store,
  Tag,
  Trash2,
  Truck,
  Unplug,
  UserRound,
  WalletCards,
  X,
} from "lucide-vue-next";
import { toast } from "@/components/ui/toast";
import PosCatalogItem from "@/components/pos/PosCatalogItem.vue";
import PosScannerDialog from "@/components/pos/PosScannerDialog.vue";
import { usePosBarcodeReader } from "@/composables/usePosBarcodeReader";
import { findPosCodeMatches, matchesPosSearch } from "@/utils/posCatalog";

definePageMeta({ layout: "storefront" });
const config = useRuntimeConfig();
const state = ref("unpaired");
const code = ref("");
const token = ref("");
const identity = ref({});
const offerings = ref([]);
const discounts = ref([]);
const session = ref({
  cart: {
    items: [],
    subtotal: 0,
    discount_total: 0,
    tax_total: 0,
    grand_total: 0,
  },
  revision: 0,
});
const cart = ref([]);
const search = ref("");
const searchInput = ref(null);
const catalogView = ref("grid");
const showFavoritesOnly = ref(false);
const scannerOpen = ref(false);
const shortcutsOpen = ref(false);
const online = ref(true);
const scanFeedback = ref({ text: "", tone: "info" });
const activeCategory = ref("All");
const discountCode = ref("");
const configuring = ref(null);
const selectedOptionIds = ref([]);
const selectedVariantId = ref("");
const configurationError = ref("");
const working = ref(false);
const message = ref("");
const messageTone = ref("info");
const paymentOpen = ref(false);
const paymentError = ref("");
const tenderType = ref("cash");
const amountTendered = ref("");
const customerName = ref("");
const customerContact = ref("");
const fulfillmentType = ref("pickup");
const deliveryAddress = reactive({
  line1: "",
  city: "",
  region: "",
  country: "PH",
});
const receipt = ref(null);
const receiptOpen = ref(false);
const lastChange = ref(0);
const currentTime = ref("");
let clockTimer;
const registerMode = ref("sale");
const stationControls = ref({ strict_mode: false });
const deliveryOrders = ref([]);
const deliveriesLoading = ref(false);
const deliveryError = ref("");
let deliveryPoller;
const strictAuthOpen = ref(false);
const strictPending = shallowRef(null);
const managerPin = ref("");
const strictError = ref("");
const strictAuthorizing = ref(false);
const deliveryPaymentOrder = ref(null);
const deliveryTender = ref("cash");
const deliveryCashReceived = ref("");
const deliveryPaymentError = ref("");
const deliveryPaymentWorking = ref(false);
const holdOpen = ref(false);
const heldOpen = ref(false);
const holdLabel = ref("");
const heldSales = ref([]);
const noteOpen = ref(false);
const itemNote = ref("");
const noteIndex = ref(-1);
const voidOpen = ref(false);
const voidReason = ref("");
const voidError = ref("");
const transactionsOpen = ref(false);
const transactionsLoading = ref(false);
const transactions = ref([]);
const digitalReceiptOpen = ref(false);
const receiptTarget = ref(null);
const receiptEmail = ref("");
const receiptActionError = ref("");
const receiptActionWorking = ref(false);
const refundOpen = ref(false);
const refundTarget = ref(null);
const refundReason = ref("");
const refundError = ref("");
const shortcuts = [
  { key: "F2 / Ctrl K", label: "Focus product search" },
  { key: "F4", label: "Open barcode scanner" },
  { key: "F8", label: "Take payment" },
  { key: "Ctrl Shift H", label: "Hold current sale" },
];

usePosBarcodeReader({
  enabled: () => state.value === "ready" && registerMode.value === "sale" && online.value && !working.value,
  onScan: scanCode,
});

const categories = computed(() => [
  "All",
  ...new Set(
    offerings.value.map(
      (item) => item.category_name || typeLabel(item.offering_type),
    ),
  ),
]);
const filtered = computed(() =>
  offerings.value.filter((item) => {
    const query = search.value.trim().toLowerCase();
    const category = item.category_name || typeLabel(item.offering_type);
    return (
      (activeCategory.value === "All" || category === activeCategory.value) &&
      (!showFavoritesOnly.value || (stationControls.value.favorite_offering_ids || []).includes(item.public_id)) &&
      matchesPosSearch(item, query)
    );
  }),
);
const favoriteOfferings = computed(() =>
  offerings.value.filter((item) =>
    (stationControls.value.favorite_offering_ids || []).includes(
      item.public_id,
    ),
  ),
);
const cartCount = computed(() =>
  cart.value.reduce((total, item) => total + Number(item.quantity || 0), 0),
);
const initials = computed(() =>
  (identity.value.display_name || "PC")
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase(),
);
const activeVariants = computed(
  () => configuring.value?.variants?.filter((item) => item.is_active) || [],
);
const configuredPrice = computed(() => {
  if (!configuring.value) return 0;
  const variant = activeVariants.value.find(
    (item) => item.public_id === selectedVariantId.value,
  );
  const options = configuring.value.option_groups
    .flatMap((group) => group.options)
    .filter((option) => selectedOptionIds.value.includes(option.public_id));
  return (
    Number(variant?.price ?? configuring.value.base_price) +
    options.reduce(
      (total, option) => total + Number(option.price_delta || 0),
      0,
    )
  );
});
const changeDue = computed(
  () =>
    Number(amountTendered.value || 0) -
    Number(session.value.cart.grand_total || 0),
);
const strictMode = computed(() => Boolean(stationControls.value.strict_mode));
const deliveryChange = computed(
  () =>
    Number(deliveryCashReceived.value || 0) -
    Number(deliveryPaymentOrder.value?.grand_total || 0),
);
const allPaymentMethods = [
  { value: "cash", label: "Cash", icon: Banknote },
  { value: "card", label: "Card", icon: CreditCard },
  { value: "gcash", label: "GCash", icon: WalletCards },
  { value: "maya", label: "Maya", icon: WalletCards },
  { value: "pay_later", label: "Pay later", icon: Landmark },
];
const paymentMethods = computed(() =>
  allPaymentMethods.filter((method) =>
    (
      stationControls.value.payment_methods ||
      allPaymentMethods.map((item) => item.value)
    ).includes(method.value),
  ),
);
const receiptOptions = computed(
  () => stationControls.value.receipt_options || ["print", "digital"],
);
const deliveryPaymentMethods = [
  { value: "cash", label: "Cash", icon: Banknote },
  { value: "card", label: "Card", icon: CreditCard },
  { value: "gcash", label: "GCash", icon: WalletCards },
  { value: "maya", label: "Maya", icon: WalletCards },
];
const deviceHeaders = () => ({ "X-Device-Token": token.value });

onMounted(() => {
  token.value = localStorage.getItem("pixelcore_pos_token") || "";
  online.value = navigator.onLine;
  try {
    const savedView = localStorage.getItem("pixelcore_pos_catalog_view");
    if (["grid", "list"].includes(savedView)) catalogView.value = savedView;
  } catch {}
  updateClock();
  clockTimer = window.setInterval(updateClock, 30000);
  window.addEventListener("online", handleOnline);
  window.addEventListener("offline", handleOffline);
  window.addEventListener("keydown", handleShortcut);
  if (token.value) {
    load();
    startDeliveryPolling();
  }
});
onBeforeUnmount(() => {
  window.clearInterval(clockTimer);
  window.clearInterval(deliveryPoller);
  window.removeEventListener("online", handleOnline);
  window.removeEventListener("offline", handleOffline);
  window.removeEventListener("keydown", handleShortcut);
});

async function pair() {
  if (working.value || code.value.length !== 8) return;
  working.value = true;
  message.value = "";
  try {
    const response = await $fetch("devices/pair/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      body: { pairing_code: code.value, device_type: "pos" },
    });
    if (response.device.device_type !== "pos")
      throw new Error("This setup code belongs to another device type.");
    token.value = response.device_token;
    localStorage.setItem("pixelcore_pos_token", token.value);
    await load();
    startDeliveryPolling();
  } catch (error) {
    message.value =
      error?.data?.error?.message || error.message || "Pairing failed.";
  } finally {
    working.value = false;
  }
}
async function load() {
  scannerOpen.value = false;
  scanFeedback.value = { text: "", tone: "info" };
  state.value = "loading";
  message.value = "";
  try {
    const response = await $fetch("devices/pos/session/", {
      baseURL: config.public.apiBaseUrl,
      headers: deviceHeaders(),
    });
    identity.value = response.business;
    offerings.value = response.offerings || [];
    discounts.value = response.discounts || [];
    session.value = response.session;
    stationControls.value = response.station_controls || { strict_mode: false };
    heldSales.value = response.session.held_sales || [];
    cart.value = (response.session.cart.items || []).map((item) => ({ ...item }));
    discountCode.value = response.session.cart.discount_code || "";
    state.value = "ready";
    if (
      !paymentMethods.value.some((method) => method.value === tenderType.value)
    )
      tenderType.value = paymentMethods.value[0]?.value || "cash";
  } catch (error) {
    message.value =
      error?.response?.status === 403
        ? "This POS station is not paired. Its setup may have expired or been revoked."
        : "PixelCore could not reconnect to this station.";
    state.value = "error";
  }
}
async function beginAdd(offering, preferredVariantId = "") {
  if (working.value || !online.value) return false;
  configuring.value = offering;
  configurationError.value = "";
  selectedVariantId.value =
    offering.variants.find((item) => item.is_active && item.public_id === preferredVariantId)?.public_id ||
    offering.variants.find((item) => item.is_active)?.public_id || "";
  selectedOptionIds.value = offering.option_groups.flatMap((group) =>
    group.minimum_choices
      ? group.options
          .filter((item) => item.is_active)
          .slice(0, group.minimum_choices)
          .map((item) => item.public_id)
      : [],
  );
  if (
    !offering.option_groups.length &&
    (!offering.variants.some((item) => item.is_active) || preferredVariantId)
  )
    return await addConfigured();
  return null;
}
async function addExactMatch() {
  await scanCode(search.value, true);
}
function handleSearchEnter(event) {
  if (event.isComposing) return;
  event.preventDefault();
  addExactMatch();
}
async function scanCode(value, allowName = false) {
  if (working.value || state.value !== "ready" || !online.value) return;
  const codeValue = String(value || "").trim().slice(0, 120);
  if (!codeValue) return;
  let matches = findPosCodeMatches(offerings.value, codeValue);
  if (!matches.length && allowName) {
    matches = offerings.value.filter((offering) => offering.name.toLowerCase() === codeValue.toLowerCase()).map((offering) => ({ offering, variantId: "" }));
  }
  registerMode.value = "sale";
  activeCategory.value = "All";
  showFavoritesOnly.value = false;
  if (matches.length !== 1) {
    search.value = codeValue;
    scanFeedback.value = { tone: "error", text: matches.length ? "More than one item uses this code. Choose the correct product and variant." : `No item matches “${codeValue}”. Check the code or search by name.` };
    await focusSearch();
    return;
  }
  const { offering, variantId } = matches[0];
  search.value = "";
  const added = await beginAdd(offering, variantId);
  scanFeedback.value = added === null
    ? { tone: "info", text: `Choose options for ${offering.name} to finish adding it.` }
    : added
      ? { tone: "success", text: `Added ${offering.name}${variantId ? ' · Matched variant' : ''}` }
      : { tone: "error", text: `${offering.name} was not added. Review the order message and try again.` };
  if (added) await focusSearch();
}
async function focusSearch() {
  registerMode.value = "sale";
  await nextTick();
  searchInput.value?.$el?.focus?.();
}
function clearSearch() {
  search.value = "";
  scanFeedback.value = { text: "", tone: "info" };
  focusSearch();
}
function setCatalogView(view) {
  catalogView.value = view;
  try { localStorage.setItem("pixelcore_pos_catalog_view", view); } catch {}
}
function handleConfiguringOpen(open) {
  if (!open) configuring.value = null;
}
function selectedCount(group) {
  return group.options.filter((option) =>
    selectedOptionIds.value.includes(option.public_id),
  ).length;
}
async function addConfigured() {
  if (working.value || !online.value || !configuring.value) return false;
  const offering = configuring.value;
  const invalidGroup = offering.option_groups.find(
    (group) =>
      selectedCount(group) < group.minimum_choices ||
      selectedCount(group) > group.maximum_choices,
  );
  if (invalidGroup) {
    configurationError.value = `Choose between ${invalidGroup.minimum_choices} and ${invalidGroup.maximum_choices} options for ${invalidGroup.name}.`;
    return false;
  }
  const options = offering.option_groups
    .flatMap((group) => group.options)
    .filter((option) => selectedOptionIds.value.includes(option.public_id));
  const selectedIds = options.map((option) => option.public_id).sort();
  const existing = cart.value.find((item) =>
    item.offering_public_id === offering.public_id &&
    (item.variant_public_id || "") === (selectedVariantId.value || "") &&
    !item.note &&
    JSON.stringify([...(item.option_public_ids || item.options?.map((option) => option.public_id) || [])].sort()) === JSON.stringify(selectedIds),
  );
  if (existing) existing.quantity = Number(existing.quantity) + 1;
  else cart.value.push({
    offering_public_id: offering.public_id,
    variant_public_id: selectedVariantId.value || null,
    name: offering.name,
    image_url: offering.media?.[0]?.url || "",
    quantity: 1,
    option_public_ids: options.map((option) => option.public_id),
    options,
  });
  configuring.value = null;
  const added = await syncCart();
  if (added) toast({ title: "Added to order", description: offering.name });
  return added;
}
async function changeQuantity(index, delta, authorizationToken = "") {
  cart.value[index].quantity = Math.max(1, cart.value[index].quantity + delta);
  await syncCart(authorizationToken);
}
async function removeItem(index, authorizationToken = "") {
  cart.value.splice(index, 1);
  await syncCart(authorizationToken);
}
async function clearCart(authorizationToken = "") {
  cart.value = [];
  discountCode.value = "";
  receipt.value = null;
  if (await syncCart(authorizationToken))
    toast({ title: "Sale voided", description: "The current cart was cleared." });
}
function requestQuantityChange(index, delta) {
  if (working.value || !online.value) return;
  if (delta < 0 && cart.value[index].quantity <= 1) return;
  if (delta >= 0) {
    changeQuantity(index, delta);
    return;
  }
  requireStrictAuthorization(
    "void_items",
    `Reduce ${cart.value[index].name} by one?`,
    (authorizationToken) => changeQuantity(index, delta, authorizationToken),
  );
}
function requestRemoveItem(index) {
  if (working.value || !online.value) return;
  requireStrictAuthorization(
    "void_items",
    `Remove ${cart.value[index].name} from this sale?`,
    (authorizationToken) => removeItem(index, authorizationToken),
  );
}
function requestVoidSale() {
  requireStrictAuthorization(
    "void_items",
    "Void the entire current sale?",
    (authorizationToken) => clearCart(authorizationToken),
  );
}
function requestPromotion() {
  const applyingNewCode =
    discountCode.value &&
    discountCode.value !== (session.value.cart.discount_code || "");
  if (!applyingNewCode) {
    syncCart();
    return;
  }
  requireStrictAuthorization(
    "discount",
    `Apply promotion code ${discountCode.value}?`,
    (authorizationToken) => syncCart(authorizationToken),
  );
}
function payloadItems() {
  return cart.value.map((item) => ({
    offering_public_id: item.offering_public_id,
    variant_public_id: item.variant_public_id || undefined,
    quantity: item.quantity,
    option_public_ids:
      item.option_public_ids ||
      item.options?.map((option) => option.public_id) ||
      [],
    note: item.note || "",
  }));
}
async function syncCart(authorizationToken = "") {
  working.value = true;
  message.value = "";
  try {
    session.value = await $fetch("devices/pos/session/", {
      baseURL: config.public.apiBaseUrl,
      method: "PUT",
      headers: {
        ...deviceHeaders(),
        ...(authorizationToken
          ? { "X-POS-Authorization": authorizationToken }
          : {}),
      },
      body: {
        if_revision: session.value.revision,
        items: payloadItems(),
        discount_code: discountCode.value,
      },
    });
    cart.value = (session.value.cart.items || []).map((item) => ({ ...item }));
    messageTone.value = "info";
    return true;
  } catch (error) {
    if (error?.response?.status === 409 && error?.data?.error?.code === "POS_SESSION_CONFLICT") {
      await load();
      message.value = "This order changed on another screen. The latest server version has been restored.";
      messageTone.value = "error";
    } else if (
      error?.response?.status === 403 &&
      error?.data?.error?.code === "DEVICE_ACCESS_DENIED"
    ) {
      message.value =
        error?.data?.error?.message || "This POS station is not paired.";
      state.value = "error";
    } else {
      message.value =
        error?.data?.error?.message || "The order could not be repriced.";
      messageTone.value = "error";
      cart.value = (session.value.cart.items || []).map((item) => ({ ...item }));
      discountCode.value = session.value.cart.discount_code || "";
    }
    return false;
  } finally {
    working.value = false;
  }
}
function openPayment() {
  if (working.value || !online.value || !cart.value.length) return;
  paymentError.value = "";
  amountTendered.value =
    tenderType.value === "cash"
      ? String(session.value.cart.grand_total || "")
      : "";
  paymentOpen.value = true;
}
async function checkout() {
  if (working.value || !online.value || !cart.value.length) return;
  if (tenderType.value === "cash" && changeDue.value < 0) {
    paymentError.value = "Cash received must cover the amount due.";
    return;
  }
  working.value = true;
  paymentError.value = "";
  const names = customerName.value.trim().split(/\s+/);
  const contactIsEmail = customerContact.value.includes("@");
  try {
    receipt.value = await $fetch("devices/pos/checkout/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      headers: { ...deviceHeaders(), "Idempotency-Key": crypto.randomUUID() },
      body: {
        if_revision: session.value.revision,
        items: payloadItems(),
        discount_code: discountCode.value,
        payment_method:
          tenderType.value === "pay_later" ? "cod" : tenderType.value,
        payment_status: tenderType.value === "pay_later" ? "unpaid" : "paid",
        fulfillment_type: fulfillmentType.value,
        shipping_address:
          fulfillmentType.value === "delivery" ? deliveryAddress : {},
        customer: {
          first_name: names.shift() || "",
          last_name: names.join(" "),
          email: contactIsEmail ? customerContact.value : "",
          phone: contactIsEmail ? "" : customerContact.value,
        },
      },
    });
    lastChange.value =
      tenderType.value === "cash" ? Math.max(0, changeDue.value) : 0;
    session.value = receipt.value.pos_session;
    cart.value = [];
    discountCode.value = "";
    paymentOpen.value = false;
    receiptOpen.value = true;
    await loadDeliveries(true);
    toast({
      title: "Sale completed",
      description: `${receipt.value.number} is ready.`,
    });
  } catch (error) {
    if (!handleDeviceAccessError(error))
      paymentError.value =
        error?.data?.error?.message ||
        "Payment could not be completed. The order remains open.";
  } finally {
    working.value = false;
  }
}
function startNextSale() {
  receiptOpen.value = false;
  receipt.value = null;
  customerName.value = "";
  customerContact.value = "";
  amountTendered.value = "";
  tenderType.value = "cash";
  fulfillmentType.value = "pickup";
  Object.assign(deliveryAddress, {
    line1: "",
    city: "",
    region: "",
    country: "PH",
  });
}
function openItemNote(index) {
  noteIndex.value = index;
  itemNote.value = cart.value[index]?.note || "";
  noteOpen.value = true;
}
async function saveItemNote() {
  if (noteIndex.value < 0 || !cart.value[noteIndex.value]) return;
  cart.value[noteIndex.value].note = itemNote.value.trim();
  noteOpen.value = false;
  await syncCart();
  toast({
    title: "Item note saved",
    description: "The note will follow this item into fulfillment.",
  });
}
function openHold() {
  if (working.value || !online.value || !cart.value.length) return;
  holdLabel.value = customerName.value || "";
  holdOpen.value = true;
}
async function holdCurrentSale() {
  if (working.value || !online.value || !cart.value.length) return;
  working.value = true;
  try {
    session.value = await $fetch("devices/pos/holds/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      headers: deviceHeaders(),
      body: { label: holdLabel.value },
    });
    cart.value = [];
    heldSales.value = session.value.held_sales || [];
    holdOpen.value = false;
    holdLabel.value = "";
    customerName.value = "";
    customerContact.value = "";
    discountCode.value = "";
    toast({
      title: "Sale held",
      description: "The counter is ready for another customer.",
    });
  } catch (error) {
    toast({
      title: "Sale not held",
      description: error?.data?.error?.message || "Try again.",
      variant: "destructive",
    });
  } finally {
    working.value = false;
  }
}
function openHeldSales() {
  heldOpen.value = true;
}
async function resumeHeldSale(hold) {
  working.value = true;
  try {
    session.value = await $fetch(
      `devices/pos/holds/${hold.public_id}/resume/`,
      {
        baseURL: config.public.apiBaseUrl,
        method: "POST",
        headers: deviceHeaders(),
      },
    );
    cart.value = (session.value.cart.items || []).map((item) => ({ ...item }));
    heldSales.value = session.value.held_sales || [];
    discountCode.value = session.value.cart.discount_code || "";
    heldOpen.value = false;
    registerMode.value = "sale";
    toast({ title: "Sale resumed", description: hold.label });
  } catch (error) {
    toast({
      title: "Sale not resumed",
      description: error?.data?.error?.message || "Try again.",
      variant: "destructive",
    });
  } finally {
    working.value = false;
  }
}
function openVoid() {
  voidReason.value = "";
  voidError.value = "";
  voidOpen.value = true;
}
function voidCurrentSale() {
  if (voidReason.value.trim().length < 3) return;
  voidOpen.value = false;
  requireStrictAuthorization(
    "void_sale",
    "Void this entire sale and record the supplied reason?",
    (authorizationToken) => executeVoid(authorizationToken),
  );
}
async function executeVoid(authorizationToken = "") {
  working.value = true;
  try {
    session.value = await $fetch("devices/pos/void/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      headers: {
        ...deviceHeaders(),
        ...(authorizationToken
          ? { "X-POS-Authorization": authorizationToken }
          : {}),
      },
      body: { reason: voidReason.value },
    });
    cart.value = [];
    discountCode.value = "";
    voidReason.value = "";
    toast({
      title: "Sale voided",
      description: "The cart was cleared and the reason was recorded.",
    });
  } catch (error) {
    voidError.value =
      error?.data?.error?.message || "The sale could not be voided.";
    voidOpen.value = true;
  } finally {
    working.value = false;
  }
}
async function openTransactions() {
  transactionsOpen.value = true;
  transactionsLoading.value = true;
  try {
    const response = await $fetch("devices/pos/transactions/", {
      baseURL: config.public.apiBaseUrl,
      headers: deviceHeaders(),
    });
    transactions.value = response.orders || [];
  } catch (error) {
    toast({
      title: "Transactions unavailable",
      description: error?.data?.error?.message || "Try again.",
      variant: "destructive",
    });
  } finally {
    transactionsLoading.value = false;
  }
}
function printReceipt() {
  window.print();
}
async function printTransaction(order) {
  receipt.value = order;
  receiptOpen.value = true;
  await nextTick();
  window.print();
}
function openDigitalReceipt(order) {
  receiptTarget.value = order;
  receiptEmail.value = order.customer_snapshot?.email || "";
  receiptActionError.value = "";
  digitalReceiptOpen.value = true;
}
async function sendDigitalReceipt() {
  if (!receiptTarget.value) return;
  receiptActionWorking.value = true;
  receiptActionError.value = "";
  try {
    await $fetch(
      `devices/pos/transactions/${receiptTarget.value.public_id}/receipt/`,
      {
        baseURL: config.public.apiBaseUrl,
        method: "POST",
        headers: deviceHeaders(),
        body: { email: receiptEmail.value },
      },
    );
    digitalReceiptOpen.value = false;
    toast({
      title: "Receipt queued",
      description: `A digital receipt will be sent to ${receiptEmail.value}.`,
    });
  } catch (error) {
    receiptActionError.value =
      error?.data?.error?.message || "The receipt could not be sent.";
  } finally {
    receiptActionWorking.value = false;
  }
}
function openRefund(order) {
  refundTarget.value = order;
  refundReason.value = "";
  refundError.value = "";
  refundOpen.value = true;
}
function requestRefundAuthorization() {
  if (!refundTarget.value || refundReason.value.trim().length < 3) return;
  refundOpen.value = false;
  strictPending.value = {
    action: "refund",
    label: `Record a full refund for ${refundTarget.value.number}?`,
    operation: (authorizationToken) => executeRefund(authorizationToken),
  };
  managerPin.value = "";
  strictError.value = "";
  strictAuthOpen.value = true;
}
async function executeRefund(authorizationToken) {
  receiptActionWorking.value = true;
  try {
    const updated = await $fetch(
      `devices/pos/transactions/${refundTarget.value.public_id}/refund/`,
      {
        baseURL: config.public.apiBaseUrl,
        method: "POST",
        headers: {
          ...deviceHeaders(),
          "X-POS-Authorization": authorizationToken,
        },
        body: { reason: refundReason.value },
      },
    );
    Object.assign(refundTarget.value, updated);
    toast({
      title: "Refund recorded",
      description: `${updated.number} is marked refunded. Return external funds separately when applicable.`,
    });
  } catch (error) {
    refundError.value =
      error?.data?.error?.message || "The refund could not be recorded.";
    refundOpen.value = true;
  } finally {
    receiptActionWorking.value = false;
  }
}
function unpair() {
  scannerOpen.value = false;
  shortcutsOpen.value = false;
  window.clearInterval(deliveryPoller);
  localStorage.removeItem("pixelcore_pos_token");
  token.value = "";
  deliveryOrders.value = [];
  state.value = "unpaired";
}
function handleOnline() {
  online.value = true;
  if (token.value) load();
}
function handleOffline() {
  online.value = false;
  scannerOpen.value = false;
  scanFeedback.value = { tone: "error", text: "Offline. Reconnect before adding items or taking payment." };
}
function handleDeviceAccessError(error) {
  if (
    error?.response?.status !== 403 ||
    error?.data?.error?.code !== "DEVICE_ACCESS_DENIED"
  )
    return false;
  paymentOpen.value = false;
  scannerOpen.value = false;
  deliveryPaymentOrder.value = null;
  transactionsOpen.value = false;
  message.value =
    error?.data?.error?.message || "This POS station is not paired.";
  state.value = "error";
  return true;
}
function handleShortcut(event) {
  if (event.isComposing || event.repeat || state.value !== "ready" || working.value || document.querySelector('[role="dialog"][data-state="open"], [role="menu"][data-state="open"]')) return;
  const key = event.key.toLowerCase();
  if (key === "f2" || ((event.ctrlKey || event.metaKey) && key === "k")) {
    event.preventDefault();
    focusSearch();
  } else if (key === "f4" && online.value) {
    event.preventDefault();
    registerMode.value = "sale";
    scannerOpen.value = true;
  } else if (key === "f8" && registerMode.value === "sale") {
    event.preventDefault();
    openPayment();
  } else if ((event.ctrlKey || event.metaKey) && event.shiftKey && key === "h" && registerMode.value === "sale") {
    event.preventDefault();
    openHold();
  }
}
function updateClock() {
  currentTime.value = new Intl.DateTimeFormat("en-PH", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date());
}
function itemDetails(item) {
  return [
    item.variant_name,
    ...(item.options || []).map((option) => option.name),
  ]
    .filter(Boolean)
    .join(" · ");
}
function typeLabel(type) {
  return (
    { physical: "Products", digital: "Digital", service: "Services" }[type] ||
    "Other"
  );
}
function startDeliveryPolling() {
  window.clearInterval(deliveryPoller);
  loadDeliveries(true);
  deliveryPoller = window.setInterval(() => loadDeliveries(true), 10000);
}
function openDeliveries() {
  registerMode.value = "deliveries";
  loadDeliveries();
}
async function loadDeliveries(quiet = false) {
  if (!token.value) return;
  if (!quiet) deliveriesLoading.value = true;
  deliveryError.value = "";
  try {
    const response = await $fetch("devices/orders/queue/", {
      baseURL: config.public.apiBaseUrl,
      headers: deviceHeaders(),
    });
    deliveryOrders.value = response.orders || [];
  } catch (error) {
    if (!handleDeviceAccessError(error))
      deliveryError.value =
        error?.data?.error?.message || "Delivery orders could not be loaded.";
  } finally {
    deliveriesLoading.value = false;
  }
}
function requireStrictAuthorization(action, label, operation) {
  if (!strictMode.value) {
    operation("");
    return;
  }
  strictPending.value = { action, label, operation };
  managerPin.value = "";
  strictError.value = "";
  strictAuthOpen.value = true;
}
function cancelStrictAction() {
  strictAuthOpen.value = false;
  strictPending.value = null;
  managerPin.value = "";
  strictError.value = "";
}
async function authorizeStrictAction() {
  if (!strictPending.value || strictAuthorizing.value) return;
  strictAuthorizing.value = true;
  strictError.value = "";
  try {
    const approval = await $fetch("devices/pos/authorize/", {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      headers: deviceHeaders(),
      body: { action: strictPending.value.action, pin: managerPin.value },
    });
    const pending = strictPending.value;
    strictAuthOpen.value = false;
    strictPending.value = null;
    managerPin.value = "";
    await pending.operation(approval.authorization_token);
    toast({
      title: "Manager approval recorded",
      description: `Approved by ${approval.approved_by}.`,
    });
  } catch (error) {
    strictError.value =
      error?.data?.error?.message || "Manager approval could not be verified.";
  } finally {
    strictAuthorizing.value = false;
  }
}
function openDeliveryPayment(order) {
  deliveryPaymentOrder.value = order;
  deliveryTender.value = "cash";
  deliveryCashReceived.value = String(order.grand_total || "");
  deliveryPaymentError.value = "";
}
async function collectDeliveryPayment() {
  if (!deliveryPaymentOrder.value || deliveryPaymentWorking.value) return;
  if (deliveryTender.value === "cash" && deliveryChange.value < 0) {
    deliveryPaymentError.value = "Cash received must cover the amount due.";
    return;
  }
  deliveryPaymentWorking.value = true;
  deliveryPaymentError.value = "";
  const order = deliveryPaymentOrder.value;
  try {
    const updated = await $fetch(`devices/orders/${order.public_id}/payment/`, {
      baseURL: config.public.apiBaseUrl,
      method: "POST",
      headers: { ...deviceHeaders(), "Idempotency-Key": crypto.randomUUID() },
      body: { payment_method: deliveryTender.value },
    });
    Object.assign(order, updated);
    deliveryPaymentOrder.value = null;
    toast({
      title: "Delivery payment recorded",
      description: `${order.number} is now paid.`,
    });
    await loadDeliveries(true);
  } catch (error) {
    deliveryPaymentError.value =
      error?.data?.error?.message || "The payment was not recorded. Try again.";
  } finally {
    deliveryPaymentWorking.value = false;
  }
}
function deliveryStage(order) {
  const status = order.fulfillments?.[0]?.status;
  return status === "ready"
    ? "Ready to dispatch"
    : order.status === "processing"
      ? "In progress"
      : "Incoming";
}
function shippingAddress(order) {
  const address = order.shipping_snapshot || {};
  return (
    [address.line1, address.city, address.region].filter(Boolean).join(", ") ||
    "Delivery address not supplied"
  );
}
function orderCustomerName(order) {
  return (
    [order.customer_snapshot?.first_name, order.customer_snapshot?.last_name]
      .filter(Boolean)
      .join(" ") || "Customer"
  );
}
function discountLabel(discount) {
  return discount.value_type === "percentage"
    ? `${Number(discount.value)}%`
    : money(discount.value);
}
function elapsed(value) {
  const minutes = Math.max(
    0,
    Math.floor((Date.now() - new Date(value).getTime()) / 60000),
  );
  return minutes < 1
    ? "Just now"
    : minutes < 60
      ? `${minutes} min ago`
      : `${Math.floor(minutes / 60)}h ${minutes % 60}m ago`;
}
const money = (value) =>
  new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: identity.value.currency || "PHP",
  }).format(Number(value || 0));
</script>

<style>
.pos-catalog-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.pos-terminal button {
  column-gap: 0.5rem;
}

@media (min-width: 640px) {
  .pos-catalog-grid {
    grid-template-columns: repeat(auto-fill, minmax(min(100%, 13rem), 1fr));
  }
}

@media print {
  body * {
    visibility: hidden !important;
  }
  .print-receipt,
  .print-receipt * {
    visibility: visible !important;
  }
  .print-receipt {
    position: fixed;
    inset: 0;
    width: 100%;
    padding: 24px;
    background: white;
    color: black;
  }
}
</style>
