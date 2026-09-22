<template>
  <section class="workspace-page space-y-5">
    <PageHeader
      title="Operations"
      description="Control stock, procurement, commercial records, expenses, and operating performance from one workspace."
    >
      <template #actions>
        <Button v-if="canCreate" type="button" @click="createOpen = true">
          <Plus class="h-4 w-4" aria-hidden="true" />
          {{ createLabel }}
        </Button>
      </template>
    </PageHeader>

    <Tabs v-model="view" class="space-y-5">
      <div class="overflow-x-auto">
        <TabsList class="h-auto min-w-max">
          <TabsTrigger v-for="tab in tabs" :key="tab.value" :value="tab.value">
            <component :is="tab.icon" class="h-4 w-4" aria-hidden="true" />
            {{ tab.label }}
          </TabsTrigger>
        </TabsList>
      </div>

      <OperationsTabGuide
        v-if="guideVisible"
        :title="guide.title"
        :description="guide.description"
        :connection="guide.connection"
        :details="guide.details"
        :icon="currentTab.icon"
        @dismiss="guideVisible = false"
      />

      <TabsContent value="summary">
        <StatePanel v-if="loading" kind="loading" title="Loading operations summary" message="Collecting stock, purchasing, document, and expense activity." />
        <StatePanel v-else-if="error" kind="error" title="Operations summary unavailable" :message="error">
          <Button type="button" variant="outline" @click="load">Try again</Button>
        </StatePanel>
        <div v-else class="space-y-5">
          <div class="flex flex-col justify-between gap-3 border-b pb-4 sm:flex-row sm:items-end">
            <div>
              <h2 class="font-semibold">Live operating summary</h2>
              <p class="mt-1 text-sm text-muted-foreground">Current-month activity, cash movement, stock health, and records needing attention.</p>
            </div>
            <Button type="button" variant="outline" size="sm" @click="view = 'reports'">
              <BarChart3 class="h-4 w-4" aria-hidden="true" />
              Open date-range reports
            </Button>
          </div>

          <dl class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4">
            <div v-for="metric in summaryMetrics" :key="metric.label" class="border-b p-5 sm:border-r xl:border-b-0 last:border-r-0">
              <dt class="flex items-center gap-2 text-sm text-muted-foreground">
                <component :is="metric.icon" class="h-4 w-4" aria-hidden="true" />
                {{ metric.label }}
              </dt>
              <dd class="mt-2 text-2xl font-semibold tabular-nums">{{ metric.value }}</dd>
              <p class="mt-1 text-xs text-muted-foreground">{{ metric.detail }}</p>
            </div>
          </dl>

          <div class="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(20rem,.75fr)]">
            <section class="rounded-xl border bg-card p-5 sm:p-6">
              <RevenueChart
                title="Sales activity"
                description="Recorded non-cancelled orders this month"
                :points="salesPoints"
                :currency="business.activeBusiness?.currency"
              />
            </section>
            <section class="rounded-xl border bg-card p-5 sm:p-6">
              <OperationsExpenseBreakdown
                :items="report?.expense_breakdown || []"
                :currency="business.activeBusiness?.currency"
              />
            </section>
          </div>

          <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
            <section class="overflow-hidden rounded-xl border bg-card">
              <div class="border-b px-5 py-4">
                <h2 class="font-semibold">Operational attention</h2>
                <p class="mt-1 text-sm text-muted-foreground">Records that may need a decision or follow-up.</p>
              </div>
              <div class="divide-y">
                <Button
                  v-for="attention in attentionItems"
                  :key="attention.view"
                  variant="ghost"
                  type="button"
                  class="h-auto w-full justify-start gap-4 rounded-none px-5 py-4 text-left hover:bg-muted/30"
                  @click="view = attention.view"
                >
                  <span class="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-muted text-primary">
                    <component :is="attention.icon" class="h-5 w-5" aria-hidden="true" />
                  </span>
                  <span class="min-w-0 flex-1">
                    <strong class="block">{{ attention.title }}</strong>
                    <span class="mt-1 block text-sm text-muted-foreground">{{ attention.detail }}</span>
                  </span>
                  <span class="text-xl font-semibold tabular-nums">{{ attention.value }}</span>
                  <ChevronRight class="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                </Button>
              </div>
            </section>

            <aside class="rounded-xl border bg-card p-5">
              <h2 class="font-semibold">Business position</h2>
              <p class="mt-1 text-sm text-muted-foreground">Current operating footprint and this month’s purchasing.</p>
              <dl class="mt-5 divide-y text-sm">
                <div v-for="record in businessPosition" :key="record.label" class="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0">
                  <dt class="text-muted-foreground">{{ record.label }}</dt>
                  <dd class="font-semibold tabular-nums">{{ record.value }}</dd>
                </div>
              </dl>
            </aside>
          </div>
        </div>
      </TabsContent>

      <TabsContent v-for="tab in directoryTabs" :key="tab.value" :value="tab.value" class="space-y-5">
        <dl class="grid overflow-hidden rounded-xl border bg-card sm:grid-cols-2 xl:grid-cols-4">
          <div v-for="metric in tabMetrics" :key="metric.label" class="border-b p-4 sm:border-r xl:border-b-0 last:border-r-0">
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

        <div v-if="relationshipFilter" class="flex flex-col gap-3 rounded-xl border bg-muted/30 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-center gap-3">
            <Link2 class="h-4 w-4 text-primary" aria-hidden="true" />
            <p class="text-sm"><span class="font-semibold">Scoped to {{ relationshipFilter.name }}</span><span class="text-muted-foreground"> · {{ relationshipFilter.detail }}</span></p>
          </div>
          <Button type="button" variant="ghost" size="sm" @click="clearRelationshipFilter">Clear filter</Button>
        </div>

        <section class="overflow-hidden rounded-xl border bg-card">
          <div class="flex flex-col justify-between gap-3 border-b px-5 py-4 sm:flex-row sm:items-center">
            <div>
              <h2 class="font-semibold">{{ currentTab.label }}</h2>
              <p class="mt-1 text-sm text-muted-foreground">{{ totalCount }} total record{{ totalCount === 1 ? '' : 's' }}. Select a row to open its detail page.</p>
            </div>
            <Button type="button" size="sm" variant="outline" :disabled="loading" @click="load">
              <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" aria-hidden="true" />
              Refresh
            </Button>
          </div>

          <StatePanel v-if="loading" kind="loading" :title="`Loading ${currentTab.label.toLowerCase()}`" message="Retrieving operational records for the active business." />
          <StatePanel v-else-if="error" kind="error" :title="`${currentTab.label} unavailable`" :message="error">
            <Button type="button" variant="outline" @click="load">Try again</Button>
          </StatePanel>
          <StatePanel v-else-if="!items.length" :title="`No ${currentTab.label.toLowerCase()} yet`" :message="emptyMessage">
            <Button v-if="canCreate" type="button" @click="createOpen = true">
              <Plus class="h-4 w-4" aria-hidden="true" />
              {{ createLabel }}
            </Button>
          </StatePanel>
          <div v-else class="overflow-x-auto">
            <Table class="min-w-[64rem]">
              <TableHeader>
                <TableRow>
                  <TableHead v-for="column in columns" :key="column.key" :class="column.align === 'right' ? 'text-right' : ''">{{ column.label }}</TableHead>
                  <TableHead class="w-12"><span class="sr-only">Open</span></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="item in items"
                  :key="item.public_id"
                  role="link"
                  tabindex="0"
                  class="cursor-pointer transition-colors hover:bg-muted/35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                  :class="rowClass(item)"
                  @click="openRecord(item)"
                  @keydown.enter="openRecord(item)"
                >
                  <TableCell
                    v-for="column in columns"
                    :key="column.key"
                    class="py-4"
                    :class="[column.align === 'right' ? 'text-right' : '', column.primary ? 'min-w-64' : '']"
                  >
                    <template v-if="column.primary">
                      <span class="flex items-center gap-3.5">
                        <Avatar class="h-12 w-12 shrink-0 rounded-xl border bg-muted">
                          <AvatarImage
                            v-if="item.image_url"
                            :src="item.image_url"
                            :alt="`${cellValue(item, column)} image`"
                            class="object-cover"
                          />
                          <AvatarFallback class="rounded-xl text-sm font-semibold">
                            {{ itemAbbreviation(item) }}
                          </AvatarFallback>
                        </Avatar>
                        <span class="min-w-0">
                          <strong class="block truncate">{{ cellValue(item, column) || 'Untitled record' }}</strong>
                          <span class="mt-1 block truncate text-xs text-muted-foreground">
                            {{ itemIdentityDetail(item) }}
                          </span>
                        </span>
                      </span>
                    </template>
                    <template v-else-if="column.kind === 'status'">
                      <StatusPill :value="cellValue(item, column)" />
                    </template>
                    <template v-else-if="column.kind === 'money'">
                      <span class="font-semibold tabular-nums">{{ money(cellValue(item, column)) }}</span>
                    </template>
                    <template v-else-if="column.kind === 'date'">
                      <span :class="dateAttentionClass(item, column)">{{ formatDate(cellValue(item, column)) }}</span>
                    </template>
                    <template v-else-if="column.kind === 'quantity'">
                      <span class="font-semibold tabular-nums">{{ quantity(cellValue(item, column)) }}</span>
                    </template>
                    <template v-else-if="column.kind === 'days'">
                      <span class="tabular-nums">{{ Number(cellValue(item, column) || 0) ? `${cellValue(item, column)} days` : '—' }}</span>
                    </template>
                    <template v-else-if="column.kind === 'progress'">
                      <span class="block min-w-28">
                        <span class="flex justify-between gap-2 text-xs"><span>{{ quantity(item.remaining_units) }} left</span><strong class="tabular-nums">{{ quantity(item.receiving_progress) }}%</strong></span>
                        <span class="mt-1.5 block h-1.5 overflow-hidden rounded-full bg-muted"><span class="block h-full rounded-full bg-primary" :style="{ width: `${Math.min(100, Number(item.receiving_progress || 0))}%` }" /></span>
                      </span>
                    </template>
                    <template v-else-if="column.kind === 'attention'">
                      <OperationsAttentionBadge :status="item.attention_status" :message="item.attention_message" />
                    </template>
                    <template v-else>
                      <span :class="column.primary ? 'font-semibold' : 'text-muted-foreground'">{{ cellValue(item, column) || '—' }}</span>
                    </template>
                  </TableCell>
                  <TableCell class="py-4 text-right"><ChevronRight class="ml-auto h-4 w-4 text-muted-foreground" aria-hidden="true" /></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
          <RecordPagination v-if="totalCount > pageSize" :page="page" :count="totalCount" :size="pageSize" :busy="loading" @page="changePage" />
        </section>

        <p v-if="['quotations', 'invoices'].includes(view)" class="rounded-xl border bg-muted/30 px-4 py-3 text-xs leading-5 text-muted-foreground">
          These are operational commercial records. PixelCore does not represent them as BIR-authorized invoices or receipts.
        </p>
      </TabsContent>

      <TabsContent value="reports" class="space-y-5">
        <div class="border-b pb-4">
          <h2 class="font-semibold">Historical and date-range reports</h2>
          <p class="mt-1 text-sm text-muted-foreground">Change the period to analyze recorded performance. Summary remains fixed to the current operating month.</p>
        </div>
        <form class="flex flex-col gap-3 rounded-xl border bg-card p-4 sm:flex-row sm:items-end" @submit.prevent="load">
          <div class="grid gap-2">
            <Label for="date-from">From</Label>
            <Input id="date-from" v-model="dateFrom" type="date" />
          </div>
          <div class="grid gap-2">
            <Label for="date-to">To</Label>
            <Input id="date-to" v-model="dateTo" type="date" />
          </div>
          <Button type="submit" variant="outline" :disabled="loading">
            <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': loading }" aria-hidden="true" />
            Refresh report
          </Button>
        </form>

        <StatePanel v-if="loading" kind="loading" title="Calculating report" message="Aggregating actual orders, bookings, stock, payments, and expenses." />
        <StatePanel v-else-if="error" kind="error" title="Report unavailable" :message="error" />
        <div v-else-if="report" class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem]">
          <section class="overflow-hidden rounded-xl border bg-card">
            <div class="border-b px-5 py-4">
              <h2 class="font-semibold">Operating result</h2>
              <p class="mt-1 text-sm text-muted-foreground">Actual recorded transactions for the selected period.</p>
            </div>
            <dl class="divide-y">
              <div v-for="metric in reportMetrics" :key="metric.label" class="flex items-center justify-between gap-4 px-5 py-4">
                <dt class="text-sm text-muted-foreground">{{ metric.label }}</dt>
                <dd class="font-semibold tabular-nums">{{ money(metric.value) }}</dd>
              </div>
            </dl>
          </section>
          <aside class="rounded-xl border bg-card p-5">
            <h2 class="font-semibold">Report basis</h2>
            <p class="mt-3 text-sm leading-6 text-muted-foreground">{{ report.basis }}</p>
            <dl class="mt-5 divide-y text-sm">
              <div v-for="item in reportBasis" :key="item.label" class="flex justify-between gap-4 py-3 first:pt-0 last:pb-0">
                <dt class="text-muted-foreground">{{ item.label }}</dt>
                <dd class="font-semibold tabular-nums">{{ item.value }}</dd>
              </div>
            </dl>
          </aside>
        </div>
        <div v-if="report && !loading" class="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(20rem,.75fr)]">
          <section class="rounded-xl border bg-card p-5 sm:p-6">
            <RevenueChart
              title="Sales activity"
              :description="`${formatDate(dateFrom)} to ${formatDate(dateTo)}`"
              :points="salesPoints"
              :currency="business.activeBusiness?.currency"
            />
          </section>
          <section class="rounded-xl border bg-card p-5 sm:p-6">
            <OperationsExpenseBreakdown
              title="Expense categories"
              description="Recorded costs in the selected period"
              :items="report.expense_breakdown || []"
              :currency="business.activeBusiness?.currency"
            />
          </section>
        </div>
      </TabsContent>
    </Tabs>

    <OperationsCreateDialog
      v-model:open="createOpen"
      :view="view"
      :business-id="businessId"
      :inventory="view === 'inventory' ? items : references.inventory"
      :suppliers="references.suppliers"
      :locations="references.locations"
      :customers="references.customers"
      :variants="references.variants"
      :categories="references.categories"
      @created="handleCreated"
    />
  </section>
