# F19 — Feature Flags and Safe Rollouts

This blueprint introduces controlled rollout mechanics to ship risky changes without destabilising production. It is additive to existing config, CI/CD, RBAC, and prior F1–F18 layers.

## 1) Minimal feature flag facility

Start with a simple registry (config or DB-backed):

```python
FEATURE_FLAGS = {
    "inventory_v2": True,
    "orders_strict_validation": True,
    "reports_v2": False,  # dark launch
    "bot_advanced_flows": False,
}

def is_enabled(flag: str) -> bool:
    return FEATURE_FLAGS.get(flag, False)
```

Branch **only at the edges** (service entrypoints), keeping legacy code until cutover. This preserves behaviour and avoids deep branching.

## 2) Rollout stages

1. **Dark launch** — new code executes silently; UI still shows legacy results while mismatches are logged.
2. **Shadow compare** — enable for a small org/user slice; collect mismatch/latency metrics.
3. **Full cutover** — flip flag globally once mismatch rate and SLO impact are acceptable; retire legacy path afterward.

## 3) Interaction with SLOs and queues

- If a flagged path harms SLOs or inflates critical queues, flip it **off** without redeploying.
- Stagger enablement per org/user to avoid spikes (especially for heavy reports or inventory recalcs).

## 4) Governance and cleanup

- Track flag ownership (who can change it), rollout dates, and planned retirement date.
- Regularly prune stale flags to avoid dual-path complexity.
- Record flag changes in audit logs; expose current flag states via an internal endpoint for observability.

## 5) Expert challenges and mitigations

- **Stale flags:** enforce cleanup cadence (e.g., monthly review).
- **Partial coverage:** ensure tests exercise both flag states for critical flows (Inventory/Orders/Reports).
- **Unauthorized toggles:** restrict flag changes to trusted roles and log every change with actor and org scope.
