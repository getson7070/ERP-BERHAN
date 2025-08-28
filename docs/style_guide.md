# UI Style Guide

This guide supplements the design tokens with practical UI patterns.

## Components
- Use Bootstrap 5 components for buttons, forms, and navigation.
- Prefer `<button class="btn btn-primary">` for primary actions and `btn-outline-secondary` for less prominent controls.

## Spacing
- Base spacing unit is `4px`.
- Use `p-2`/`m-2` for compact layouts and scale upwards in multiples of 4.

## Typography
- Base font size is `16px` with `1.5` line height.
- Headings use the `h1`–`h6` classes; avoid inline styles.

## Color & Contrast
- Primary color `#0d6efd`; secondary `#6c757d`.
- Ensure text contrast ratio of at least 4.5:1.

## Accessibility
- All interactive elements must have discernible text.
- Provide `aria-label` or `sr-only` text for icon-only buttons.

## Visual Regression Testing
Visual snapshots live under `tests/visual/`. CI runs Playwright to compare against committed baselines:

```bash
pytest tests/visual
```

Update snapshots intentionally with:

```bash
pytest tests/visual --update-snapshots
```