</template>

<script setup>
import {
  AlertTriangle,
  BarChart3,
  Boxes,
  Building2,
  ChevronRight,
  CircleDollarSign,
  ClipboardList,
  FileText,
  Link2,
  PackageCheck,
  Plus,
  ReceiptText,
  RefreshCw,
  ShoppingCart,
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from '@/components/ui/toast'
import OperationsCreateDialog from '@/components/operations/OperationsCreateDialog.vue'
import OperationsAttentionBadge from '@/components/operations/OperationsAttentionBadge.vue'
import OperationsExpenseBreakdown from '@/components/operations/OperationsExpenseBreakdown.vue'
import OperationsTabGuide from '@/components/operations/OperationsTabGuide.vue'
import RecordPagination from '@/components/workspace/RecordPagination.vue'
import RevenueChart from '@/components/workspace/RevenueChart.vue'

useHead({ title: 'Operations | PixelCore' })

const route = useRoute()
const router = useRouter()
const business = useBusinessStore()
const { apiFetch } = useApiClient()

const tabs = [
  { label: 'Summary', value: 'summary', icon: BarChart3 },
  { label: 'Inventory', value: 'inventory', icon: Boxes },
  { label: 'Suppliers', value: 'suppliers', icon: Building2 },
  { label: 'Purchase orders', value: 'purchase-orders', icon: ShoppingCart },
  { label: 'Quotations', value: 'quotations', icon: FileText },
  { label: 'Invoices', value: 'invoices', icon: ReceiptText },
  { label: 'Expenses', value: 'expenses', icon: CircleDollarSign },
  { label: 'Reports', value: 'reports', icon: ClipboardList },
]
const directoryTabs = tabs.filter(tab => !['summary', 'reports'].includes(tab.value))
const view = computed({
  get: () => tabs.some(tab => tab.value === route.query.view) ? String(route.query.view) : 'summary',
  set: value => {
    if (!tabs.some(tab => tab.value === value)) return
    void router.push({ query: { ...route.query, view: value, page: undefined, supplier: undefined } })
  },
})
const currentTab = computed(() => tabs.find(tab => tab.value === view.value) || tabs[0])
const businessId = computed(() => business.activeBusiness?.public_id || '')
const items = ref([])
const totalCount = ref(0)
const page = ref(1)
const pageSize = 20
const report = ref(null)
const summaryCounts = reactive({ inventory: 0, suppliers: 0, purchaseOrders: 0, quotations: 0, invoices: 0, expenses: 0 })
const references = reactive({ inventory: [], suppliers: [], locations: [], customers: [], variants: [], categories: [] })
const loading = ref(true)
const error = ref('')
const createOpen = ref(false)
const guideVisible = ref(true)

const today = new Date()
const dateTo = ref(today.toISOString().slice(0, 10))
const dateFrom = ref(new Date(today.getFullYear(), today.getMonth(), 1).toISOString().slice(0, 10))
const summaryDateTo = today.toISOString().slice(0, 10)
const summaryDateFrom = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().slice(0, 10)

const canCreate = computed(() => directoryTabs.some(tab => tab.value === view.value))
const createLabel = computed(() => ({
  inventory: items.value.length ? 'Adjust stock' : 'Add stock item',
  suppliers: 'New supplier',
  'purchase-orders': 'New purchase order',
  quotations: 'New quotation',
  invoices: 'New invoice',
  expenses: 'New expense',
}[view.value] || 'New record'))
const emptyMessage = computed(() => ({
  inventory: 'Add a product variant and location, then establish its opening balance through an audited adjustment.',
  suppliers: 'Add suppliers so purchasing and expense records have a reliable business contact.',
  'purchase-orders': 'Create a purchase order to track expected stock and partial or complete receiving.',
  quotations: 'Prepare a customer quotation that can later become an order or invoice.',
  invoices: 'Create an operational invoice and allocate received payments from its detail page.',
  expenses: 'Record incurred costs so operations reports remain evidence-based.',
}[view.value] || 'No records are available.'))

const columns = computed(() => {
  const tableColumns = ({
  inventory: [
    { key: 'offering_name', label: 'Product', primary: true },
    { key: 'sku', label: 'SKU' },
    { key: 'location_name', label: 'Location' },
    { key: 'bin_location', label: 'Bin' },
    { key: 'available', label: 'Available', kind: 'quantity', align: 'right' },
    { key: 'reorder_quantity', label: 'Reorder', kind: 'quantity', align: 'right' },
  ],
  suppliers: [
    { key: 'name', label: 'Supplier', primary: true },
    { key: 'code', label: 'Code' },
    { key: 'product_count', label: 'Products', align: 'right' },
    { key: 'open_purchase_order_count', label: 'Open POs', align: 'right' },
    { key: 'payment_terms_days', label: 'Terms', kind: 'days', align: 'right' },
    { key: 'lead_time_days', label: 'Lead time', kind: 'days', align: 'right' },
  ],
  'purchase-orders': [
    { key: 'number', label: 'Order', primary: true },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'supplier_reference', label: 'Supplier reference' },
    { key: 'expected_at', label: 'Expected', kind: 'date' },
    { key: 'status', label: 'Status', kind: 'status' },
    { key: 'receiving_progress', label: 'Receiving', kind: 'progress' },
    { key: 'total_amount', label: 'Value', kind: 'money', align: 'right' },
  ],
  quotations: [
    { key: 'number', label: 'Quotation', primary: true },
    { key: 'customer_name', label: 'Customer' },
    { key: 'expires_at', label: 'Expires', kind: 'date' },
    { key: 'status', label: 'Status', kind: 'status' },
    { key: 'grand_total', label: 'Total', kind: 'money', align: 'right' },
  ],
  invoices: [
    { key: 'number', label: 'Invoice', primary: true },
    { key: 'customer_name', label: 'Customer' },
    { key: 'due_at', label: 'Due', kind: 'date' },
    { key: 'status', label: 'Status', kind: 'status' },
    { key: 'amount_paid', label: 'Paid', kind: 'money', align: 'right' },
    { key: 'balance_due', label: 'Balance', kind: 'money', align: 'right' },
  ],
  expenses: [
    { key: 'description', label: 'Expense', primary: true },
    { key: 'category_name', label: 'Category' },
    { key: 'supplier_name', label: 'Supplier' },
    { key: 'incurred_at', label: 'Incurred', kind: 'date' },
    { key: 'payment_method', label: 'Payment method' },
    { key: 'amount', label: 'Amount', kind: 'money', align: 'right' },
  ],
  }[view.value] || [])
  return tableColumns.length ? [...tableColumns, { key: 'attention_message', label: 'Attention', kind: 'attention' }] : []
})

