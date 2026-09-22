<template>
  <section class="workspace-page space-y-5">
    <ButtonLink :to="backPath" variant="ghost" size="sm" class="w-fit -ml-2">
      <ArrowLeft class="h-4 w-4" aria-hidden="true" />
      Back to {{ resourceMeta.label.toLowerCase() }}
    </ButtonLink>

    <StatePanel
      v-if="loading"
      kind="loading"
      title="Loading operations record"
      message="Retrieving the latest operational details."
    />
    <StatePanel v-else-if="error" kind="error" title="Record unavailable" :message="error">
      <Button type="button" variant="outline" @click="loadRecord">Try again</Button>
    </StatePanel>

    <template v-else-if="record">
      <PageHeader :title="recordTitle" :description="resourceMeta.description">
        <template #actions>
          <StatusPill v-if="recordStatus" :value="recordStatus" />
          <Button type="button" variant="outline" @click="editOpen = true">
            <Pencil class="h-4 w-4" aria-hidden="true" />
            Edit details
          </Button>
          <Button
            v-if="resource === 'invoices'"
            type="button"
            variant="outline"
            :disabled="pdfLoading"
            @click="openInvoicePdf"
          >
            <Loader2 v-if="pdfLoading" class="h-4 w-4 animate-spin" aria-hidden="true" />
            <FileDown v-else class="h-4 w-4" aria-hidden="true" />
            {{ pdfLoading ? 'Opening…' : 'View PDF' }}
          </Button>
          <Button v-if="actionMeta" type="button" @click="actionOpen = true">
            <component :is="actionMeta.icon" class="h-4 w-4" aria-hidden="true" />
            {{ actionMeta.label }}
          </Button>
        </template>
      </PageHeader>

      <section
        v-if="deadlineMeta"
        class="flex items-center gap-3 rounded-xl border px-4 py-3"
        :class="deadlineMeta.tone"
      >
        <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-background/70">
          <CalendarClock class="h-4 w-4" aria-hidden="true" />
        </span>
        <div class="min-w-0 sm:flex sm:items-baseline sm:gap-2">
          <p class="font-semibold tabular-nums">{{ deadlineMeta.relative }}</p>
          <p class="truncate text-xs opacity-80">{{ deadlineMeta.label }} · {{ deadlineMeta.formattedDate }}</p>
        </div>
      </section>

      <div
        v-if="record.attention_status && record.attention_status !== 'clear'"
        class="flex flex-col gap-3 rounded-xl border border-amber-300/70 bg-amber-50 p-4 text-amber-950 sm:flex-row sm:items-center sm:justify-between dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100"
      >
        <div>
          <p class="font-semibold">This record needs attention</p>
          <p class="mt-1 text-sm opacity-80">{{ record.attention_message }}</p>
        </div>
        <OperationsAttentionBadge :status="record.attention_status" :message="record.attention_message" />
      </div>

      <dl class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4">
        <div v-for="metric in metrics" :key="metric.label" class="border-b p-4 sm:border-r xl:border-b-0 last:border-r-0">
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0">
              <dt class="text-xs text-muted-foreground">{{ metric.label }}</dt>
              <dd class="mt-1 text-xl font-semibold tabular-nums">{{ metric.value }}</dd>
            </div>
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-muted text-primary">
              <component :is="metric.icon" class="h-4 w-4" aria-hidden="true" />
            </span>
          </div>
          <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
        </div>
      </dl>

      <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <section class="overflow-hidden rounded-xl border bg-card">
          <div class="border-b px-5 py-4">
            <h2 class="font-semibold">{{ primarySectionTitle }}</h2>
            <p class="mt-1 text-sm text-muted-foreground">{{ primarySectionDescription }}</p>
          </div>

          <div v-if="resource === 'suppliers'" class="flex flex-col gap-4 border-b p-5 sm:flex-row sm:items-center">
            <Button
              v-if="record.image_url"
              type="button"
              variant="ghost"
              class="h-auto w-fit shrink-0 rounded-xl p-0 focus-visible:ring-offset-4"
              :aria-label="`Preview ${record.name} supplier image`"
              @click="supplierImageOpen = true"
            >
              <Avatar class="h-28 w-28 rounded-xl border bg-muted">
                <AvatarImage :src="record.image_url" :alt="record.name" class="object-cover" />
                <AvatarFallback class="rounded-xl text-xl font-semibold">{{ initials(record.name) }}</AvatarFallback>
              </Avatar>
            </Button>
            <Avatar v-else class="h-28 w-28 rounded-xl border bg-muted">
              <AvatarFallback class="rounded-xl text-xl font-semibold">{{ initials(record.name) }}</AvatarFallback>
            </Avatar>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-lg font-semibold">{{ record.name }}</h3>
                <StatusPill :value="record.is_active ? 'active' : 'inactive'" />
              </div>
              <p class="mt-1 text-sm text-muted-foreground">{{ humanize(record.category) }}<span v-if="record.code"> · {{ record.code }}</span></p>
              <p class="mt-2 text-sm">{{ record.contact_name || 'No contact person assigned' }}</p>
            </div>
          </div>

          <div v-if="resource === 'purchase-orders'" class="border-b bg-muted/20 px-5 py-5 sm:px-6">
            <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div class="flex items-start gap-3">
                <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-background text-primary ring-1 ring-border">
                  <PackageCheck class="h-5 w-5" aria-hidden="true" />
                </span>
                <div>
                  <p class="font-semibold">{{ receivingStatus }}</p>
                  <p class="mt-1 text-sm text-muted-foreground">{{ receivingDescription }}</p>
                </div>
              </div>
              <div class="text-left sm:text-right">
                <span class="text-3xl font-semibold tabular-nums">{{ quantity(record.receiving_progress) }}%</span>
                <span class="mt-1 block text-xs text-muted-foreground">received</span>
              </div>
            </div>
            <Progress :model-value="Number(record.receiving_progress || 0)" class="mt-4 h-2.5" />
            <dl class="mt-5 grid divide-y border-y sm:grid-cols-3 sm:divide-x sm:divide-y-0">
              <div class="flex items-center justify-between gap-4 py-3 sm:block sm:px-4 sm:first:pl-0">
                <dt class="flex items-center gap-2 text-xs text-muted-foreground"><Boxes class="h-4 w-4" aria-hidden="true" />Ordered</dt>
                <dd class="font-semibold tabular-nums sm:mt-1">{{ quantity(sumLines('quantity_ordered')) }}</dd>
              </div>
              <div class="flex items-center justify-between gap-4 py-3 sm:block sm:px-4">
                <dt class="flex items-center gap-2 text-xs text-muted-foreground"><PackageCheck class="h-4 w-4" aria-hidden="true" />Received</dt>
                <dd class="font-semibold tabular-nums sm:mt-1">{{ quantity(sumLines('quantity_received')) }}</dd>
              </div>
              <div class="flex items-center justify-between gap-4 py-3 sm:block sm:px-4 sm:last:pr-0">
                <dt class="flex items-center gap-2 text-xs text-muted-foreground"><Clock3 class="h-4 w-4" aria-hidden="true" />Remaining</dt>
                <dd class="font-semibold tabular-nums sm:mt-1">{{ quantity(record.remaining_units) }}</dd>
              </div>
            </dl>
          </div>

          <div v-if="documentLines.length" class="overflow-x-auto">
            <Table class="min-w-[46rem]">
              <TableHeader>
                <TableRow>
                  <TableHead>Item</TableHead>
                  <TableHead class="text-right">Quantity</TableHead>
                  <TableHead class="text-right">Unit amount</TableHead>
                  <TableHead v-if="resource === 'purchase-orders'" class="text-right">Received</TableHead>
                  <TableHead v-else class="text-right">Tax</TableHead>
                  <TableHead class="text-right">Line total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="(line, index) in documentLines" :key="line.public_id">
                  <TableCell class="py-4">
                    <div class="flex min-w-72 items-start gap-3.5">
                      <Avatar class="h-11 w-11 shrink-0 rounded-xl border bg-muted">
                        <AvatarImage
                          v-if="line.image_url"
                          :src="line.image_url"
                          :alt="`${line.description} image`"
                          class="object-cover"
                        />
                        <AvatarFallback class="rounded-xl text-xs font-semibold">
                          {{ lineItemAbbreviation(line) }}
                        </AvatarFallback>
                      </Avatar>
                      <div class="min-w-0">
                        <span class="block truncate font-medium">{{ line.description }}</span>
                        <span class="mt-1 block truncate text-xs text-muted-foreground">
                          {{ lineItemDetail(line, index) }}
                        </span>
                        <ButtonLink
                          v-if="resource === 'purchase-orders' && line.inventory_balance_public_id"
                          :to="`/workspace/operate/inventory/${line.inventory_balance_public_id}`"
                          variant="link"
                          size="sm"
                          class="mt-1 h-auto p-0 text-xs"
                        >
                          Open inventory balance
                          <ArrowUpRight class="h-3.5 w-3.5" aria-hidden="true" />
                        </ButtonLink>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell class="py-4 text-right tabular-nums">{{ quantity(lineQuantity(line)) }}</TableCell>
                  <TableCell class="py-4 text-right tabular-nums">{{ money(lineUnitAmount(line)) }}</TableCell>
                  <TableCell class="py-4 text-right tabular-nums">
                    {{ resource === 'purchase-orders' ? quantity(line.quantity_received) : `${quantity(line.tax_rate)}%` }}
                  </TableCell>
                  <TableCell class="py-4 text-right font-semibold tabular-nums">{{ money(lineTotal(line)) }}</TableCell>
                </TableRow>
              </TableBody>
              <TableFooter>
                <TableRow>
                  <TableCell :colspan="4" class="text-right font-medium">Document total</TableCell>
                  <TableCell class="text-right text-base font-semibold tabular-nums">{{ money(documentTotal) }}</TableCell>
                </TableRow>
              </TableFooter>
            </Table>
          </div>

          <dl v-else class="grid gap-px bg-border sm:grid-cols-2">
            <div v-for="field in primaryFields" :key="field.label" class="bg-card px-5 py-4">
              <dt class="text-xs text-muted-foreground">{{ field.label }}</dt>
              <dd class="mt-1 whitespace-pre-line text-sm font-medium leading-6">{{ field.value || 'Not provided' }}</dd>
            </div>
          </dl>
        </section>

        <aside class="space-y-5">
          <section v-if="resource === 'expenses'" class="rounded-xl border bg-card p-5">
            <div class="flex items-start gap-3">
              <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-muted text-primary">
                <Paperclip class="h-5 w-5" aria-hidden="true" />
              </span>
              <div class="min-w-0 flex-1">
                <h2 class="font-semibold">Receipt evidence</h2>
                <p class="mt-1 truncate text-sm text-muted-foreground">
                  {{ record.receipt_name || 'No receipt attached' }}
                </p>
              </div>
            </div>
            <Button v-if="record.receipt_url" as-child variant="outline" class="mt-4 w-full">
              <a :href="record.receipt_url" target="_blank" rel="noopener noreferrer">
                <FileText class="h-4 w-4" aria-hidden="true" />
                View receipt
              </a>
            </Button>
            <p v-else class="mt-4 text-xs leading-5 text-muted-foreground">Use Edit details to attach an image or PDF receipt to this expense.</p>
          </section>

          <section class="rounded-xl border bg-card p-5">
            <h2 class="font-semibold">Record details</h2>
            <dl class="mt-4 divide-y text-sm">
              <div v-for="field in secondaryFields" :key="field.label" class="py-3 first:pt-0 last:pb-0">
                <dt class="text-xs text-muted-foreground">{{ field.label }}</dt>
                <dd class="mt-1 break-words font-medium">{{ field.value || 'Not provided' }}</dd>
              </div>
            </dl>
          </section>

          <section v-if="record.notes" class="rounded-xl border bg-card p-5">
            <h2 class="font-semibold">Internal notes</h2>
            <p class="mt-3 whitespace-pre-line text-sm leading-6 text-muted-foreground">{{ record.notes }}</p>
          </section>

          <section v-if="connections.length" class="overflow-hidden rounded-xl border bg-card">
            <div class="border-b px-5 py-4">
              <h2 class="font-semibold">Connected records</h2>
              <p class="mt-1 text-sm text-muted-foreground">How this record participates in Operations.</p>
            </div>
            <ButtonLink
              v-for="connection in connections"
              :key="connection.label"
              :to="connection.to"
              variant="ghost"
              class="h-auto w-full justify-between gap-4 rounded-none border-b px-5 py-3 text-left last:border-b-0"
            >
              <span class="flex min-w-0 items-center gap-3">
                <Avatar class="h-10 w-10 shrink-0 rounded-lg border bg-muted">
                  <AvatarImage v-if="connection.imageUrl" :src="connection.imageUrl" :alt="`${connection.label} image`" class="object-cover" />
                  <AvatarFallback class="rounded-lg text-xs font-semibold">{{ connection.abbreviation || initials(connection.label) }}</AvatarFallback>
                </Avatar>
                <span class="min-w-0">
                  <strong class="block truncate text-sm">{{ connection.label }}</strong>
                  <span class="mt-1 block text-xs font-normal text-muted-foreground">{{ connection.detail }}</span>
                </span>
              </span>
              <span class="flex items-center gap-2 font-semibold tabular-nums">{{ connection.value }}<ChevronRight class="h-4 w-4" aria-hidden="true" /></span>
            </ButtonLink>
          </section>

          <Alert v-if="resource === 'invoices' || resource === 'quotations'">
            <Info class="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Operational document</AlertTitle>
            <AlertDescription>
              This record supports internal operations and is not represented as a BIR-authorized invoice or receipt.
            </AlertDescription>
          </Alert>
        </aside>
      </div>

      <section v-if="resource === 'suppliers'" class="overflow-hidden rounded-xl border bg-card">
        <div class="flex flex-col gap-3 border-b px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="font-semibold">Products from this supplier</h2>
            <p class="mt-1 text-sm text-muted-foreground">Supplier-specific SKUs, costs, minimum quantities, and replenishment lead times.</p>
          </div>
          <Button type="button" variant="outline" @click="supplierProductOpen = true">
            <Plus class="h-4 w-4" aria-hidden="true" />
            Add product
          </Button>
        </div>
        <StatePanel
          v-if="!record.products?.length"
          title="No supplied products yet"
          message="Connect the exact catalog variants this supplier can provide. Purchase orders also create this connection automatically."
        />
        <div v-else class="overflow-x-auto">
          <Table class="min-w-[46rem]">
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>Supplier SKU</TableHead>
                <TableHead class="text-right">Latest cost</TableHead>
                <TableHead class="text-right">Minimum</TableHead>
                <TableHead class="text-right">Lead time</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="product in record.products" :key="product.public_id">
                <TableCell class="py-4">
                  <span class="flex min-w-64 items-center gap-3.5">
                    <Avatar class="h-11 w-11 shrink-0 rounded-xl border bg-muted">
                      <AvatarImage v-if="product.image_url" :src="product.image_url" :alt="`${product.offering_name} image`" class="object-cover" />
                      <AvatarFallback class="rounded-xl text-sm font-semibold">{{ initials(product.offering_name) }}</AvatarFallback>
                    </Avatar>
                    <span class="min-w-0">
                      <span class="block truncate font-medium">{{ product.offering_name }}</span>
                      <span class="mt-1 block truncate text-xs text-muted-foreground">{{ product.variant_name }}<span v-if="product.sku"> · {{ product.sku }}</span></span>
                    </span>
                  </span>
                </TableCell>
                <TableCell class="py-4">{{ product.supplier_sku || 'Not provided' }}</TableCell>
                <TableCell class="py-4 text-right font-medium tabular-nums">{{ money(product.last_unit_cost) }}</TableCell>
                <TableCell class="py-4 text-right tabular-nums">{{ quantity(product.minimum_order_quantity) }}</TableCell>
                <TableCell class="py-4 text-right tabular-nums">{{ product.lead_time_days }} days</TableCell>
                <TableCell class="py-4"><StatusPill :value="product.is_active ? 'active' : 'inactive'" /></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </section>

      <section v-if="resource === 'inventory'" class="overflow-hidden rounded-xl border bg-card">
        <div class="border-b px-5 py-4">
          <h2 class="font-semibold">Stock movement history</h2>
          <p class="mt-1 text-sm text-muted-foreground">Every receipt and adjustment that changed this balance.</p>
        </div>
        <StatePanel v-if="!stockMovements.length" title="No stock movements yet" message="Receiving a purchase order or recording an adjustment will create the first audit entry." />
        <Table v-else>
          <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>Movement</TableHead><TableHead>Reason or reference</TableHead><TableHead class="text-right">Quantity</TableHead></TableRow></TableHeader>
          <TableBody>
            <TableRow v-for="movement in stockMovements" :key="movement.public_id">
              <TableCell>{{ formatDateTime(movement.created_at) }}</TableCell>
              <TableCell>{{ humanize(movement.movement_type) }}</TableCell>
              <TableCell>{{ movement.note || [movement.reference_type, movement.reference_id].filter(Boolean).join(' · ') || 'No reason recorded' }}</TableCell>
              <TableCell class="text-right font-semibold tabular-nums" :class="Number(movement.quantity_delta) < 0 ? 'text-destructive' : 'text-emerald-700'">{{ Number(movement.quantity_delta) > 0 ? '+' : '' }}{{ quantity(movement.quantity_delta) }}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </section>

      <section v-if="resource === 'invoices'" class="overflow-hidden rounded-xl border bg-card">
        <div class="border-b px-5 py-4">
          <h2 class="font-semibold">Payment history</h2>
          <p class="mt-1 text-sm text-muted-foreground">Allocations recorded against this invoice.</p>
        </div>
        <StatePanel
          v-if="!record.payment_allocations?.length"
          title="No payments recorded"
          message="Use Record payment when funds are received."
        />
        <Table v-else>
          <TableHeader>
            <TableRow>
              <TableHead>Received</TableHead>
              <TableHead>Reference</TableHead>
              <TableHead class="text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="payment in record.payment_allocations" :key="payment.public_id">
              <TableCell>{{ formatDateTime(payment.received_at) }}</TableCell>
              <TableCell>{{ payment.reference || 'No reference' }}</TableCell>
              <TableCell class="text-right font-semibold tabular-nums">{{ money(payment.amount) }}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </section>
    </template>

    <Dialog v-model:open="supplierImageOpen">
      <DialogContent class="overflow-hidden p-0 sm:max-w-3xl">
        <DialogHeader class="border-b px-6 py-5 pr-14">
          <DialogTitle>{{ record?.name || 'Supplier' }} image</DialogTitle>
          <DialogDescription>Supplier identity image used in Operations records.</DialogDescription>
        </DialogHeader>
        <div class="grid max-h-[70dvh] place-items-center bg-muted/40 p-5">
          <img
            v-if="record?.image_url"
            :src="record.image_url"
            :alt="`${record.name} supplier image`"
            class="max-h-[60dvh] max-w-full rounded-xl object-contain"
          />
        </div>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="actionOpen">
      <DialogContent class="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{{ actionMeta?.dialogTitle }}</DialogTitle>
          <DialogDescription>{{ actionMeta?.description }}</DialogDescription>
        </DialogHeader>

        <form id="operations-action-form" class="space-y-4" @submit.prevent="submitAction">
          <template v-if="resource === 'inventory'">
            <div class="grid gap-2">
              <Label for="quantity-delta">Quantity change</Label>
              <Input id="quantity-delta" v-model="actionForm.quantity_delta" type="number" step="0.001" />
              <p class="text-xs text-muted-foreground">Use a negative number to record damaged, missing, or removed stock.</p>
            </div>
            <div class="grid gap-2">
              <Label for="adjustment-note">Reason</Label>
              <Textarea id="adjustment-note" v-model.trim="actionForm.note" rows="3" placeholder="Physical count, correction, or damaged stock" />
            </div>
          </template>

          <template v-else-if="resource === 'purchase-orders'">
            <div v-for="line in receivableLines" :key="line.public_id" class="grid gap-2 rounded-xl border p-4">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <Label :for="`receipt-${line.public_id}`">{{ line.description }}</Label>
                  <p class="mt-1 text-xs text-muted-foreground">
                    {{ quantity(line.quantity_received) }} of {{ quantity(line.quantity_ordered) }} received
                  </p>
                </div>
                <span class="text-sm font-semibold tabular-nums">{{ quantity(remainingQuantity(line)) }} remaining</span>
              </div>
              <Input
                :id="`receipt-${line.public_id}`"
                v-model="actionForm.receipts[line.public_id]"
                type="number"
                min="0"
                :max="remainingQuantity(line)"
                step="0.001"
              />
            </div>
          </template>

          <template v-else-if="resource === 'invoices'">
            <div class="grid gap-2">
              <Label for="payment-amount">Amount received</Label>
              <Input id="payment-amount" v-model="actionForm.amount" type="number" min="0.01" :max="record?.balance_due" step="0.01" />
            </div>
            <div class="grid gap-2">
              <Label for="payment-reference">Payment reference</Label>
              <Input id="payment-reference" v-model.trim="actionForm.reference" placeholder="Bank transfer, receipt, or transaction number" />
            </div>
          </template>

          <p v-if="actionError" class="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive" role="alert">
            {{ actionError }}
          </p>
        </form>

        <DialogFooter>
          <Button type="button" variant="outline" @click="actionOpen = false">Cancel</Button>
          <Button form="operations-action-form" type="submit" :disabled="actionSaving || !canSubmitAction">
            <Loader2 v-if="actionSaving" class="h-4 w-4 animate-spin" aria-hidden="true" />
            {{ actionSaving ? 'Saving…' : actionMeta?.submitLabel }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <OperationsEditDialog
      v-model:open="editOpen"
      :resource="resource"
      :business-id="businessId"
      :record="record"
      :suppliers="references.suppliers"
      :locations="references.locations"
      :categories="references.categories"
      @saved="handleSaved"
    />

    <SupplierProductDialog
      v-if="resource === 'suppliers'"
      v-model:open="supplierProductOpen"
      :business-id="businessId"
      :supplier-id="recordId"
      :variants="references.variants"
      :default-lead-time="Number(record?.lead_time_days || 0)"
      @created="handleSupplierProductCreated"
    />
  </section>
</template>

<script setup>
import {
  AlertTriangle,
  ArrowLeft,
  ArrowUpRight,
  Boxes,
  CalendarClock,
  CalendarDays,
  ChevronRight,
  CircleDollarSign,
  Clock3,
  FileDown,
  FileText,
  HandCoins,
  Info,
  ListChecks,
  Loader2,
  LockKeyhole,
  PackageCheck,
  PackageSearch,
  Paperclip,
  Pencil,
  Plus,
  ReceiptText,
  ShoppingCart,
  Tags,
  Warehouse,
} from 'lucide-vue-next'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import ButtonLink from '@/components/ui/button-link/ButtonLink.vue'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Table, TableBody, TableCell, TableFooter, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import OperationsAttentionBadge from '@/components/operations/OperationsAttentionBadge.vue'
import OperationsEditDialog from '@/components/operations/OperationsEditDialog.vue'
import SupplierProductDialog from '@/components/operations/SupplierProductDialog.vue'

const route = useRoute()
const business = useBusinessStore()
const { apiFetch } = useApiClient()

const resources = {
  inventory: { label: 'Inventory', description: 'Stock position, availability, and reorder threshold for this location.' },
  suppliers: { label: 'Suppliers', description: 'Supplier identity, purchasing contact, and internal relationship notes.' },
  'purchase-orders': { label: 'Purchase orders', description: 'Supplier commitment, receiving progress, and expected stock.' },
  quotations: { label: 'Quotations', description: 'Customer quote, commercial terms, and conversion status.' },
  invoices: { label: 'Invoices', description: 'Invoice balance, customer details, line items, and payment allocations.' },
  expenses: { label: 'Expenses', description: 'Recorded operating cost, category, supplier, and payment evidence.' },
}

const resource = computed(() => String(route.params.resource || ''))
const recordId = computed(() => String(route.params.recordId || ''))
const resourceMeta = computed(() => resources[resource.value] || { label: 'Operations', description: 'Operational record.' })
const businessId = computed(() => business.activeBusiness?.public_id || '')
const backPath = computed(() => `/workspace/operate?view=${resource.value}`)
const record = ref(null)
const loading = ref(true)
const error = ref('')
const actionOpen = ref(false)
const editOpen = ref(false)
const supplierProductOpen = ref(false)
const supplierImageOpen = ref(false)
const actionSaving = ref(false)
const actionError = ref('')
const pdfLoading = ref(false)
const stockMovements = ref([])
const actionForm = reactive({ quantity_delta: '0', note: '', receipts: {}, amount: '', reference: '' })
const references = reactive({ suppliers: [], locations: [], categories: [], variants: [] })

const recordTitle = computed(() => {
  if (!record.value) return resourceMeta.value.label
  return record.value.number || record.value.name || record.value.offering_name || record.value.description || resourceMeta.value.label
})
useHead(() => ({ title: `${recordTitle.value} | Operations | PixelCore` }))
const recordStatus = computed(() => {
  if (!record.value) return ''
  if (resource.value === 'suppliers') return record.value.is_active ? 'active' : 'inactive'
  if (resource.value === 'inventory') return Number(record.value.available) <= Number(record.value.low_stock_threshold) ? 'low stock' : 'in stock'
  return record.value.status || ''
})
const actionMeta = computed(() => {
  if (!record.value) return null
  if (resource.value === 'inventory') return { label: 'Adjust stock', dialogTitle: 'Adjust stock balance', description: 'Record a quantity change with a clear reason for the audit trail.', submitLabel: 'Record adjustment', icon: Boxes }
  if (resource.value === 'purchase-orders' && receivableLines.value.length) return { label: 'Receive stock', dialogTitle: 'Receive purchase order', description: 'Enter only the quantities received in this delivery.', submitLabel: 'Receive stock', icon: PackageCheck }
  if (resource.value === 'invoices' && Number(record.value.balance_due) > 0 && record.value.status !== 'void') return { label: 'Record payment', dialogTitle: 'Record invoice payment', description: 'Allocate a received amount against this invoice.', submitLabel: 'Record payment', icon: ReceiptText }
  return null
})

const deadlineMeta = computed(() => {
  if (!record.value) return null
  const configuration = {
    'purchase-orders': { value: record.value.expected_at, label: 'Expected delivery' },
    quotations: { value: record.value.expires_at, label: 'Quote expiry' },
    invoices: { value: record.value.due_at, label: 'Payment due' },
  }[resource.value]
  if (!configuration?.value) return null

  const completedLabel = {
    'purchase-orders': record.value.status === 'received' ? 'Received in full' : record.value.status === 'cancelled' ? 'Order cancelled' : '',
    quotations: ['accepted', 'converted'].includes(record.value.status) ? humanize(record.value.status) : '',
    invoices: record.value.status === 'paid' ? 'Paid in full' : record.value.status === 'void' ? 'Invoice void' : '',
  }[resource.value]
  if (completedLabel) {
    return {
      ...configuration,
      relative: completedLabel,
      formattedDate: formatDate(configuration.value),
      tone: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-950 dark:text-emerald-100',
    }
  }

  const days = daysUntil(configuration.value)
  const relative = days < 0
    ? `${Math.abs(days)} day${Math.abs(days) === 1 ? '' : 's'} overdue`
    : days === 0
      ? 'Due today'
      : `${days} day${days === 1 ? '' : 's'} left`
  const tone = days < 0
    ? 'border-destructive/30 bg-destructive/10 text-destructive'
    : days <= 3
      ? 'border-amber-500/35 bg-amber-500/10 text-amber-950 dark:text-amber-100'
      : 'border-primary/20 bg-primary/5 text-foreground'
  return { ...configuration, relative, formattedDate: formatDate(configuration.value), tone }
})

const receivingStatus = computed(() => {
  const progress = Number(record.value?.receiving_progress || 0)
  if (progress >= 100) return 'Receiving complete'
  if (progress > 0) return 'Partially received'
  return 'Awaiting first delivery'
})

const receivingDescription = computed(() => {
  if (record.value?.received_at) return `Completed ${formatDateTime(record.value.received_at)}`
  const remaining = quantity(record.value?.remaining_units)
  return `${remaining} unit${Number(record.value?.remaining_units || 0) === 1 ? '' : 's'} still expected at ${record.value?.location_name || 'the receiving location'}.`
})

const metrics = computed(() => {
  if (!record.value) return []
  if (resource.value === 'inventory') return [
    metric('On hand', quantity(record.value.on_hand), 'Recorded physical quantity', Boxes),
    metric('Reserved', quantity(record.value.reserved), 'Committed to active orders', LockKeyhole),
    metric('Available', quantity(record.value.available), 'Ready for sale or use', PackageCheck),
    metric('Low-stock threshold', quantity(record.value.low_stock_threshold), 'Reorder attention point', AlertTriangle),
  ]
  if (resource.value === 'suppliers') return [
    metric('Supplied products', record.value.product_count || 0, 'Connected catalog variants', PackageSearch),
    metric('Purchase orders', record.value.purchase_order_count || 0, `${record.value.open_purchase_order_count || 0} currently open`, ShoppingCart),
    metric('Preferred source for', record.value.preferred_inventory_count || 0, 'Inventory balances', Warehouse),
    metric('Typical lead time', record.value.lead_time_days ? `${record.value.lead_time_days} days` : 'Not set', 'Replenishment planning', Clock3),
  ]
  if (resource.value === 'purchase-orders') return [
    metric('Line items', documentLines.value.length, 'Products on this order', ListChecks),
    metric('Ordered units', quantity(sumLines('quantity_ordered')), 'Total units committed', Boxes),
    metric('Received units', quantity(sumLines('quantity_received')), 'Units added to stock', PackageCheck),
    metric('Order value', money(documentLines.value.reduce((sum, line) => sum + lineTotal(line), 0)), 'At recorded unit cost', CircleDollarSign),
  ]
  if (resource.value === 'quotations') return [
    metric('Subtotal', money(record.value.subtotal), 'Before recorded tax', CircleDollarSign),
    metric('Tax', money(record.value.tax_total), 'Included tax amount', ReceiptText),
    metric('Quote total', money(record.value.grand_total), record.value.currency, HandCoins),
    metric('Line items', documentLines.value.length, 'Products or services quoted', ListChecks),
  ]
  if (resource.value === 'invoices') return [
    metric('Invoice total', money(record.value.grand_total), record.value.currency, FileText),
    metric('Paid', money(record.value.amount_paid), 'Allocated payments', HandCoins),
    metric('Balance due', money(record.value.balance_due), 'Outstanding amount', CircleDollarSign),
    metric('Payments', record.value.payment_allocations?.length || 0, 'Recorded allocations', ListChecks),
  ]
  return [
    metric('Amount', money(record.value.amount), 'Recorded cost', CircleDollarSign),
    metric('Tax', money(record.value.tax_amount), 'Recorded tax portion', ReceiptText),
    metric('Category', record.value.category_name || 'Uncategorized', 'Expense classification', Tags),
    metric('Incurred', formatDate(record.value.incurred_at), 'Operating date', CalendarDays),
  ]
})

const documentLines = computed(() => ['purchase-orders', 'quotations', 'invoices'].includes(resource.value) ? record.value?.lines || [] : [])
const documentTotal = computed(() => {
  if (!record.value) return 0
  if (resource.value === 'purchase-orders') {
    return documentLines.value.reduce((sum, line) => sum + lineTotal(line), 0)
  }
  return Number(record.value.grand_total || 0)
})
const receivableLines = computed(() => documentLines.value.filter(line => remainingQuantity(line) > 0))
const primarySectionTitle = computed(() => documentLines.value.length ? 'Line items' : resource.value === 'suppliers' ? 'Supplier profile' : resource.value === 'inventory' ? 'Stock identity' : 'Expense information')
const primarySectionDescription = computed(() => documentLines.value.length ? 'Quantities and values captured on this document.' : resource.value === 'suppliers' ? 'Contact and organization details used throughout purchasing.' : resource.value === 'inventory' ? 'The product variant and location represented by this balance.' : 'Classification and payment details for this cost.')

const primaryFields = computed(() => {
  if (!record.value) return []
  if (resource.value === 'inventory') return [
    field('Product', record.value.offering_name), field('Variant', record.value.variant_name),
    field('SKU', record.value.sku), field('Barcode', record.value.barcode),
    field('Location', record.value.location_name), field('Bin or shelf', record.value.bin_location),
    field('Preferred supplier', record.value.preferred_supplier_name), field('Last physically counted', formatDate(record.value.last_counted_at)),
  ]
  if (resource.value === 'suppliers') return [
    field('Supplier name', record.value.name), field('Category', humanize(record.value.category)), field('Supplier code', record.value.code),
    field('Contact person', record.value.contact_name), field('Account reference', record.value.account_reference),
    field('Email', record.value.email), field('Phone', record.value.phone),
    field('Website', record.value.website), field('Address', record.value.address), field('Tax identifier', record.value.tax_id),
  ]
  return [
    field('Description', record.value.description), field('Category', record.value.category_name),
    field('Supplier', record.value.supplier_name), field('Payment method', record.value.payment_method),
    field('Reference', record.value.reference), field('Receipt', record.value.receipt_public_id ? 'Attached' : 'No receipt attached'),
  ]
})

const secondaryFields = computed(() => {
  if (!record.value) return []
  if (resource.value === 'inventory') return [field('Unit cost', money(record.value.unit_cost)), field('Sale price', money(record.value.sale_price)), field('Reorder quantity', quantity(record.value.reorder_quantity)), field('Target stock', quantity(record.value.target_stock_level)), field('Record ID', record.value.public_id), field('Updated', formatDateTime(record.value.updated_at))]
  if (resource.value === 'suppliers') return [field('Status', record.value.is_active ? 'Active' : 'Inactive'), field('Payment terms', record.value.payment_terms_days ? `${record.value.payment_terms_days} days` : 'Due on receipt'), field('Typical lead time', record.value.lead_time_days ? `${record.value.lead_time_days} days` : 'Not set'), field('Created', formatDateTime(record.value.created_at)), field('Updated', formatDateTime(record.value.updated_at)), field('Record ID', record.value.public_id)]
  if (resource.value === 'purchase-orders') return [field('Supplier', record.value.supplier_name), field('Receiving location', record.value.location_name), field('Ordered date', formatDate(record.value.ordered_at)), field('Expected date', formatDate(record.value.expected_at)), field('Received in full', formatDateTime(record.value.received_at)), field('Supplier reference', record.value.supplier_reference), field('Shipping method', record.value.shipping_method), field('Delivery address', record.value.shipping_address), field('Created', formatDateTime(record.value.created_at)), field('Updated', formatDateTime(record.value.updated_at))]
  if (resource.value === 'quotations') return [field('Customer', record.value.customer_name), field('Customer email', record.value.customer_email), field('Accepted', formatDateTime(record.value.accepted_at)), field('Created', formatDateTime(record.value.created_at)), field('Converted order', record.value.converted_order_public_id), field('Converted invoice', record.value.converted_invoice_public_id)]
  if (resource.value === 'invoices') return [field('Customer', record.value.customer_name), field('Customer email', record.value.customer_email), field('Issued', formatDate(record.value.issued_at)), field('Order', record.value.order_public_id), field('Created', formatDateTime(record.value.created_at)), field('Updated', formatDateTime(record.value.updated_at))]
  return [field('Supplier', record.value.supplier_name), field('Payment method', record.value.payment_method), field('Reference', record.value.reference), field('Created', formatDateTime(record.value.created_at)), field('Updated', formatDateTime(record.value.updated_at))]
})

const connections = computed(() => {
  if (!record.value) return []
  if (resource.value === 'inventory') return record.value.preferred_supplier_public_id ? [{
    label: record.value.preferred_supplier_name || 'Preferred supplier',
    detail: 'Used as the suggested source for replenishment.',
    value: 'Supplier',
    imageUrl: record.value.preferred_supplier_image_url,
    abbreviation: initials(record.value.preferred_supplier_name),
    to: `/workspace/operate/suppliers/${record.value.preferred_supplier_public_id}`,
  }] : []
  if (resource.value === 'suppliers') return [
    { label: 'Supplied products', detail: 'Catalog variants available from this supplier', value: record.value.product_count || 0, abbreviation: 'P', to: `/workspace/operate/suppliers/${record.value.public_id}` },
    { label: 'Purchase orders', detail: `${record.value.open_purchase_order_count || 0} currently open`, value: record.value.purchase_order_count || 0, abbreviation: 'PO', to: `/workspace/operate?view=purchase-orders&supplier=${record.value.public_id}` },
    { label: 'Expense records', detail: 'Operating costs linked to this supplier', value: record.value.expense_count || 0, abbreviation: 'E', to: `/workspace/operate?view=expenses&supplier=${record.value.public_id}` },
    { label: 'Preferred inventory source', detail: 'Stock balances that recommend this supplier', value: record.value.preferred_inventory_count || 0, abbreviation: 'I', to: `/workspace/operate?view=inventory&supplier=${record.value.public_id}` },
  ]
  if (resource.value === 'purchase-orders') return [
    { label: record.value.supplier_name, detail: 'Supplier responsible for this order', value: 'Supplier', imageUrl: record.value.supplier_image_url, abbreviation: initials(record.value.supplier_name), to: `/workspace/operate/suppliers/${record.value.supplier_public_id}` },
    { label: 'Inventory balances', detail: 'Receiving these lines updates stock at the selected location', value: documentLines.value.filter(line => line.inventory_balance_public_id).length, abbreviation: 'I', to: '/workspace/operate?view=inventory' },
  ]
  if (resource.value === 'quotations') return [
    ...(record.value.converted_invoice_public_id ? [{ label: 'Converted invoice', detail: 'Invoice created from this quotation', value: 'Invoice', abbreviation: 'I', to: `/workspace/operate/invoices/${record.value.converted_invoice_public_id}` }] : []),
    ...(record.value.converted_order_public_id ? [{ label: 'Converted order', detail: 'Sales order created from this quotation', value: 'Order', abbreviation: 'SO', to: '/workspace/orders' }] : []),
  ]
  if (resource.value === 'invoices' && record.value.order_public_id) return [{ label: 'Sales order', detail: 'Commercial order that produced this invoice', value: 'Order', abbreviation: 'SO', to: '/workspace/orders' }]
  if (resource.value === 'expenses' && record.value.supplier_public_id) return [{ label: record.value.supplier_name || 'Supplier', detail: 'Supplier connected to this operating expense', value: 'Supplier', imageUrl: record.value.supplier_image_url, abbreviation: initials(record.value.supplier_name), to: `/workspace/operate/suppliers/${record.value.supplier_public_id}` }]
  return []
})

const canSubmitAction = computed(() => {
  if (resource.value === 'inventory') return Number(actionForm.quantity_delta) !== 0
  if (resource.value === 'purchase-orders') return Object.values(actionForm.receipts).some(value => Number(value) > 0)
  if (resource.value === 'invoices') return Number(actionForm.amount) > 0 && Number(actionForm.amount) <= Number(record.value?.balance_due || 0)
  return false
})

watch(actionOpen, open => {
  if (!open) return
  actionError.value = ''
  actionForm.quantity_delta = '0'
  actionForm.note = ''
  actionForm.amount = record.value?.balance_due || ''
  actionForm.reference = ''
  actionForm.receipts = Object.fromEntries(receivableLines.value.map(line => [line.public_id, String(remainingQuantity(line))]))
})

onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses()
  await Promise.all([loadRecord(), loadReferences()])
})

