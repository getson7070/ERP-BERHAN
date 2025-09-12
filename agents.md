Agent Operations & Safety Standard (AGENTS.md)

Purpose. Define how conversational/automation agents are designed, secured, evaluated, deployed, and operated in ERP-BERHAN.
Scope. Applies to all agent modules, bot adapters (Telegram/Slack), schedulers (Celery), plugins, and any future RPA/ML components.

Corporate policy reference: all agent behavior must align with BERHAN Pharma SOP and corporate policy (see docs/berhan_sop_pack.md).
Agents must also uphold BERHAN Pharma policies on ethics, diversity, environmental stewardship, occupational health & safety, information security, and governance; see docs/corporate_policy_alignment.md for the feature mapping.
For secure local setup refer to [docs/local_dev_quickstart.md](docs/local_dev_quickstart.md). Planned enhancements and gating steps are tracked in [docs/audit_roadmap.md](docs/audit_roadmap.md).

1) Scope & Definitions

Agent: A programmatic worker that receives structured input (event/API/prompt), performs ERP actions (e.g., progress a tender, approve an order), and returns structured output with full auditability.

Orchestrator: Flask/FastAPI endpoints + Celery tasks + plugin loader that route work to agents.

HITL (Human-in-the-Loop): Required approval step for high-risk actions (e.g., tender award, high-value order approval).

Out of scope: Agents must not alter secrets, RBAC, RLS policies, or DR settings.

2) Operating Principles

Least privilege (RBAC) with tenant isolation (PostgreSQL RLS on org_id).

Tamper-evidence (hash-chained audit logs) for all state-changing actions.

Safety by default: input sanitation, rate limits, lockouts, HITL gates, GraphQL depth/complexity caps.

Idempotency & replayability: idempotency keys; bounded retries; DLQ + safe replay.

Repeatable delivery: PR-only merges; CI gates must pass; signed artifacts; documented runbooks.

Observability: metrics, tracing, dashboards/status page; SLOs with alerts.

3) Architecture & Flow (high level)

