# ERP-BERHAN — Critical Stability Upgrades

This bundle contains surgical fixes for the failing areas seen in test runs:
1) Analytics fallbacks (methods remain callable even if deleted by tests)
2) GraphQL depth/complexity guards + metrics newline fix
3) Dead-letter queue handler pushes to the same redis_client as tests
4) RBAC cartesian matrix (both erp/authz.py and top-level authz.py)
