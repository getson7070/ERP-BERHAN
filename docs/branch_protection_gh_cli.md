# Branch protection (apply via GitHub CLI)
# Requires: gh auth login (repo admin)
gh api -X PUT repos/${OWNER}/${REPO}/branches/main/protection --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      {"context":"gitleaks"},
      {"context":"dependency-review"},
      {"context":"pip-audit"},
      {"context":"alembic-dry-run"},
      {"context":"rbac"}
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 1},
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
