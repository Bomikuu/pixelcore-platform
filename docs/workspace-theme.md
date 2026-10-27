# Workspace theme

The left navigation footer places an accessible moon/sun button beside the account menu. Both remain outside the scrolling module list and are available in the mobile drawer; the collapsed desktop rail stacks their icon controls.
It switches between light and dark, changes its label to the next action, and
supports ordinary keyboard activation. It is present on narrow screens too.

The initial choice follows `prefers-color-scheme`. A manual selection overrides
the device setting and persists in the `pixelcore-workspace-theme` local-storage
key until changed or cleared. Invalid or missing preferences fall back to the device setting. Device
changes are observed while the preference is `system`. The preference contains no
account, business, or record information. Nuxt color-mode,
already installed by Shadcn, owns persistence and device detection.

## Ownership

- `useWorkspaceTheme` adapts Nuxt color-mode into shared preference, resolved mode,
  toggle, and computed brand-aware theme style.
- Nuxt color-mode owns the Tailwind theme class, stored preference, and device-change
  handling. `workspace-theme.global` sets non-administrative routes to forced light
  without changing the stored workspace preference. `workspace-theme.client` owns
  root CSS variables and native `color-scheme`.
- Primary Shadcn Buttons consume `--primary-foreground`, including dark accents
  that require dark text instead of hard-coded white.
- `businessThemeStyle` owns the semantic surface, text, border, action, and sidebar
  palette. Dark mode retains the business accent's hue while adapting lightness for
  contrast. Shape and typography settings remain in the existing brand mapping.
- `WorkspaceShell`, `WorkspaceSearch`, and `WorkspaceQuickActions` consume the same
  theme. Portalled operations forms, menus, popovers, and toasts inherit root tokens.
- The business store owns identity data; it no longer writes competing light-only
  root CSS variables when identity changes.

The toggle applies to `/workspace` and `/settings` route boundaries. Other routes
use the existing light brand mapping. Public previews explicitly receive light
surface tokens even while their surrounding settings workspace is dark.

Switching themes is immediate. Existing hover/focus transitions and reduced-motion
rules remain the shared stylesheet's responsibility.

## Verification

Run `npm run check:ui` and
`node --test utils/workspaceTheme.test.mjs utils/workspaceQuickActions.test.mjs utils/workspaceSearch.test.mjs`.
The theme tests cover device/manual preference resolution, route boundaries,
brand-hue/shape preservation, public-preview isolation, light restoration, and
text/action/input-boundary contrast across six different brand colors.

Browser evidence belongs under `output/playwright/workspace-theme`: initial device
preference, reload persistence, manual override, keyboard activation, root and
dialog parity, mobile bounds, and leaving/returning to workspace routes. Browser
API calls are intercepted and no real business records are changed. No builds run.
