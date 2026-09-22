---
version: 1
slug: pixelcore-frontend-pages-workspace-operate-index-vue
primary_target: pixelcore-frontend/pages/workspace/operate/index.vue
related_targets:
  - pixelcore-frontend/pages/workspace/operate/[resource]/[recordId].vue
  - pixelcore-frontend/components/operations/OperationsCreateDialog.vue
  - pixelcore-frontend/components/operations/DocumentLineFields.vue
  - pixelcore-frontend/components/workspace/WorkspaceShell.vue
---

# Operations workspace brief

## Use scene

Owners, administrators, and managers use this surface during active daily work to understand stock, suppliers, procurement, customer commercial records, expenses, and actual operating performance. It must scan quickly on a laptop while still remaining usable on a tablet or narrow viewport.

## Thesis

Operations is a connected record system, not a stack of unrelated dashboards. One calm workspace uses a stable tab directory, thin metric bands, information-dense tables, and dedicated record pages. Summary numbers support decisions; lists and detail pages remain the primary work surfaces.

## Hierarchy

1. Page identity and the one creation action relevant to the active tab.
2. Stable Shadcn tab navigation with Summary first and Reports last. Summary is the live current-month control view; Reports is adjustable historical analysis.
3. Evidence-based summary values, charts, business position, and attention items.
4. Paginated operational directories with clear row navigation.
5. Dedicated editable record pages with connected-record navigation and context-specific actions such as stock adjustment, receiving, and payment allocation.
6. Supplier identity and sourcing context: image, category, contact, payment terms, lead time, and the exact product variants supplied.
7. Attention states that highlight overdue deliveries, expiring quotations, overdue invoices, missing expense evidence, low stock, and incomplete supplier setup.

## Visual rules

- Preserve the workspace palette, typography, borders, and 12px card radius.
- Prefer shared bordered surfaces and dividers over nested cards or decorative shadows.
- Use tabular numerals for quantities, currency, and counts.
- Pair every directory summary value with a meaningful Lucide icon that supports scanning; do not repeat one generic symbol across unrelated metrics.
- Carry the same context-specific metric icons into dedicated record pages so list and detail summaries read as one system.
- Directory tables use generous primary identity cells with a real record image when available and a meaningful abbreviation fallback when it is not.
- Attention status is a compact icon trigger. Hover, keyboard focus, or click reveals the status label and practical message without making the table wider.
- Keep controls explicit, compact, and aligned with the record they affect.
- Form-heavy create and edit dialogs use a wide, viewport-bounded working surface with a fixed header and footer plus an independently scrolling form body. Small actions and confirmations remain compact.
- Do not imply forecasts. Mark current-page summaries when aggregation is limited to a page.
- Use product language: purchase order, quotation, invoice, expense, stock balance, and supplier.
- Every tab starts with a compact custom operational alert, not a generic alert primitive. It shows the tab icon, concise explanation, a prominent Learn more action, and a comfortably sized labelled dismiss action. Learn more opens a focused Shadcn dialog containing a contained vertical icon-led workflow with a practical explanation for every stage. The dialog body scrolls independently on short screens and must never introduce horizontal overflow; dismissal is intentionally session-memory only so the alert returns after refresh.
- Use Shadcn tooltips beside domain-specific form labels that benefit from explanation. Help triggers must be keyboard accessible, visually quiet, and separate from the label's click target.
- Relationship links must preserve context: opening purchase orders, expenses, or inventory from a supplier shows records scoped to that supplier and makes the active scope visible.
- Receiving must distinguish ordered, partially received, remaining, and fully received quantities, and preserve a completion timestamp plus stock-movement audit trail.
- Purchase-order receiving uses one clear progress sequence with ordered, received, and remaining quantities rather than a percentage alone.
- Purchase orders, quotations, and invoices share one line-item table pattern: a generous identity cell, product image when available, abbreviation fallback, clear metadata, aligned quantities and amounts, and a document-total footer.
- Active delivery, quotation, and invoice deadlines appear immediately below the record header as a compact single-line countdown such as `5 days left`, `Due today`, or `2 days overdue`; the strip includes only its icon, countdown, deadline label, and date.
- Connected-record rows carry a real supplier image when available and a concise record abbreviation when no meaningful image exists.
- Expense create and edit forms expose receipt evidence directly, accepting image or PDF uploads; the expense detail page names the attached file and provides an explicit view action.
- Supplier lists and detail pages use an image or initials fallback and always show supplier category; no supplier should be represented by name alone. The detail image supports a larger preview, and selecting a replacement image shows a local preview before save.

## Required states

- Loading, empty, error, and populated states for every directory and record page.
- Disabled submit states during invalid or saving modal actions.
- Keyboard-accessible table-row navigation and visible focus treatment.
- Horizontal overflow protection for dense operational tables.
- Paginated lists with totals retained outside the current page.
