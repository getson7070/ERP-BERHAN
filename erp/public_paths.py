"""Shared public endpoint allowlists for security and tenant guards."""

# Health/readiness endpoints must stay publicly accessible for load balancers and probes.
# Keep this allowlist small and path-based (no wildcards) to minimise bypass risk.
PUBLIC_PATHS: set[str] = {
    "/health",
    "/healthz",
    "/health/ready",
    "/health/live",
    "/health/readyz",
    "/healthz/ready",
    "/readyz",
    "/status",
    "/status/health",
    "/status/healthz",
    # Auth endpoints must stay reachable for unauthenticated users to sign in or self-register.
    "/auth/login",
    "/login",
    "/auth/register",
}

PUBLIC_PREFIXES: tuple[str, ...] = (
    "/static/",
    "/assets/",
    "/favicon",
    "/robots.txt",
)
