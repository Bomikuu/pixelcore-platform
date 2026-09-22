# DineEase to PixelCore parity ledger

Source repository: `/home/bomiku1/projects/dineEase-web` (read-only)

PixelCore preserves capabilities through generic business-scoped records. The source
route names below are compatibility inputs, not permission to modify DineEase.

| DineEase surface | PixelCore destination | Generalization |
| --- | --- | --- |
| Registration, verification, Google auth, password reset | Account authentication and onboarding | Account creation is separate from business creation |
| Restaurants and setup guide | Businesses, locations, presets, setup center | Presets provide vocabulary and starter records only |
| Menus, add-ons, nutrition, costing | Offerings, variants, option groups, food profiles | Food fields are an optional typed extension |
| Promotions | Discounts and campaigns | Rules apply to storefront, POS, and displays |
| Calendar and tasks | Schedule calendar and business events | Events remain the Google Calendar bridge |
| Tables and reservations | Resource types, resources, layouts, bookings | Tables are the restaurant resource preset |
| Employees and onboarding | Workforce profiles and business invitations | Membership remains the authorization source |
| Documents, attendance, leave, flags | Workforce operations | Location-scoped and industry-neutral |
| Attendance terminal | Business device: attendance terminal | One-time pairing and revocable sessions |
| Menu displays and poster menu | Display Studio | Poster Menu is a catalog-board template |
| Table QR menu | Published QR catalog | Uses offerings and business identity |
| Counter kiosk and customer display | POS station and paired customer display | Uses server-authoritative carts and orders |
| Cart, order, payment | Sell and customer portal | Guest checkout remains supported |
| Favorites and account | Business-scoped customer portal | No platform-wide discovery marketplace |
| Profit and expense reports | Operate reports | Uses actual orders, costs, inventory, and expenses |

## Uncommitted source work included in the port

- Interactive poster builder and canvas
- Portable poster JSON import and export
- Updated display/session API behavior
- Calendar and Google Calendar synchronization changes
- Setup and QR catalog refinements

## Compatibility rule

Existing PixelCore endpoints remain authoritative. Old route aliases redirect to the
new workspace or public surface; new APIs use UUID public identifiers, snake_case
fields, pagination, tenant filtering, and the standard PixelCore error envelope.
