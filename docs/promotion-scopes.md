# Promotions

Open Sell → Promotions at /workspace/sell/promotions. Existing links using
/workspace/sell?view=promotions redirect to the same list.

The list supports server pagination (20 per page), search, status, and catalog
scope filters. Summary counts cover the entire active business, independent of
the current filtered page. Each promotion has an Edit action and a dedicated
page; name, value, activation, code, schedule, and scope can all be updated.

## Scope contract

The existing business-scoped discounts endpoint and offering_ids remain valid.
category_ids is an optional array of category UUIDs. scope_type is a derived,
read-only field: catalog, categories, or products.

- Both arrays empty: the entire catalog.
- offering_ids set: only the selected offerings.
- category_ids set: products assigned directly to those categories, including
  future additions. Descendant categories must be selected explicitly.
- Setting both arrays is rejected. All identifiers must belong to the business.

Both storefront cart totals and POS preview calculate the discount against only
eligible lines. A fixed discount is capped at the eligible subtotal; unrelated
items and shipping do not enlarge that subtotal. The existing single-promotion
selection behavior remains in place; promotions do not stack.

The editor shows schedule inputs in the operator's device timezone and submits
UTC timestamps. The list formats schedules in the business timezone.

Apply the schema update with:

    docker compose exec -T backend python manage.py migrate commerce --noinput

No frontend build or test suite was run for this change.
