# Analytics workspace

`/workspace/analytics` uses `GET /api/businesses/<id>/reports/`. The existing
report definitions remain authoritative: gross sales are non-cancelled order
grand totals; gross profit subtracts snapshot item costs; the operating result
subtracts recorded expenses. These are operational values, not cash receipts or
net refund accounting. Refunded orders follow the existing report definition.

The report now supplies full-period daily order counts, top six products,
category item totals, every order status, and the five most recent orders.
Business-local dates control the period and daily buckets. Cancelled orders
appear in status/recent activity but are excluded from sales and product ranks.
Product order counts are distinct even when multiple variants share an order.
Current catalog category names are used; deleted/unlinked items remain in
Uncategorized. The top five categories plus the remaining-category total cover
all item sales. Item totals may differ from order totals due to shipping and
order-level adjustments. Product names and costs retain their order snapshots.

Overview, Sales, Products, and Operations select real sections. Committed date
ranges (`from`, `to`), section (`tab`), and chart grouping (`interval`) live in
the URL. Native date fields retain the browser calendar. Range validation uses
the report endpoint's maximum of 366 days between endpoints. Current inventory
and invoice positions are explicitly distinguished from period bookings.
Superseded report requests are aborted and cannot replace the current response.

Each section has its own six summary tiles:

- Overview: gross sales, non-cancelled orders, average order, gross profit,
  expenses, and net operating result.
- Sales: gross sales, all orders placed, fully paid orders, average order,
  fulfilled orders, and cancelled orders. State counts use orders placed in the
  selected period, not the date of a later status change.
- Products: item sales, units sold, distinct recorded products, category groups,
  average unit value, and the top product's share of all item sales. Counts and
  denominators come from complete-period aggregates, never the top-six sample.
- Operations: period expenses and bookings, current inventory at cost, current
  low-stock balances, current open invoices, and current overdue invoices.

Export identifies the active section and includes that section's summary metrics.

Summary tiles use the shared Tooltip with hover and keyboard-focus explanations.
They move upward 3px over 200ms on hover-capable devices. Reduced motion disables
movement and transitions. Primary metric definitions stay visible without hover.
The sales chart has currency and order axes, daily/weekly/monthly grouping,
pointer inspection, arrow-key inspection, and an equivalent accessible table.
Sparklines use actual daily series; no comparison percentages are invented.

Export downloads the displayed report's summaries, daily activity, category
totals, and bounded product ranking as CSV. User-controlled text is quoted and
spreadsheet formula prefixes are escaped. Export is unavailable during loading
and failure.

## Canonical UI Map

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
| --- | --- | --- | --- | --- |
| Date | components/ui/input with Popover | DESIGN.md; BusinessReportView | Native browser date calendar within authored range popover | Date boundary unit/API tests; browser validation and focus |
| Select/Listbox | components/ui/select | DESIGN.md | Authored Radix popup matching trigger width | Browser keyboard and popup geometry |
| Form | components/ui/label, input, button | AGENTS.md; report range contract | novalidate with inline range error | Helper tests and browser invalid range |
| Scrollbar | assets/css/tailwind.css | DESIGN.md | Internal table/chart overflow; document owns page scrolling | Narrow viewport inspection |

The existing runtime CSS tokens and business theme adapter own colors, Manrope,
focus, and shape. This screen does not add an independent palette or alter the
shared workspace shell. RevenueChart remains the single-series sibling variant;
AnalyticsSalesChart is the dual-axis sales/order variant for this report.

## Verification

- `npm run check:ui`
- `node --test utils/analytics.test.mjs` from pixelcore-frontend
- `python manage.py test operations.test_analytics --keepdb --noinput` from backend
- Design context lint and the premium static auditor
- Isolated browser preview: hover/focus, reduced motion, intervals, section tabs,
  invalid range, export, empty, loading, retry, and desktop/narrow layouts

The premium static auditor currently treats capitalized Vue `Select` as a native
select and the Button inside a Radix PopoverTrigger as actionless. Those two
findings require component-aware review: the Select is authored and the trigger's
action is delegated by Radix. Native Date ownership is explicitly resolved above.
The full repository audit also reports existing findings outside this screen;
it is not a clean repository-wide compliance result.