const guide = computed(() => ({
  summary: {
    title: 'Your live operating control view',
    description: 'Use Summary for the current month’s stock, purchasing, receivables, expenses, and immediate follow-up. It is intentionally different from historical Reports.',
    connection: 'Operations records → current status → attention queue → business decisions',
    details: [
      'Inventory, suppliers, purchase orders, quotations, invoices, and expenses remain the source records. Summary does not replace their detail pages.',
      'The current-month metrics show what is happening now, including sales, cost, expenses, stock health, and outstanding customer balances.',
      'Operational rules surface low stock, overdue deliveries, unpaid invoices, and missing expense evidence so follow-up is not buried in a directory.',
      'Use the attention links to open the responsible tab, inspect the source record, and record the next action instead of changing totals manually.',
    ],
  },
  inventory: {
    title: 'Inventory is stock by product variant and location',
    description: 'Available stock equals on-hand quantity less active reservations. Reorder settings and a preferred supplier help the team act before stock is exhausted.',
    connection: 'Product variant → inventory balance → preferred supplier → purchase order → receiving movement',
    details: [
      'Each sellable variation has its own SKU, cost, price, and inventory identity. Different sizes or colors should not share one balance.',
      'A balance belongs to one product variant at one location. On-hand stock changes only through recorded movements, while reservations reduce what is available.',
      'The preferred supplier is the default replenishment source. Supplier-product records retain that supplier’s SKU, latest cost, minimum order, and lead time.',
      'A purchase order records what was requested and the expected delivery date. Creating it does not increase available stock.',
      'Receive stock when goods physically arrive. Partial receipts update only the quantities delivered and create an auditable movement for the selected location.',
    ],
  },
  suppliers: {
    title: 'Suppliers describe who provides your products and services',
    description: 'Add identity, category, contacts, payment terms, lead time, image, and the exact products they can supply. Supplier history grows through purchase orders and expenses.',
    connection: 'Supplier identity → supplied products → purchase orders and expenses → inventory and reports',
    details: [
      'Identity includes the supplier category, contact person, account reference, payment terms, lead time, and a recognizable image or logo.',
      'The supplied-products list connects exact catalog variants to supplier SKUs, unit costs, minimum order quantities, and product-specific lead times.',
      'Purchase orders build delivery history, while supplier-linked expenses retain costs that may not involve inventory, such as contractors or services.',
      'Receiving supplier orders updates inventory. Purchase and expense values then contribute to operating reports without duplicating the source records.',
    ],
  },
  'purchase-orders': {
    title: 'Purchase orders track what you expect to receive',
    description: 'Ordered quantities do not affect stock. Use Receive stock when goods arrive; partial and completed quantities then update inventory with an audit trail.',
    connection: 'Supplier and products → purchase order → receiving location → inventory balances',
    details: [
      'Select the supplier and exact product variants being purchased. Their latest unit costs and supplier relationship remain available for future replenishment.',
      'The order records quantities, costs, supplier reference, ordered date, expected date, shipping method, and delivery instructions.',
      'The receiving location determines which inventory balances will increase. A single order should point to the location physically accepting the goods.',
      'Use Receive stock for each delivery. Partial receipts leave remaining units open; a full receipt records completion time and closes the order.',
    ],
  },
  quotations: {
    title: 'Quotations are customer proposals, not charges',
    description: 'Track draft, sent, accepted, declined, expired, and converted quotes. Expiry warnings identify proposals needing follow-up.',
    connection: 'Customer → quotation → customer decision → accepted order or invoice',
    details: [
      'A quotation starts with an existing customer so contact and commercial history remain connected to one customer record.',
      'Line items define the proposed products or services, quantity, unit price, tax rate, total, expiry, and customer-facing terms.',
      'Sent quotations remain proposals until the customer accepts or declines. Expiring and expired records are highlighted for follow-up or replacement.',
      'Accepted work can be converted into the appropriate sales order or operational invoice without re-entering the commercial details.',
    ],
  },
  invoices: {
    title: 'Invoices track customer balances and collection deadlines',
    description: 'Due dates, partial payments, outstanding balances, and payment references show what is collectible and what needs attention.',
    connection: 'Customer or order → invoice → payment allocations → reporting',
    details: [
      'An invoice belongs to a customer and can optionally reference the sales order that created the obligation.',
      'Issued and due dates establish the collection window. The detail page keeps billed, paid, and remaining balances visible together.',
      'Record each payment allocation with its amount and traceable reference. Partial payments reduce the balance without marking the invoice fully paid.',
      'Collected amounts, outstanding balances, and overdue counts feed Summary and Reports while the invoice remains the authoritative source record.',
    ],
  },
  expenses: {
    title: 'Expenses capture the real cost of operating',
    description: 'Categories, suppliers, references, and receipts make reports explainable. Missing evidence is highlighted for follow-up.',
    connection: 'Supplier and category → expense evidence → operating costs → Summary and Reports',
    details: [
      'Link the supplier when there is one and choose a category that explains what the business purchased or paid for.',
      'The amount, tax portion, incurred date, payment method, transaction reference, and receipt form the reviewable evidence for the cost.',
      'Missing receipts and payment references are highlighted because undocumented costs are harder to reconcile or audit later.',
      'Recorded expenses reduce the operating result and appear in category breakdowns for the selected reporting period.',
    ],
  },
  reports: {
    title: 'Reports explain recorded performance over a chosen period',
    description: 'Reports aggregate actual sales, product costs, expenses, payments, purchasing, and stock value. They do not contain forecasts.',
    connection: 'Source transactions → selected date range → operating result → business review',
    details: [
      'Orders, bookings, inventory, purchase orders, invoices, payments, and expenses remain the underlying evidence for every reported value.',
      'Choose a date range to recalculate activity for that period. Summary remains the current operating view and is not changed by this selection.',
      'The report combines recorded sales, product cost, gross profit, expenses, net operating result, collections, and inventory value.',
      'Use the result to investigate changes and open the corresponding operational records. Reports summarize evidence; they do not edit transactions or predict future performance.',
    ],
  },
}[view.value]))

