# erp/utils.py
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict, Iterable, Iterator, List, Mapping, Tuple

from flask import jsonify, request

# ──────────────────────────────────────────────────────────────────────────────
# IMPORTANT
# Do NOT import from flask_jwt_extended at module import time.
# Import INSIDE request/route functions only (see decorators below).
# This prevents LocalProxy objects being created before Eventlet monkey-patching.
# ──────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────── JSON helpers ────────────────────────────────
def _json_error(status_code: int, message: str, extra: Dict[str, Any] | None = None):
    payload = {"error": message, "status": status_code}
    if extra:
        payload.update(extra)
    return jsonify(payload), status_code


# ─────────────────────────── Auth/JWT decorators ─────────────────────────────
def login_required(fn: Callable) -> Callable:
    """
    Require a valid JWT for the request (no top-level JWT imports).
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper


def mfa_required(fn: Callable) -> Callable:
    """
    Require MFA indicated by either:
      - claim "mfa": true, or
      - claim "amr": ["mfa", ...]
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        verify_jwt_in_request()
        claims = get_jwt() or {}
        ok = bool(claims.get("mfa"))
        amr = claims.get("amr")
        if isinstance(amr, (list, tuple)) and "mfa" in amr:
            ok = True
        if not ok:
            return _json_error(401, "Multi-factor authentication required")
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*required_roles: Iterable[str]) -> Callable:
    """
    Require that JWT 'roles' includes ALL provided roles.
    Usage: @roles_required("admin", "manager")
    """
    flat: List[str] = []
    for r in required_roles:
        if isinstance(r, str):
            flat.append(r)
        else:
            flat.extend([str(x) for x in r])
    needed = set(flat)

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask_jwt_extended import verify_jwt_in_request, get_jwt
            verify_jwt_in_request()
            claims = get_jwt() or {}
            roles = claims.get("roles", [])
            if isinstance(roles, str):
                roles = [roles]
            if not needed.issubset(set(roles)):
                return _json_error(403, "Insufficient role", {"required": sorted(needed)})
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def optional_jwt(fn: Callable) -> Callable:
    """
    Allow a route to work with or without a JWT. If Authorization exists,
    verify it; otherwise proceed as anonymous.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, exceptions
        auth_hdr = request.headers.get("Authorization")
        if auth_hdr:
            try:
                verify_jwt_in_request()
            except exceptions.NoAuthorizationError:
                # Header present but not a valid JWT: treat as anonymous
                pass
        return fn(*args, **kwargs)
    return wrapper


# ───────────────────────── Sorting/Filtering helpers ─────────────────────────
def sanitize_direction(direction: str | None, default: str = "asc") -> str:
    """
    Normalize a sort direction to 'asc' or 'desc'.
    Accepts: 'asc', 'desc', 'ASC', 'DESC', '+', '-' (where '-' => desc).
    """
    if not direction:
        return default
    d = str(direction).strip().lower()
    if d in ("asc", "+", "ascending"):
        return "asc"
    if d in ("desc", "-", "descending"):
        return "desc"
    return default


def sanitize_sort(
    sort_param: str | None,
    allowed_fields: Mapping[str, Any],
    default_field: str | None = None,
    default_dir: str = "asc",
) -> Tuple[Any | None, str]:
    """
    Parse a client sort parameter safely and map it to an allowed field.

    sort_param examples:
      - "name"          -> ("name", "asc")
      - "name:desc"     -> ("name", "desc")
      - "-created_at"   -> ("created_at", "desc")  (leading '-' means desc)
      - "created_at:ASC"

    allowed_fields: mapping of client parameter -> actual sortable object
                    (e.g., {"name": User.name, "created_at": User.created_at})
    Returns (field_obj, direction). field_obj is None if not resolvable.
    """
    # Defaults
    direction = sanitize_direction(default_dir, default="asc")
    field_key = default_field

    if sort_param:
        token = sort_param.strip()
        if ":" in token:
            key, dir_token = token.split(":", 1)
            field_key = key.strip() or default_field
            direction = sanitize_direction(dir_token, default=direction)
        else:
            # Optional leading '-' for desc
            if token.startswith("-"):
                direction = "desc"
                token = token[1:]
            elif token.startswith("+"):
                token = token[1:]
            field_key = token or default_field

    field_obj = allowed_fields.get(field_key) if field_key else None
    return field_obj, direction


# ────────────────────────────── Streaming export ─────────────────────────────
def stream_export(
    rows: Iterable[Mapping[str, Any]] | Iterable[Iterable[Any]],
    fieldnames: List[str] | None = None,
    filename: str = "export.csv",
    fmt: str = "csv",
    mimetype: str | None = None,
):
    """
    Stream an export response (CSV or JSONL) without loading everything in memory.
    """
    from flask import Response, stream_with_context
    import io
    import csv
    import json

    fmt = (fmt or "csv").lower()
    if fmt not in ("csv", "jsonl"):
        fmt = "csv"

    if not mimetype:
        mimetype = "text/csv" if fmt == "csv" else "application/json"

    def _as_dict_iter(it: Iterable[Mapping[str, Any]] | Iterable[Iterable[Any]]):
        """
        Normalize the iterator to yield dict rows for CSV when possible.
        If given iterables and fieldnames provided, map by index.
        """
        nonlocal fieldnames
        it = iter(it)

        try:
            first = next(it)
        except StopIteration:
            return iter([])

        # Determine row type and fieldnames
        if isinstance(first, Mapping):
            if fieldnames is None:
                fieldnames = list(first.keys())

            def gen() -> Iterator[Mapping[str, Any]]:
                yield first
                for r in it:
                    yield r  # expected dict-like
            return gen()
        else:
            # Row is sequence (list/tuple). Require fieldnames.
            if not fieldnames:
                # fall back to generic colN names
                fieldnames = [f"col{i}" for i in range(len(first))]

            def gen() -> Iterator[Mapping[str, Any]]:
                yield {k: v for k, v in zip(fieldnames, first)}
                for r in it:
                    yield {k: v for k, v in zip(fieldnames, r)}
            return gen()

    if fmt == "csv":
        dict_iter = _as_dict_iter(rows)

        def generate_csv():
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames or [])
            # header
            writer.writeheader()
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            # rows
            for row in dict_iter:
                writer.writerow(row)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Accel-Buffering": "no",  # hint for some proxies to not buffer
        }
        return Response(
            stream_with_context(generate_csv()),
            mimetype=mimetype,
            headers=headers,
        )

    # jsonl (one JSON object per line)
    def generate_jsonl():
        for row in rows:
            if isinstance(row, Mapping):
                yield json.dumps(row, ensure_ascii=False) + "\n"
            else:
                # if it's a sequence, wrap with indices or provided fieldnames
                if fieldnames:
                    obj = {k: v for k, v in zip(fieldnames, row)}
                else:
                    obj = list(row)
                yield json.dumps(obj, ensure_ascii=False) + "\n"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename.replace(".csv", ".jsonl")}"',
        "X-Accel-Buffering": "no",
    }
    return Response(
        stream_with_context(generate_jsonl()),
        mimetype=mimetype,
        headers=headers,
    )


# ────────────────────────────── Misc small helpers ───────────────────────────
def clamp_int(value: Any, default: int, min_value: int, max_value: int) -> int:
    """
    Safely convert an incoming value to int and clamp to [min_value, max_value].
    """
    try:
        x = int(str(value).strip())
    except Exception:
        x = default
    return max(min_value, min(max_value, x))


def get_pagination_from_args(
    default_page: int = 1,
    default_per_page: int = 20,
    max_per_page: int = 200,
) -> Tuple[int, int]:
    """
    Read ?page= and ?per_page= from request.args with sane clamping.
    """
    page = clamp_int(
        request.args.get("page"),
        default=default_page,
        min_value=1,
        max_value=10**9,
    )
    per_page = clamp_int(
        request.args.get("per_page"),
        default=default_per_page,
        min_value=1,
        max_value=max_per_page,
    )
    return page, per_page


__all__ = [
    # decorators
    "login_required",
    "mfa_required",
    "roles_required",
    "optional_jwt",
    # sorting / export
    "sanitize_direction",
    "sanitize_sort",
    "stream_export",
    # misc
    "clamp_int",
    "get_pagination_from_args",
]
