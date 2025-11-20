# Finance: General Ledger & Reconciliation

## 1. Double-Entry Journal

- Core entities:
  - `GLJournalEntry` – header with document/posting dates, currency, fx_rate.
  - `GLJournalLine` – lines with `account_code`, debit/credit, base amounts.

- Rules:
  - Every journal entry must be balanced in **transaction** and **base** currency.
  - Entries are created in `draft` status and must be **posted** before affecting reports.
  - Posted entries are **immutable**; corrections are done via reversing journals.

- API:
  - `POST /api/finance/journal` – create draft journal.
  - `POST /api/finance/journal/<id>/post` – validate and post.
  - Only roles `finance` and `admin` are allowed.

## 2. Finance Audit Log

- Immutable table `finance_audit_log` records:
  - `event_type` (e.g. `JOURNAL_POSTED`, `BANK_AUTOMATCH`)
  - `entity_type`, `entity_id`
  - Non-sensitive metadata payload.
- Used for internal & external audits (who did what, when, and to which record).

## 3. Bank Reconciliation

- Entities:
  - `BankStatement` (header: bank account, period, opening/closing balances)
  - `BankStatementLine` (date, description, amount, running balance, match info)

- API:
  - `POST /api/finance/reconcile/bank-statements/import`
    - Import statements from uploads or bank APIs.
  - `POST /api/finance/reconcile/bank-statements/<id>/auto-match`
    - Simple auto-match by absolute amount and date window.
  - Auto-matching writes an audit event `BANK_AUTOMATCH`.

## 4. Ageing Reports

- Skeleton `/api/finance/reports/ar-ageing` groups open receivables into buckets:
  - `current`, `1-30`, `31-60`, `61-90`, `90+` days past due.
- Wire this into your actual AR/AP models and fields.

## 5. Next Steps

- Integrate GL posting with existing invoice/payment flows.
- Extend matching and ageing to satisfy Ethiopian accounting and tax requirements.
- Add year-end controls (closed periods, reversal posting) before production use.
