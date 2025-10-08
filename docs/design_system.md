# Design System

This project follows a small set of spacing and typography tokens to keep
interfaces consistent.

## Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` | Tight padding/margins |
| `--space-sm` | `8px` | Form element gaps |
| `--space-md` | `16px` | Section spacing |
| `--space-lg` | `24px` | Dialog and card padding |
| `--space-xl` | `32px` | Elevated card padding |

## Typography

| Token | Value | Usage |
|-------|-------|-------|
| `--font-base` | `16px/1.5` | Body text |
| `--font-sm` | `14px/1.4` | Secondary text |
| `--font-lg` | `20px/1.6` | Section headings |

These tokens are referenced in templates and styles to keep layout and
readability aligned with modern UI/UX standards.

## Color

| Token | Value | Usage |
|-------|-------|-------|
| `--surface-bg` | `#0f172a` | Primary background gradient anchor |
| `--surface-card` | `#111827` | Card surface base color |
| `--action-accent` | `#93c5fd` | Interactive accents and links |
| `--text-primary` | `#e5e7eb` | Foreground text |
| `--text-muted` | `#94a3b8` | Secondary text |

All core tokens are implemented in `erp/static/css/base.css` so templates can
consume the same palette and spacing primitives without re-declaring inline
styles.【F:erp/static/css/base.css†L1-L121】

## Components

- **Card layout** – `.card` defines the frosted-glass gradient background, 20px
  radius, and hover affordances used by authentication and dashboard views.【F:erp/static/css/base.css†L33-L73】
- **Primary button** – `.btn` plus optional `.btn--full` provides a11y-friendly
  hover states, focus rings, and responsive sizing for CTAs.【F:erp/static/css/base.css†L81-L128】
- **Utility spacing** – `.u-mt-sm`, `.u-mt-md`, `.u-mt-lg`, and `.stack` help
  compose layouts without reintroducing inline styles.【F:erp/static/css/base.css†L129-L162】
