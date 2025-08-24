# Agent Instructions

## Remote connection

- Ensure the `origin` remote points to `https://github.com/getson7070/ERP-BERHAN.git`.
- Authenticate pushes using the `getson7070` account with a personal access token.
- If the remote is missing, configure it with:

  `git remote add origin https://getson7070:<PAT>@github.com/getson7070/ERP-BERHAN.git`

- After running required checks, push updates to the `main` branch:

  `git push origin HEAD:main`