async function loadRecord() {
  if (!resources[resource.value]) {
    error.value = 'This operations section does not exist.'
    loading.value = false
    return
  }
  if (!businessId.value) return
  loading.value = true
  error.value = ''
  try {
    record.value = await apiFetch(`businesses/${businessId.value}/${resource.value}/${recordId.value}/`)
    if (resource.value === 'inventory') await loadStockMovements()
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || requestError?.data?.detail || 'The operations record could not be loaded.'
  } finally {
    loading.value = false
  }
}

async function loadReferences() {
  if (!businessId.value) return
  const base = `businesses/${businessId.value}`
  try {
    const [suppliers, locations, categories, offerings] = await Promise.all([
      apiFetch(`${base}/suppliers/?page=1`),
      apiFetch(`${base}/locations/`),
      apiFetch(`${base}/expense-categories/?page=1`),
      apiFetch(`${base}/offerings/?page_size=200`),
    ])
    references.suppliers = normalizeList(suppliers)
    references.locations = normalizeList(locations)
    references.categories = normalizeList(categories)
    references.variants = normalizeList(offerings).flatMap(offering => (offering.variants || []).map(variant => ({
      ...variant,
      label: `${offering.name} · ${variant.name || variant.sku || 'Default'}`,
    })))
  } catch {
    // The detail page remains readable if optional edit references are unavailable.
  }
}

