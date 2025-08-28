# UI Style Guide

This guide expands on the design tokens in `docs/design_system.md` and documents
common components to keep the interface consistent and accessible.

## Components
- **Buttons** – Use `.btn-primary` for main actions and `.btn-secondary` for
  alternatives.
- **Forms** – Align labels with inputs using Bootstrap's grid; mark required
  fields with `required` and include inline validation feedback.
- **Alerts** – Display success and error states via the shared
  `templates/partials/messages.html` partial.

## Color & Spacing
- Primary color: `#0d6efd`
- Success color: `#198754`
- Spacing tokens: `--space-xs: .25rem`, `--space-sm: .5rem`, `--space-md: 1rem`.

## Accessibility
- Ensure a minimum 4.5:1 contrast ratio for text.
- All interactive elements must be reachable via keyboard navigation.

Visual regressions are checked in CI by the `visual-regression` workflow running
`pytest tests/visual`.
