from __future__ import annotations

import hashlib
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    send_file,
    send_from_directory,
)
from werkzeug.utils import safe_join

bp = Blueprint("main", __name__)

_UI_KIT_ARCHIVE = "modern-ui-kit.zip"
_UI_KIT_DIRECTORY = "modern-ui-kit"


def _repo_root() -> Path:
    """Resolve the repository root from the Flask application context."""

    root = Path(current_app.root_path).parent
    override = current_app.config.get("REPO_ROOT")
    if override:
        root = Path(override)
    return root.resolve()


def _resolve_within_repo(raw_path: str | Path | None, *, default: Path) -> Path:
    """Resolve a configured path ensuring it remains within the repository boundary."""

    candidate = Path(raw_path) if raw_path else default
    if not candidate.is_absolute():
        candidate = (_repo_root() / candidate).resolve()
    else:
        candidate = candidate.resolve()

    repo_root = _repo_root()
    try:
        candidate.relative_to(repo_root)
    except ValueError:  # pragma: no cover - defensive guard
        abort(403, "Configured path must reside within the repository root")

    return candidate


def _ui_kit_archive_path() -> Path:
    default = _repo_root() / "ui-preview" / _UI_KIT_ARCHIVE
    raw = current_app.config.get("UI_KIT_ARCHIVE")
    return _resolve_within_repo(raw, default=default)


def _ui_kit_directory() -> Path:
    default = _repo_root() / "ui-preview" / _UI_KIT_DIRECTORY
    raw = current_app.config.get("UI_KIT_DIRECTORY")
    return _resolve_within_repo(raw, default=default)


@bp.get("/")
def root():
    """Redirect the root request to the workspace chooser."""

    return redirect("/choose_login", code=302)


@bp.get("/choose_login")
def choose_login():
    """Allow users to pick their role-specific workspace."""

    roles = [
        {"key": "admin", "label": "Admin"},
        {"key": "sales", "label": "Sales"},
        {"key": "store", "label": "Storekeeper"},
        {"key": "finance", "label": "Finance"},
        {"key": "tech", "label": "Technical"},
    ]
    return render_template("choose_login.html", roles=roles)


@bp.get("/ui-kit")
def ui_kit() -> str:
    """Render a landing page describing the UI kit and download options."""

    archive_path = _ui_kit_archive_path()
    archive_exists = archive_path.is_file()
    archive_checksum = None
    archive_size = None
    if archive_exists:
        archive_checksum = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        archive_size = archive_path.stat().st_size

    base_dir = _ui_kit_directory()
    assets_available = base_dir.is_dir()
    asset_definitions = [
        ("Base layout", "templates/base.html"),
        ("Home dashboard", "templates/home.html"),
        ("Operations dashboard", "templates/dashboard.html"),
        ("Workspace chooser", "templates/choose_login.html"),
        ("Authentication page", "templates/auth/login.html"),
        ("Design system stylesheet", "static/css/base.css"),
        ("Navigation script", "static/js/navigation.js"),
        ("Theme preferences script", "static/js/theme-preferences.js"),
    ]

    asset_rows = []
    if assets_available:
        for label, relative_path in asset_definitions:
            file_path = base_dir / relative_path
            exists = file_path.is_file()
            asset_rows.append(
                {
                    "label": label,
                    "relative_path": relative_path,
                    "exists": exists,
                    "size": file_path.stat().st_size if exists else None,
                }
            )

    return render_template(
        "ui_kit.html",
        archive_available=archive_exists,
        assets_available=assets_available,
        archive_checksum=archive_checksum,
        archive_size=archive_size,
        asset_rows=asset_rows,
    )


@bp.get("/ui-kit/download")
def download_ui_kit():
    """Deliver the zipped UI kit so designers can download it locally."""

    archive_path = _ui_kit_archive_path()
    if not archive_path.is_file():
        abort(404, "UI kit archive is not available on this deployment")

    return send_file(
        archive_path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=_UI_KIT_ARCHIVE,
        max_age=3600,
        conditional=True,
    )


@bp.get("/ui-kit/assets/<path:asset>")
def download_ui_kit_asset(asset: str):
    """Serve individual files from the UI kit with path traversal protection."""

    base_dir = _ui_kit_directory()
    if not base_dir.is_dir():
        abort(404, "UI kit assets are not available on this deployment")

    safe_path = safe_join(str(base_dir), asset)
    if safe_path is None:
        abort(404)

    file_path = Path(safe_path)
    if not file_path.exists() or not file_path.is_file():
        abort(404)

    return send_from_directory(
        file_path.parent,
        file_path.name,
        as_attachment=True,
        max_age=3600,
        conditional=True,
    )