function handleSaved(saved) {
  record.value = saved
  toast({ title: 'Details updated', description: 'The connected Operations records now use the latest information.' })
}

async function handleSupplierProductCreated() {
  toast({ title: 'Product connected', description: 'The supplier catalog now includes this product and its purchasing terms.' })
  await loadRecord()
}

async function loadStockMovements() {
  try {
    const response = await apiFetch(`businesses/${businessId.value}/stock-movements/?balance_public_id=${recordId.value}&page=1`)
    stockMovements.value = normalizeList(response)
  } catch {
    stockMovements.value = []
  }
}

async function submitAction() {
  actionSaving.value = true
  actionError.value = ''
  try {
    if (resource.value === 'inventory') {
      await apiFetch(`businesses/${businessId.value}/inventory/${recordId.value}/adjust/`, {
        method: 'POST', body: { quantity_delta: actionForm.quantity_delta, note: actionForm.note },
      })
    } else if (resource.value === 'purchase-orders') {
      await apiFetch(`businesses/${businessId.value}/purchase-orders/${recordId.value}/receive/`, {
        method: 'POST', body: { receipts: actionForm.receipts },
      })
    } else if (resource.value === 'invoices') {
      await apiFetch(`businesses/${businessId.value}/invoices/${recordId.value}/payments/`, {
        method: 'POST', body: { amount: actionForm.amount, reference: actionForm.reference },
      })
    }
    actionOpen.value = false
    toast({ title: actionMeta.value?.submitLabel || 'Record updated', description: 'The latest operation is reflected in this record.' })
    await loadRecord()
  } catch (requestError) {
    actionError.value = requestError?.data?.error?.message || requestError?.data?.detail || 'The operation could not be saved.'
  } finally {
    actionSaving.value = false
  }
}

