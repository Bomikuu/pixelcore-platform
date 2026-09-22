# Live sales desk

## Access

- `/workspace`: sales series, period metrics, attention queues and paginated order activity.
- `/workspace/orders`: active, awaiting-payment, delivery, fulfilled, cancelled, refunded and all-order views.
- `/workspace/sell/requests`: approval, stock holds, active rental, due-today, overdue, returned and history views.
- Legacy `/workspace/sell?view=orders` links redirect to the dedicated orders page, preserving query parameters.

The sidebar puts these three operational destinations first. All existing analytics, tracker, catalog, workforce, POS, CMS and settings destinations remain accessible.

## Meaning of the figures

The graph shows order value for orders currently fully paid, excluding cancelled/refunded orders, grouped by their **placement date** in the business timezone. It is not a cash-receipts, net-refund or rental-income report. Rental requests alone generate no revenue. The sales period is 7, 30 or 90 days. Operational queue counts are business-wide/all-time and do not change with that period selector.

Lists fetch 20 rows at a time and retain filters/search/page in the URL. Counts and sales aggregates use all matching database rows, not the loaded page. Refresh runs every 30 seconds when visible, can be switched off, and pauses for an open review. If refresh fails, the prior data is labeled stale.

## Rental follow-up

- A collected rental becomes overdue on the day **after** its inclusive return date, according to the business timezone. Returned records are never overdue.
- Approved rentals whose collection date has passed get a separate collection-overdue queue.
- Phone/email buttons open the operator's apps; PixelCore does not automatically send a message.
- **Record customer follow-up** writes a staff note and audit event without changing status, stock or payment.
- **Extend by agreement** requires a later date and a note. It preserves the original date in the audit event, keeps units held and does not charge a late fee.
- **Record physical return** requires explicit confirmation. Never use it simply to clear an alert; stock remains held until the units return.
- Owner/admin/manager permissions remain enforced for request details and actions. Staff can see their existing order workspace but not private request queues or counts.

## Additive API

- `GET /api/businesses/{id}/live-sales/?days=30` returns sales totals, the complete daily series, timezone, timestamp and current order/request counts.
- Orders add `scope` and `search` filtering plus an all-business `summary` alongside the existing paginated response.
- Product requests add `scope`, `search`, full summary counts, `updated_at` and derived `attention`. Existing `kind`/`status` filters still work.
- Request transitions accept `follow_up` and `extend`, optional `ends_on`, and optional `expected_updated_at` for optimistic concurrency. The UI sends the timestamp and stale updates return 409.

No schema migration or container rebuild is required.

## Focused verification

Backend and browser checks are left to the user; the required UI-boundary check is run during implementation.

Implementation result: `npm run check:ui` passed, and the scoped Impeccable detector reported no findings. Runtime layout, polling, and backend regression tests have not been executed in this pass. No independent visual-review pass was run under the user's verification/delegation budget; detector output is not a visual sign-off.

```sh
docker compose exec -T backend python manage.py test commerce.test_live_sales --keepdb
```

Check more than 20 orders/requests, next/previous pages, URL reload/back, hidden-tab refresh, opened-dialog refresh pausing, overdue and returned filters, contact links, extension conflicts and physical-return confirmation. Existing hero-test reruns remain separate from this change.