const relationshipFilter = computed(() => {
  const supplierId = String(route.query.supplier || '')
  if (!supplierId || !['inventory', 'purchase-orders', 'expenses'].includes(view.value)) return null
  const supplier = references.suppliers.find(item => item.public_id === supplierId)
  const details = {
    inventory: 'Preferred-source inventory balances only',
    'purchase-orders': 'Purchase orders from this supplier only',
    expenses: 'Expenses linked to this supplier only',
  }
  return { name: supplier?.name || 'selected supplier', detail: details[view.value] }
})

const tabMetrics = computed(() => {
  const currentItems = items.value
  if (view.value === 'inventory') return [
    metric('Stock balances', totalCount.value, 'Across variants and locations', Boxes),
    metric('On hand', quantity(sum(currentItems, 'on_hand')), 'Current page quantity', PackageCheck),
    metric('Without supplier', currentItems.filter(item => item.attention_status === 'setup').length, 'Need a replenishment source', Building2),
    metric('Low stock', currentItems.filter(item => Number(item.available) <= Number(item.low_stock_threshold)).length, 'On this page', AlertTriangle),
  ]
  if (view.value === 'suppliers') return [
    metric('Suppliers', totalCount.value, 'Business directory', Building2),
    metric('Product sources', quantity(sum(currentItems, 'product_count')), 'Connected catalog variants', Boxes),
    metric('Open purchase orders', quantity(sum(currentItems, 'open_purchase_order_count')), 'Awaiting delivery', ShoppingCart),
    metric('Need setup', currentItems.filter(item => ['setup', 'warning'].includes(item.attention_status)).length, 'Missing products or contact details', AlertTriangle),
  ]
  if (view.value === 'purchase-orders') return [
    metric('Purchase orders', totalCount.value, 'All recorded orders', ShoppingCart),
    metric('Overdue', currentItems.filter(item => item.attention_status === 'critical').length, 'Supplier follow-up needed', AlertTriangle),
    metric('Partially received', currentItems.filter(item => item.status === 'partially_received').length, 'Goods still outstanding', Boxes),
    metric('Fully received', currentItems.filter(item => item.status === 'received').length, 'Inventory updated', PackageCheck),
  ]
  if (view.value === 'quotations') return [
    metric('Quotations', totalCount.value, 'All customer quotes', FileText),
    metric('Quoted value', money(sum(currentItems, 'grand_total')), 'Current page', CircleDollarSign),
    metric('Expiring', currentItems.filter(item => ['warning', 'critical'].includes(item.attention_status)).length, 'Follow-up or refresh needed', RefreshCw),
    metric('Converted', currentItems.filter(item => item.status === 'converted').length, 'On this page', PackageCheck),
  ]
  if (view.value === 'invoices') return [
    metric('Invoices', totalCount.value, 'Operational documents', ReceiptText),
    metric('Billed', money(sum(currentItems, 'grand_total')), 'Current page', CircleDollarSign),
    metric('Outstanding', money(sum(currentItems, 'balance_due')), 'Current page', FileText),
    metric('Overdue', currentItems.filter(item => item.attention_status === 'critical').length, 'Collection follow-up needed', AlertTriangle),
  ]
  return [
    metric('Expenses', totalCount.value, 'Recorded costs', ReceiptText),
    metric('Spend', money(sum(currentItems, 'amount')), 'Current page', CircleDollarSign),
    metric('Missing receipts', currentItems.filter(item => item.attention_message === 'Attach receipt').length, 'Evidence needed', FileText),
    metric('Missing references', currentItems.filter(item => item.attention_message === 'Add payment reference').length, 'Payment traceability needed', AlertTriangle),
  ]
})

