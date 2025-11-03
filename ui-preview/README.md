Preview pipeline check.
# ERP UI Preview Lane

## Local quick start
1. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` (e.g., `http://localhost:18000`).
2. `npm i`
3. `npm run dev` â†’ open shown URL (usually `http://localhost:5173`).

## PR Preview (Netlify)
- Add repo secrets: `NETLIFY_SITE_ID`, `NETLIFY_AUTH_TOKEN`.
- Open a Pull Request that changes `ui-preview/**`.
- GitHub will comment a **Preview URL** you can click and review.

> Note: previews use mockless calls to your API base URL; point it at staging to avoid prod data.


