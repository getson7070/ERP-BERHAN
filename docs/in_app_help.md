# In-App Help

To reduce training effort, the UI provides contextual help:

- Tooltip icons explain form fields and workflow steps.
- A help sidebar links to tutorials and support resources.
- Keyboard shortcuts are listed under the help menu.
- A guided product tour built with `intro.js` walks users through key tasks.
- Service workers queue offline actions and issue push notifications when tasks complete or attention is required.

When adding new modules, include tooltips and update `templates/help/` partials so users receive guidance without leaving the app.