const summaryMetrics = computed(() => [
  { label: 'Sales', value: money(report.value?.sales), detail: 'Actual orders this month', icon: CircleDollarSign },
  { label: 'Gross profit', value: money(report.value?.gross_profit), detail: 'Sales less recorded cost', icon: BarChart3 },
  { label: 'Expenses', value: money(report.value?.expenses), detail: 'Costs incurred this month', icon: ReceiptText },
  { label: 'Invoice exposure', value: money(report.value?.invoice_aging?.outstanding), detail: 'Outstanding operational invoices', icon: FileText },
])
const attentionItems = computed(() => [
  { title: 'Low-stock balances', detail: `${report.value?.inventory?.out_of_stock_items || 0} are already out of stock.`, value: report.value?.inventory?.low_stock_items || 0, view: 'inventory', icon: AlertTriangle },
  { title: 'Overdue supplier deliveries', detail: `${report.value?.purchase_orders?.open || 0} purchase orders remain open.`, value: report.value?.purchase_orders?.overdue || 0, view: 'purchase-orders', icon: ShoppingCart },
  { title: 'Overdue customer invoices', detail: money(report.value?.invoice_aging?.outstanding) + ' remains outstanding.', value: report.value?.invoice_aging?.overdue_count || 0, view: 'invoices', icon: FileText },
  { title: 'Expenses missing receipts', detail: 'Attach evidence so operating reports can be reviewed.', value: report.value?.expense_evidence?.missing_receipts || 0, view: 'expenses', icon: ReceiptText },
])
const businessPosition = computed(() => [
  { label: 'Inventory balances', value: report.value?.inventory?.balances ?? summaryCounts.inventory },
  { label: 'Out of stock', value: report.value?.inventory?.out_of_stock_items || 0 },
  { label: 'Active suppliers', value: `${report.value?.suppliers?.active || 0} / ${report.value?.suppliers?.total || summaryCounts.suppliers}` },
  { label: 'Purchase orders this month', value: report.value?.purchase_orders?.total || 0 },
  { label: 'Received purchase orders', value: report.value?.purchase_orders?.received || 0 },
  { label: 'Purchase order value', value: money(report.value?.purchase_orders?.ordered_value) },
])
const salesPoints = computed(() => (report.value?.daily_activity || []).map(item => ({
  key: item.date,
  label: new Intl.DateTimeFormat('en-PH', { month: 'short', day: 'numeric' }).format(new Date(`${item.date}T12:00:00`)),
  fullLabel: new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium' }).format(new Date(`${item.date}T12:00:00`)),
  value: Number(item.sales || 0),
})))
const reportMetrics = computed(() => report.value ? [
  { label: 'Sales', value: report.value.sales },
  { label: 'Cost of goods', value: Number(report.value.sales) - Number(report.value.gross_profit) },
  { label: 'Gross profit', value: report.value.gross_profit },
  { label: 'Expenses', value: report.value.expenses },
  { label: 'Net operating result', value: report.value.net_operating_result },
  { label: 'Collected payments', value: report.value.collected_payments },
  { label: 'Inventory value at cost', value: report.value.inventory.value_at_cost },
] : [])
const reportBasis = computed(() => report.value ? [
  { label: 'Orders', value: report.value.orders.total },
  { label: 'Bookings', value: report.value.bookings.total },
  { label: 'Low stock', value: report.value.inventory.low_stock_items },
  { label: 'Open purchase orders', value: report.value.purchase_orders.open },
  { label: 'Open invoices', value: report.value.invoice_aging.open_count },
] : [])

