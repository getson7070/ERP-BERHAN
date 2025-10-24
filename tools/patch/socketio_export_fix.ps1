param([Parameter(Mandatory=$true)][string]$RepoPath)
$ErrorActionPreference = "Stop"
$target = Join-Path $RepoPath "erp\__init__.py"
if (!(Test-Path $target)) { throw "erp\__init__.py not found at $RepoPath" }
$content = Get-Content $target -Raw
if ($content -match "(?s)socketio\s*=" -and $content -match "__all__") {
  Write-Host "[socketio-fix] socketio export appears present. Skipping."
  exit 0
}
$insertion = @'
# --- [autogen] SocketIO export invariant (idempotent) ---
try:
    from flask_socketio import SocketIO  # type: ignore
    if "socketio" not in globals():
        _app_for_socket = None
        try:
            if "create_app" in globals():
                _app_for_socket = create_app(testing=True) if "testing" in create_app.__code__.co_varnames else create_app()
        except Exception:
            _app_for_socket = None
        socketio = SocketIO(_app_for_socket, cors_allowed_origins="*")  # noqa: F401
        try:
            __all__  # noqa
        except NameError:
            __all__ = []
        if "socketio" not in __all__:
            __all__.append("socketio")
except Exception as _e:
    pass
# --- [/autogen] ---
'@
Set-Content -Path $target -Value ($content + "`n`n" + $insertion) -Encoding UTF8
Write-Host "[socketio-fix] inserted socketio export invariant"
