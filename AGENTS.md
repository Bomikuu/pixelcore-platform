# PixelCore agent guidance

## Agent tooling

- Always use the `jev-cli` and `graphify` skills when working in this repository.
- Keep Jev input free of secrets. Treat its judgments as guidance and verify changes directly.
- Use graphify to trace relevant code relationships; scope extraction to the task when the full repository is large.

## Verification policy

- Use automated tests and targeted automated checks by default for both frontend and backend changes.
- Do not run frontend or backend builds unless the user explicitly requests them. Do not use a build as a routine verification step.
- Run visual tests, browser-based visual inspections, or manual verification only when the user explicitly requests them.
- Keep verification scoped to the change. Documentation-only changes do not require application tests or builds.
- The required frontend `npm run check:ui` check below remains part of automated verification.

## Frontend component boundary

- Treat `pixelcore-frontend/components/ui` as the canonical Shadcn component layer.
- Do not add raw `button`, `input`, `select`, `textarea`, or table primitives in application pages or feature components.
- Use Shadcn `Button`, `Input`, `Textarea`, `Checkbox`, `Select`, `Dialog`, `Table`, `Tabs`, `Toast`, and related components directly.
- Use `ButtonLink` for router links styled as actions and `ButtonAnchor` for external or document anchors styled as actions. Ordinary navigation remains a semantic `NuxtLink` or anchor.
- Use the adapters in `components/ui/native-*` only when preserving browser-native array checkbox, boolean radio, or DOM change-event behavior is required.
- Run `npm run check:ui` from `pixelcore-frontend` after frontend changes. The check compiles every Vue template and rejects raw or legacy UI primitives outside the shared layer.

## Repository boundary

- `/home/bomiku1/projects/dineEase-web` is protected source material. Do not modify it while implementing PixelCore.