watch(() => [view.value, businessId.value, route.query.supplier], () => {
  page.value = 1
  guideVisible.value = true
  void load()
})

onMounted(async () => {
  if (!business.activeBusiness) await business.loadBusinesses()
  await Promise.all([loadReferences(), load()])
})

async function load() {
  if (!businessId.value) return
  loading.value = true
  error.value = ''
  try {
    if (view.value === 'summary') await loadSummary()
    else if (view.value === 'reports') await loadReport()
    else await loadDirectory()
  } catch (requestError) {
    error.value = requestError?.data?.error?.message || requestError?.data?.detail || `Could not load ${currentTab.value.label.toLowerCase()}.`
  } finally {
    loading.value = false
  }
}

async function loadDirectory() {
  const params = new URLSearchParams({ page: String(page.value) })
  if (route.query.supplier) params.set('supplier', String(route.query.supplier))
  const response = await apiFetch(`businesses/${businessId.value}/${view.value}/?${params.toString()}`)
  items.value = normalizeList(response)
  totalCount.value = Number(response?.count ?? items.value.length)
}

async function loadSummary() {
  const base = `businesses/${businessId.value}`
  const [reportResponse, inventory, suppliers, purchaseOrders, quotations, invoices, expenses] = await Promise.all([
    apiFetch(`${base}/reports/?date_from=${summaryDateFrom}&date_to=${summaryDateTo}`),
    apiFetch(`${base}/inventory/?page=1`),
    apiFetch(`${base}/suppliers/?page=1`),
    apiFetch(`${base}/purchase-orders/?page=1`),
    apiFetch(`${base}/quotations/?page=1`),
    apiFetch(`${base}/invoices/?page=1`),
    apiFetch(`${base}/expenses/?page=1`),
  ])
  report.value = reportResponse
  Object.assign(summaryCounts, {
    inventory: countOf(inventory), suppliers: countOf(suppliers), purchaseOrders: countOf(purchaseOrders),
    quotations: countOf(quotations), invoices: countOf(invoices), expenses: countOf(expenses),
  })
}