Entry points: REST (/api/*), GraphQL (/api/graphql), bot webhooks (/bot/*), scheduled Celery jobs.

Execution path: API → (RBAC/RLS checks) → Agent function → ERP connector/plugin → DB (RLS enforced) → Audit append.

Security layers: MFA/SSO, short-lived JWTs (kid rotation + Redis revocation), Flask-Talisman (CSP/HSTS), Flask-Limiter (app-layer rate limits/lockouts), GraphQL depth/complexity guards, Argon2 password hashing.

Infra: Containers (non-root, HEALTHCHECK, pinned digests), K8s (probes, HPA, NetworkPolicies, CSI secrets), PgBouncer, Redis, Celery.

Observability: Prometheus /metrics (e.g., MV age, queue lag, RL 429s), structured logs, tracing IDs, status page.

DR: Backups + weekly restore drills (RPO ≤15m, RTO ≤60m).

4) Agent Catalog (maintain this table in PRs)
AgentPurposeTriggersInputs → OutputsAllowed APIs/ToolsSecrets/EnvOwnerEnvs
tender_lifecycle_agentEnforce ordered tender transitionsREST/GraphQL{org_id,tender_id,action} → {state}/api/tenders/*–Tender OpsDev/Stg/Prod
tender_eval_agentRecord evaluation resultsREST/GraphQL{org_id,tender_id,notes,scores} → {evaluation_id,state}/api/tenders/*–EvaluationDev/Stg/Prod
tender_award_agentWrite award & notify (HITL)REST + HITL{org_id,tender_id,awarded_to,award_date} → {state:'awarded'}/api/tenders/*, webhooks–ManagementDev/Stg/Prod
order_submission_agentCreate order (idempotent)Client UI/REST{org_id,item_id,qty,customer_id,idempotency_key} → {order_id,'pending'}/api/orders/*–SalesDev/Stg/Prod
order_approval_agentApprove/reject ordersStaff UI/REST{org_id,order_id,decision} → {status}/api/orders/*–OpsDev/Stg/Prod
marketing_report_agentSubmit marketing visit reportsUI/REST{org_id,rep_id,institution,contacts[],products[],outcome,sales_figures} → {report_id}/api/marketing/*–MarketingDev/Stg/Prod
maintenance_request_agentSubmit maintenance requestUI/REST{org_id,client_id,description,severity} → {ticket_id,'submitted'}/api/maintenance/*–SupportDev/Stg/Prod
maintenance_ops_agentAssign/progress/completeStaff UI/REST{org_id,ticket_id,action} → {status}/api/maintenance/*–SupportDev/Stg/Prod
notifications_agentSend role-aware notificationsCelery/Webhooks{org_id,type,payload} → {result}SMTP/SMS/Bottokens in envOpsDev/Stg/Prod
analytics_refresh_agentIncremental MV refresh/exportsCron{org_id} → {freshness}DB, OLAP export–DataDev/Stg/Prod

Allowed tools are explicit. Agents may call only what the catalog lists; any expansion requires PR review.

5) Permissions & Secrets (least privilege)

Enforce RBAC at API and RLS at DB on every call (scope to org_id).

Secrets live in GitHub Environments/Actions Secrets or K8s Secrets; rotate per docs/security/secret_rotation.md.

No hard-coded tokens; no credentials in git remotes.

6) Safety & Privacy

Sanitize inputs (strip HTML/URLs where not needed), validate types/ranges, and bound payload size; enforce rate limits.

HITL for high-risk actions: tender award, high-value order approvals.

PII/PHI: redact in logs; adhere to docs/data_retention.md (retention, deletion).

GraphQL: enforce depth/complexity caps; default filters by org_id.

7) Domain Agents & Workflows
7.1 Tender Workflow

States (ordered):
advert_registered → decided_to_register → documents_secured → preparing_documentation → documentation_prepared → document_submitted → opening_minute → evaluated → awarded

Transitions: forward-only (admin rollback to previous state via runbook only).

Permissions: tender_officer advances; management required for award.

Audit: each transition appends hash-chained log with {prior_state,new_state,actor,reason}.

HITL: awarded requires human approval + second-factor confirmation.

Data contracts (YAML)

name: tender_lifecycle_agent
input_schema:
  org_id: uuid
  tender_id: uuid
  action: enum[
    ADVANCE_TO_DECIDED_TO_REGISTER,
    ADVANCE_TO_DOCUMENTS_SECURED,
    ADVANCE_TO_PREPARING_DOCUMENTATION,
    ADVANCE_TO_DOCUMENTATION_PREPARED,
    ADVANCE_TO_DOCUMENT_SUBMITTED,
    ADVANCE_TO_OPENING_MINUTE,
    ADVANCE_TO_EVALUATED
  ]
  payload: object
output_schema:
  state: string
errors: [INVALID_TRANSITION, NOT_AUTHORIZED, RLS_DENIED, RATE_LIMITED, VALIDATION_ERROR]

name: tender_award_agent
input_schema:
  org_id: uuid
  tender_id: uuid
  awarded_to: string
  award_date: date
controls: { hitl_required: true, audit_required: true }
output_schema: { state: "awarded" }
errors: [HITL_REQUIRED, NOT_AUTHORIZED, VALIDATION_ERROR]


Runbook (tenders)

Idempotency: (org_id,tender_id,action)

DLQ replay: management sign-off needed for awarded replays

Rollback: only to previous state; never skip; always include reason

7.2 Orders

Flow: pending → approved | rejected (submissions are idempotent)

Data contracts

name: order_submission_agent
input_schema:
  org_id: uuid
  item_id: uuid
  qty: int>0
  customer_id: uuid
  idempotency_key: string
output_schema: { order_id: uuid, status: "pending" }
errors: [DUPLICATE_SUBMISSION, OUT_OF_STOCK, NOT_AUTHORIZED]

name: order_approval_agent
input_schema:
  org_id: uuid
  order_id: uuid
  decision: enum[APPROVE, REJECT]
controls: { hitl_required_if_total_gt: 10000 }  # example threshold
output_schema: { status: enum[approved, rejected] }
errors: [NOT_AUTHORIZED, VALIDATION_ERROR]


Metrics: orders_pending, orders_approved_total, duplicate_blocked_total, p95 latency.

7.3 Marketing Reports

Scope: visits/interactions with institutions, contacts, products discussed, outcomes, sales figures.

Privacy: contacts may contain PII → mask in logs; retention per docs/data_retention.md.

Contract

name: marketing_report_agent
input_schema:
  org_id: uuid
  rep_id: uuid
  institution: string
  contacts: array[object{name,email,phone}]
  products: array[string]
  outcome: string
  sales_figures: number
output_schema: { report_id: uuid }
errors: [NOT_AUTHORIZED, RLS_DENIED, VALIDATION_ERROR]


RBAC: reps view own history; management sees all in org.

7.4 Maintenance

Flow: submitted → assigned → in_progress → completed

Contracts

name: maintenance_request_agent
input_schema: { org_id: uuid, client_id: uuid, description: string, severity: enum[LOW,MEDIUM,HIGH] }
output_schema: { ticket_id: uuid, status: "submitted" }
errors: [NOT_AUTHORIZED, VALIDATION_ERROR]

name: maintenance_ops_agent
input_schema: { org_id: uuid, ticket_id: uuid, action: enum[ASSIGN, START, COMPLETE] }
output_schema: { status: enum[assigned, in_progress, completed] }
errors: [INVALID_TRANSITION, NOT_AUTHORIZED]


SLOs: first_response ≤ 4h; resolution targets by severity.
Metrics: maintenance_pending, first_response_time, resolution_time_p95.

7.5 Client vs Employee Sides

Client dashboard: place orders, view approvals, file maintenance, track status, message support; RBAC scoped to own org; PWA offline queue/replay applies.

Employee dashboard (role-aware): marketing CRUD (own vs all), inventory ops, tender create/list/report, order approvals, maintenance triage, user admin—all authenticated, authorized, and audited.

7.6 Cross-cutting enforcement

RBAC + RLS on every call; org_id required and verified.

Rate limits & lockouts on sensitive endpoints (/auth/*, awards, approvals).

Audit chain on all state changes (tenders, orders, maintenance).

Idempotency on client-initiated creates (orders, maintenance).

A11y & UX: consistent Bootstrap templates, breadcrumbs, saved views, i18n.

7.7 Alerts & Status Page

Trigger alerts and show on the status page:

mv_age_minutes > 10 (warning)

rate_limit_429s_total > threshold (warning)

orders_pending > N for 24h (page)

audit_chain_broken_total > 0 (page immediately)

maintenance_first_response_time_p95 > 4h (page)

8) Data Contracts & Versioning

Store contracts next to agents; update on change; bump since_version when altering fields.

Error taxonomy is stable (e.g., NOT_AUTHORIZED, RLS_DENIED, INVALID_TRANSITION, RATE_LIMITED, VALIDATION_ERROR).

9) Evaluation & Red-Team (CI-enforced)

Functional tests: deterministic outcomes for each contract.

Security tests: prompt-/input-injection, cross-org leakage, replay abuse, rate-limit/lockout behavior.

Regression gates (must pass): ruff/flake8, mypy, pytest ≥80% coverage, Bandit, pip-audit, gitleaks, Docker+Trivy, kube-linter/score, ZAP baseline, Pa11y.

10) Observability & SLOs

Per-agent metrics: success_rate, escalation_rate, p95_latency, queue_lag, cost_estimate, RL_429s_total, MV_age_minutes.

Tracing/log fields: org_id, agent, request_id, idempotency_key.

Status page: MV freshness, queue lag, RL 429 count, last DR drill result; link to artifacts.

11) Runbooks (required for each agent)

Idempotency strategy + key.

Retries/backoff with jitter; DLQ target & replay command; safety checks for replay.

Rollback steps per workflow.

Incident severity matrix, escalation contacts, communications template.

12) Delivery & Change Control

PR-only (no direct pushes to main); branch protection requires all checks + code review.

Signed commits/images; release notes per change; version prompts/templates alongside code.

Safer Git flow

gh repo set-default getson7070/ERP-BERHAN
gh auth login
git checkout -b feature/agent-<name>
git push -u origin feature/agent-<name>
gh pr create -B main -t "Agent: <name> – safety/permissions/obs" -b "Summary + eval results"

13) Deployment & Environments

Environments: dev → stg → prod; approvals and canary/blue-green for agent changes.

K8s: readiness/liveness, HPA, NetworkPolicies; secrets via env/CSI.

Containers: non-root, HEALTHCHECK, pinned digests; Trivy scans in CI.

AWS deployments:
- Push the latest `main` branch to GitHub before building artifacts.
- Build and push images to ECR (`ACCOUNT_ID.dkr.ecr.<region>.amazonaws.com/erp-berhan:<tag>`) with dependencies installed from `requirements.lock` using `python3 -m pip`.
- Containers must listen on port 8080 and apply migrations via `scripts/run_migrations.sh` before starting `gunicorn --bind 0.0.0.0:${PORT:-8080}`.
- `DATABASE_URL` and `REDIS_URL` must not use `localhost`; point to RDS or ElastiCache endpoints.

14) Performance & Capacity

Budgets: throughput target, p95 SLA, queue size; publish soak tests.

Database: PgBouncer, tuned pools, N+1 guards (joined/selectin load), cache policies.

15) Compliance & Governance

Map controls to ISO-27001 and relevant Ethiopian law (control matrix).

Audit logs: append-only, hash chain (prev_hash, hash, created_at), RLS protected; scheduled integrity checker publishes results.

Access recertifications: quarterly exports to immutable storage; link artifact.

Data retention: per entity policy in docs/data_retention.md.

16) Bot Adapters & Plugins

Telegram/Slack: whitelisted commands only; map to agents; enforce RBAC/RLS.

Plugin loader: registers routes/jobs for approved capabilities only (deny-by-default).

Marketplace: plugins declare permissions; reviewed via CI + manual approval.

17) References (repo-local)

Security & hardening: security.md, docs/security/secret_rotation.md

Audit chain & gaps: docs/audit_summary.md (+ migration adding hash-chain columns)

Blueprints/Templates: docs/blueprints.md, docs/templates.md

DR & Retention: docs/dr_plan.md, docs/data_retention.md

CI pipeline: .github/workflows/ci.yml (ruff, mypy, pytest+cov, Bandit, pip-audit, gitleaks, Trivy, kube-linters, ZAP, Pa11y)

Status page: see readme link

18) Agent PR Checklist (copy into every agent PR)

 Catalog updated (owner, tools, envs)

 Data contracts (input/output) committed & versioned

 RBAC/RLS enforced; only declared tools used

 Secrets from env/secret store; no hard-coded tokens

 HITL added for sensitive actions (if applicable)

 Idempotency + retry/backoff + DLQ implemented

 Metrics/tracing fields added (org_id, agent, request_id, idempotency_key)

 Tests: unit + integration + security (injection, leakage, RL/lockout)

 CI green (lint, types, tests ≥80%, SAST/SCA/secrets, ZAP, Trivy, Pa11y, kube-linters)

 Docs updated (runbook, status page, changelog)

19) Seed Templates

Agent module skeleton

# erp/agents/<name>.py
from dataclasses import dataclass
from typing import TypedDict, Literal

class Input(TypedDict):
    org_id: str
    action: str
    idempotency_key: str | None

@dataclass
class Output:
    status: Literal["ok","error"]
    detail: str | None = None

ALLOWED_TOOLS = ["rest_api:/api/<domain>/*", "celery_queue:<queue>"]

def run(payload: Input) -> Output:
    # 1) validate (types/ranges), scope to org_id (RLS)
    # 2) enforce RBAC for action; check rate limits/lockouts
    # 3) use idempotency_key to dedupe side-effects
    # 4) perform action via approved APIs/connectors
    # 5) append audit entry; return Output(...)
    ...


Runbook snippet

Idempotency: <strategy/key>
Retries/Backoff: <policy> (max N, jitter)
DLQ: <queue>; replay: scripts/dlq_replay.py --agent <name> --since <t>
Rollback: <steps>; tender states only step back one level
Alerts: success_rate<target, p95>budget, audit_chain_broken_total>0
On-call: <DRI>, rotation <link>

20) Change History

v1.0 — Initial, comprehensive standard aligned to ERP-BERHAN security/CI/DR/UX and the Tender, Orders, Marketing, and Maintenance definitions.
v1.1 — Documented September 2025 audit (overall score 8.3/10) highlighting unified authentication, HR workflow forms, ORM migration guidance, and expanded observability.
v1.2 — Added structured JSON logging with request IDs, feature-gated report builder, and linked corporate SOP repository.
v1.3 — Enforced RLS on HR tables, added nightly backup script with checksums, and introduced index-advice tooling.

21) 2025 Audit Snapshot

Latest assessment rated the platform **8.3/10** overall with the following focal points:

- **Security 8.7:** strong CI gates and scans; continue consolidating auth and role checks.
- **User-friendliness 7.8:** Bootstrap UI is clean but HR pages still evolving.
- **Database 7.6:** KPI tables and retention routines in place; replace residual raw SQL with SQLAlchemy services.
- **Code quality 8.1:** modular blueprints; tighten helper consistency.
- **Web access 8.2:** blueprint routing solid; guard unfinished endpoints with feature flags.
- **Integration 8.5:** CI pipeline exercises full stack; document Celery/Redis configs for operators.
- **Inter-function communication 8.2:** analytics tasks coordinated; wire HR forms to persistence layer.
- **Performance 8.3:** perf tests scheduled; add indices and slow-query logging.

Top remediation items:
1. Unify auth/permissions across all routes.
2. Complete HR recruitment and performance workflows.
3. Replace ad-hoc SQL with ORM models/services.
4. Stabilize report builder with persistence and feature flagging.
5. Polish style and add smoke tests for new pages.
6. Add structured logging and health/ready probes. *(Completed)*
7. Add DB indices and enable slow-query logs.
8. Restrict unfinished features in navigation.
