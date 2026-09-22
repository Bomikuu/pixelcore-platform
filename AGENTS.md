# PixelCore agent guidance

## Frontend component boundary

- Treat `pixelcore-frontend/components/ui` as the canonical Shadcn component layer.
- Do not add raw `button`, `input`, `select`, `textarea`, or table primitives in application pages or feature components.
- Use Shadcn `Button`, `Input`, `Textarea`, `Checkbox`, `Select`, `Dialog`, `Table`, `Tabs`, `Toast`, and related components directly.
- Use `ButtonLink` for router links styled as actions and `ButtonAnchor` for external or document anchors styled as actions. Ordinary navigation remains a semantic `NuxtLink` or anchor.
- Use the adapters in `components/ui/native-*` only when preserving browser-native array checkbox, boolean radio, or DOM change-event behavior is required.
- Run `npm run check:ui` from `pixelcore-frontend` after frontend changes. The check compiles every Vue template and rejects raw or legacy UI primitives outside the shared layer.

## Repository boundary

- `/home/bomiku1/projects/dineEase-web` is protected source material. Do not modify it while implementing PixelCore.