async function loadReport() {
  report.value = await apiFetch(`businesses/${businessId.value}/reports/?date_from=${dateFrom.value}&date_to=${dateTo.value}`)
}

async function loadReferences() {
  if (!businessId.value) return
  const base = `businesses/${businessId.value}`
  try {
    const [locations, suppliers, customers, offerings, categories, inventory] = await Promise.all([
      apiFetch(`${base}/locations/`), apiFetch(`${base}/suppliers/?page=1`), apiFetch(`${base}/customers/?page=1`),
      apiFetch(`${base}/offerings/?page=1`), apiFetch(`${base}/expense-categories/?page=1`), apiFetch(`${base}/inventory/?page=1`),
    ])
    references.locations = normalizeList(locations)
    references.suppliers = normalizeList(suppliers)
    references.customers = normalizeList(customers)
    references.categories = normalizeList(categories)
    references.inventory = normalizeList(inventory)
    references.variants = normalizeList(offerings).flatMap(offering => (offering.variants || [])
      .filter(variant => variant.is_active)
      .map(variant => ({ public_id: variant.public_id, label: `${offering.name} · ${variant.name}` })))
  } catch {
    // Directory pages remain usable if optional creation references are unavailable.
  }
}

async function changePage(nextPage) {
  page.value = nextPage
  await load()
}

