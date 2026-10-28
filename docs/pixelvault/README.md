# PixelVault planning package

Prepared 2026-10-28 in Asia/Manila. The user requested planning from the detailed lending prompt and supplied PixelVault branding, then selected Django/DRF + React/TypeScript. No application code or external project was created.

Start with the [design specification](../superpowers/specs/2026-10-28-pixelvault-design.md) and [implementation index](../superpowers/plans/2026-10-28-pixelvault-implementation.md). The index links five independently reviewable phase plans and their exact proposed files/interfaces/tests.

Supporting context:

- [Product truth and open dependencies](PRODUCT.md).
- [Pinned brand and proposed UI system](DESIGN.md).
- [Preserved branding reference and provenance](brand/README.md).
- [Community](surfaces/community.md), [member workspace](surfaces/workspace.md), and [administration](surfaces/admin.md) surface briefs.
- [Evidence-backed PixelFlow integration contract](PIXELFLOW-INTEGRATION.md).

These are reviewable proposals. Proposed grace periods, calculation basis, fee payer, badge thresholds and implementation files are explicit decisions for review, not already operating product behavior. The demo interest/fee values are test fixtures, not market or legal recommendations.

PixelVault is planned as a standalone app at `/home/micxsz/projects/pixelvault`; that repository does not yet exist. PixelCore and PixelFlow remain separate existing applications. Their source and root product/design files were not changed. At approved execution, migrate this scoped context into the new product's own documentation and retain the original planning references.

The only financial integration established by source inspection is PixelFlow's supported collection/refund/event contract. Disbursement and settlement to individual lenders require separate approved capabilities. A payment success is not a settled lender payout. No future registration, template, badge or test result is represented as legal authorization or live provider approval.
