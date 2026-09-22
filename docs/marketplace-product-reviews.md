# Marketplace product page and reviews

The Marketplace shop layout uses a width-bounded, 1920px product detail workspace: gallery and store identity, product details and attributes, and a purchase panel. It becomes two columns at laptop widths and a single column on mobile. Brand Default and Luxury layouts are unchanged.

- Existing product photography, zoom, approved 3D models, variants, server-priced carts, stock reservations, and rental requests remain shared.
- Buy now adds the selected item to the existing bag and opens checkout; it does not clear other bag items or bypass server pricing.
- Key attributes use the product profile's specifications. No wholesale tiers, delivery promises, review counts, or sales statistics are fabricated.

## Customer reviews

- `GET /api/public/{slug}/storefront/products/{product_slug}/reviews/`: five reviews per page, `page`, `rating` (1–5), and `ordering` (`newest`, `highest`, `lowest`). Includes visible-only rating totals and distribution.
- `GET/PUT/DELETE .../reviews/mine/`: existing authenticated account only. PUT requires a paid or partially refunded, non-cancelled purchase linked to that account in the same business. DELETE always removes only the caller's review.
- One review per account/product, protected by a unique constraint and transactional writes. Authors can edit it without creating another rating.
- Reviews contain a 1–5 rating, title (120 characters), and body (3,000 characters). Text is rendered with Vue's escaped interpolation, never raw HTML. Public responses show only the author's first name, not email or order details.
- Existing guest purchases can be linked through the store account's existing portal workflow. Reviews do not link accounts by user-supplied email or order numbers.
- Django admin → Catalog → Product reviews lets authorized administrators hide reviews. Hidden reviews do not contribute to totals, and customer edits cannot override moderation. Admin creation/editing of customer review content is disabled.
- No demo reviews are seeded. An empty product honestly shows “No reviews yet.”

Apply catalog migration `0009_productreview` before using the endpoints. No dependency or container rebuild is required.