async function openInvoicePdf() {
  pdfLoading.value = true
  try {
    const documentBlob = await apiFetch(`businesses/${businessId.value}/invoices/${recordId.value}/pdf/`, { responseType: 'blob' })
    const documentUrl = URL.createObjectURL(documentBlob)
    window.open(documentUrl, '_blank', 'noopener,noreferrer')
    window.setTimeout(() => URL.revokeObjectURL(documentUrl), 60_000)
  } catch (requestError) {
    toast({
      title: 'PDF unavailable',
      description: requestError?.data?.error?.message || requestError?.data?.detail || 'The invoice PDF could not be opened.',
      variant: 'destructive',
    })
  } finally {
    pdfLoading.value = false
  }
}

function metric(label, value, detail, icon) { return { label, value, detail, icon } }
function field(label, value) { return { label, value } }
function normalizeList(response) { return Array.isArray(response) ? response : response?.results || [] }
function lineQuantity(line) { return resource.value === 'purchase-orders' ? line.quantity_ordered : line.quantity }
function lineUnitAmount(line) { return resource.value === 'purchase-orders' ? line.unit_cost : line.unit_price }
function lineTotal(line) { return Number(line.line_total ?? Number(lineQuantity(line) || 0) * Number(lineUnitAmount(line) || 0)) }
function lineItemAbbreviation(line) { return initials(resource.value === 'purchase-orders' ? line.offering_name || line.description : line.description || 'Line item') }
function lineItemDetail(line, index) {
  if (resource.value === 'purchase-orders') {
    return [line.offering_name, line.variant_name, line.sku].filter(Boolean).join(' · ') || `Line ${index + 1}`
  }
  return `Line ${index + 1} · ${resource.value === 'quotations' ? 'Quotation item' : 'Invoice item'}`
}
function remainingQuantity(line) { return Math.max(0, Number(line.quantity_ordered || 0) - Number(line.quantity_received || 0)) }
function sumLines(fieldName) { return documentLines.value.reduce((sum, line) => sum + Number(line[fieldName] || 0), 0) }
function daysUntil(value) {
  const target = new Date(value)
  const today = new Date()
  target.setHours(0, 0, 0, 0)
  today.setHours(0, 0, 0, 0)
  return Math.round((target.getTime() - today.getTime()) / 86_400_000)
}
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium' }).format(new Date(value)) : 'Not set' }
function formatDateTime(value) { return value ? new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : 'Not set' }
function quantity(value) { return new Intl.NumberFormat('en-PH', { maximumFractionDigits: 3 }).format(Number(value || 0)) }
function money(value) {
  return new Intl.NumberFormat('en-PH', { style: 'currency', currency: record.value?.currency || business.activeBusiness?.currency || 'PHP' }).format(Number(value || 0))
}
function initials(value) { return String(value || 'S').split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() }
function humanize(value) { return String(value || 'Not set').replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase()) }
</script>
