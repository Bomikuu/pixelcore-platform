# Monthly demonstration fixture

Import from the repository root with `npm run seed:demo`. The default target
is the separate `northline-monthly-demo` business in local SQLite. Existing
Docker/PostgreSQL data is a different database. Start the local applications
with `npm run dev` to view the imported records.

`dataset.json` is the editable source of the fictional catalog, people,
suppliers and monthly activity. The application importer resolves its string
identifiers into stable UUIDs, computes monetary totals and stock ledgers,
and adapts calendar dates. Use the importer instead of `manage.py loaddata`.

```bash
npm run seed:demo -- --month 2026-10
npm run seed:demo -- --owner-email existing-owner@example.com
```

Without `--owner-email`, the initial demo login is
`monthly.demo@example.test` / `PixelCoreDemo123!`. Existing passwords are
preserved, so a changed password remains changed. `--owner-email` attaches
the separate demo business to that existing account without editing the
account or its other businesses. Use that same owner on later imports.

The month defaults to the current month in Asia/Manila. Past months,
including leap-year February, are supported; future transaction-history
months are rejected. Historical day positions are scaled across the elapsed
part of the month to avoid future sales. Event days are clamped to the actual
last day, and appointments are distributed across Monday–Saturday slots.
Attendance uses the elapsed weekdays specified in the fixture. Reimporting
the current month refreshes dates and statuses as the month progresses.

Retail orders, line items, payments, refunds, fulfillments, purchase receipts
and stock movements are connected. Each inventory balance is reconciled to
its full ledger and active reservations, including previously imported
months. One variant intentionally has low available stock. Service invoices
and their payment allocations represent separate commercial work; they do
not duplicate retail order payments. Sample quotations include a conversion
to a matching service invoice.

Generated records are refreshed on import. Manually added records are not
deleted. An unrelated business with the requested slug is rejected. Imports
run in a database transaction; newly written image files are removed if that
import fails. No notifications, calendar synchronization, provider payments,
builds, or application servers are started by the importer.

## Images

`images/` contains eight original AI-generated PNG files:

- `transit-runner.png`: stone knit running shoes.
- `ridge-utility-jacket.png`: clay utility jacket.
- `atlas-everyday-tee.png`: chalk cotton T-shirt.
- `field-day-tote.png`: sand canvas tote.
- `signal-bottle.png`: cobalt insulated bottle.
- `relay-crossbody.png`: olive crossbody bag.
- `storefront-hero.png`: fictional lifestyle-shop interior.
- `event-venue.png`: fictional community event venue.

All were generated with the built-in `image_gen` tool. The complete prompt
set and provenance are in `image-prompts.json`. These are fictional
photorealistic assets, not photographs of real products, premises or people.
They use no external hotlinks or third-party photographs. The importer
checks PNG integrity and records dimensions and SHA-256 checksums in the
media library. Each business gets its own media paths. Stable file hashes
avoid duplicate uploads on repeated imports.

## Direct Django use

In an already configured development backend environment:

```bash
python manage.py seed_month_demo --month 2026-10
```

This uses that environment's configured database and media storage. The root
`npm run seed:demo` command consistently selects the lightweight local SQLite
settings and bootstraps dependencies and migrations. `DEBUG=True` is required.

### Docker media storage

Docker's PostgreSQL database and named media volume are separate from the
host's SQLite database and `pixelcore-backend/media` folder. To populate the
Docker environment, run the importer inside its backend:

```bash
docker compose exec backend python manage.py seed_month_demo --month 2026-10
```

If the Docker database already has demo records but its media volume is
missing the files, restore only the bundled images:

```bash
docker compose exec backend python manage.py seed_month_demo --media-only
```

This restores images to the storage used by Django and Nginx, without
refreshing orders, invoices, attendance, passwords, or other sample activity.
For the equivalent repair in local SQLite/media, use
`npm run seed:demo -- --media-only`. No build is required.

## Automated verification

With Django's local environment configured, run:

```bash
python manage.py test businesses.test_monthly_demo --noinput
```

The tests use an isolated test database and temporary media, and cover
relationships, exact financial and stock totals, image integrity, repeat
imports, month boundaries, account preservation, transaction rollback and
absence of email, payment or calendar requests. No build or visual/manual
test is required.