function clearRelationshipFilter() {
  void router.push({ query: { ...route.query, supplier: undefined, page: undefined } })
}

async function handleCreated(record) {
  toast({ title: `${currentTab.value.label.replace(/s$/, '')} saved`, description: 'The new operations record is ready to review.' })
  await Promise.all([load(), loadReferences()])
  if (record?.public_id) await router.push(recordPath(record.public_id))
}

function openRecord(item) {
  void router.push(recordPath(item.public_id))
}

function recordPath(publicId) {
  return `/workspace/operate/${view.value}/${publicId}`
}

function cellValue(item, column) {
  if (column.key === 'supplier_status') return item.is_active ? 'active' : 'inactive'
  if (column.key === 'line_count') return item.lines?.length || 0
  return item[column.key]
}

function rowClass(item) {
  if (item.attention_status === 'critical') return 'bg-destructive/[0.035] hover:bg-destructive/[0.07]'
  if (item.attention_status === 'warning') return 'bg-amber-500/[0.035] hover:bg-amber-500/[0.07]'
  return ''
}

function dateAttentionClass(item, column) {
  if (!['expected_at', 'expires_at', 'due_at'].includes(column.key)) return ''
  if (item.attention_status === 'critical') return 'font-semibold text-destructive'
  if (item.attention_status === 'warning') return 'font-semibold text-amber-700 dark:text-amber-300'
  return ''
}

function initials(value) {
  return String(value || 'Supplier').split(/\s+/).slice(0, 2).map(part => part[0]).join('').toUpperCase()
}

function itemAbbreviation(item) {
  const fixed = {
    'purchase-orders': 'PO',
    quotations: 'Q',
    invoices: 'I',
    expenses: 'E',
  }
  return fixed[view.value] || initials(item.name || item.offering_name || item.description || currentTab.value.label)
}

function itemIdentityDetail(item) {
  if (view.value === 'inventory') return [item.variant_name, item.sku].filter(Boolean).join(' · ') || 'Product inventory'
  if (view.value === 'suppliers') return humanize(item.category)
  if (view.value === 'purchase-orders') return item.supplier_name || 'Purchase order'
  if (['quotations', 'invoices'].includes(view.value)) return item.customer_name || currentTab.value.label.replace(/s$/, '')
  if (view.value === 'expenses') return [item.category_name, item.supplier_name].filter(Boolean).join(' · ') || 'Operating expense'
  return currentTab.value.label.replace(/s$/, '')
}

function humanize(value) {
  return String(value || 'supplier').replaceAll('_', ' ').replace(/^./, character => character.toUpperCase())
}

function normalizeList(response) {
  return Array.isArray(response) ? response : response?.results || []
}

function countOf(response) {
  return Number(response?.count ?? normalizeList(response).length)
}

function sum(records, field) {
  return records.reduce((total, record) => total + Number(record[field] || 0), 0)
}

function metric(label, value, detail, icon) {
  return { label, value, detail, icon }
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-PH', { dateStyle: 'medium' }).format(new Date(value))
}

function quantity(value) {
  return new Intl.NumberFormat('en-PH', { maximumFractionDigits: 3 }).format(Number(value || 0))
}

function money(value) {
  return new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: business.activeBusiness?.currency || 'PHP',
  }).format(Number(value || 0))
}
</script>
