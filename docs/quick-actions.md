# Workspace Search and Quick actions

The header has an icon-only Search button followed by Quick actions. Search opens a
Shadcn Dialog/Command surface for records; Quick actions has no search field and opens
directly to eight grouped shortcut buttons. Both surfaces keep the active business
visible. Their accessible names remain available on narrow screens.

## Record search and suggestions

Search is dedicated to existing records; creation shortcuts live in their own dialog.
On opening, Products, Promotions, Categories, and Employees show up to three recently
updated suggestions each. Typing returns up to five matches per type. Category filters
limit the search to one type; clear restores suggestions immediately and refocuses the
input. Product/service matches open the catalog editor, promotions open their editor,
categories open their existing `?edit=` editor, and employees open their profile.

`GET businesses/<business-id>/workspace-search/?search=...&scope=all` supplies minimal
record summaries. It searches names, product and variant SKUs/barcodes, promotion codes,
and employee codes/job titles. Type prefixes such as `promo` and `products canvas`
narrow server-side searches. It uses tenant-scoped queries and bounded database results,
never downloads whole catalogs or follows external pagination links. Enabled modules
gate types; employee results are owner/admin only, matching EmployeeAdminSummaryView.
Staff and managers retain permitted commerce search without acquiring employee-profile
access. No personal contact, attendance, or payroll data is returned. Responses are
private and non-cacheable.

Result summaries include `image_url`. Products prefer ready cover media, then other
ready product images, then legacy library images; category covers and employee
profile photos use their existing storage URLs. Image assets must belong to the
active business and be ready images. Product media is prefetched in batches.
Promotions have no dedicated image field and use their type icon; missing or failed
photos use a type icon or employee initials via the shared Avatar components.

Remote requests debounce by 300ms, cancel on changes/close, ignore stale responses,
and pause during IME composition. Enter flushes a pending debounce without accidentally
opening an outdated result while records are loading. Loading, no matches, errors,
and retry have explicit feedback. New queries reset the result scroll position. Search
uses a teal focus underline and respects reduced motion. Queries remain transient
inside the modal rather than becoming URL history or persisted storage.

| Action | Destination |
| --- | --- |
| Add product | `/workspace/sell/products/new` |
| Add promotion | `/workspace/sell/promotions/new` |
| Record expense | Existing OperationsCreateDialog, expenses |
| Create invoice | Existing OperationsCreateDialog, invoices |
| Create quotation | Existing OperationsCreateDialog, quotations |
| Create purchase order | Existing OperationsCreateDialog, purchase-orders |
| Add supplier | Existing OperationsCreateDialog, suppliers |
| Add employee | `/workspace/operate/workforce/employees/new` |

The launcher opens a create flow; it does not save, publish, pay, or send an
invitation by itself. Complex product, promotion, and employee forms keep their
canonical dedicated pages. Operations forms stay over the current page and keep
their existing validation, document definitions, and backend endpoints.

## Context and permissions

The user’s membership is selected by matching `auth.user.businesses[].public_id`
to the active business. Only owner, admin, and manager roles receive create
actions, matching `BusinessScopedModelViewSet.mutation_roles`. Commerce requires
`sell`; operations and workforce actions require `operate` in `enabled_modules`.
Unknown memberships and missing capability data receive an explicit empty state.
Read-only roles can search permitted records but cannot use creation shortcuts.
Frontend filtering does not replace Django authorization.

Changing business, role, modules, identity, or route closes the launcher and
cancels preparation. The operation form captures its original business ID and
success callback; an in-flight request cannot be reassigned to a newly selected
business. The shared submit handler rejects duplicate submissions and keeps
dismissal unavailable while saving.

## Interaction and data loading

Search provides an explicit clear control, arrow-key browsing and Enter selection,
IME-safe Enter handling, Escape, and trigger focus restoration. Quick actions uses
ordinary Tab/Shift+Tab and Enter navigation among shortcut buttons. Both use the
existing hover and focus theme. Dialog entry/exit uses the shared 200ms animation; viewport width does not
interpolate. Reduced motion follows the global stylesheet.

Reference choices load only after selecting an operation. Supplier creation needs
none; expense needs suppliers/categories; invoice and quotation need customers;
purchase order needs suppliers, locations, and active variants. Pagination stays
on the same tenant endpoint and never follows a response-provided external URL.
Loading, cancel, failure/retry, no matches, and no access are explicit states.

After a successful operation, a `pixelcore:operations-created` event carries only
business ID, resource, and record ID. Analytics and the operations workspace
refresh when that event matches their active business. Other pages keep their
existing refresh behavior. The success message names the original business.

## Canonical owners and verification

- Header ownership: `WorkspaceShell` mounts `WorkspaceSearch` followed by `WorkspaceQuickActions`.
- Dialog, Command, Button, Alert, and Toast: `components/ui`.
- Operations fields and persistence: `OperationsCreateDialog` and existing APIs.
- Role and module sources: `businesses/views.py:MeView`, the identity serializer,
  and `businesses/api.py:BusinessScopedModelViewSet`.
- Shortcut registry and reference loading: `utils/workspaceQuickActions.js`.
- Record search: `WorkspaceRecordSearch`, `utils/workspaceSearch.js`, and
  `businesses/search.py:WorkspaceSearchView`.
- Automated checks: `npm run check:ui` and
  `node --test utils/workspaceQuickActions.test.mjs utils/workspaceSearch.test.mjs`,
  plus `python manage.py test businesses.test_search` in the backend runtime.
- Browser evidence in `output/playwright/quick-actions`: all eight destinations,
  keyboard search, IME, preparation cancellation, role filtering, reference retry,
  simulated single-submit save, analytics refresh, focus, and 320px layout.

Browser checks intercept API traffic; they do not create real records or send
messages. No builds are required or run. The broad premium static auditor still
has repository-wide findings and misclassifies delegated Shadcn trigger actions;
it is not a clean repository-wide compliance result.
