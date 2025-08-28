# Accessibility and UX Enhancements

- **WCAG Testing**: `pa11y-ci` runs in CI to validate templates against WCAG 2.1 AA.
- **Per-user Dashboards**: Users can rearrange and save widgets; preferences are stored server-side.
- **In-app Tours**: `intro.js` guides new users through key workflows.
- **Push Notifications**: Service workers dispatch browser notifications for assigned tasks and alerts.
- **Offline Sync**: Actions queue in IndexedDB and replay when connectivity returns.
- **Inline Row Editing**: Datatables support in-place edits with optimistic locking.
- **Barcode Scanning**: Inventory views accept camera or handheld scanner input.
- **Saved Filters and Templates**: Users save filter sets and export layouts for reuse.
- **Kanban Board**: Drag-and-drop workflow board exposes SLA timers and escalation rules.
