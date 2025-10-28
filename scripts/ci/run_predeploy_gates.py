from erp.security_hardening import safe_run, safe_call, safe_popen
import os, sys, importlib, subprocess
STRICT = os.getenv("PREDEPLOY_STRICT", "1") != "0"
def run_py(path, hard=True):
    if not os.path.exists(path):
        print(f"[gate] SKIP (missing): {path}")
        return True
    print(f"[gate] RUN {path}")
    code = safe_call([sys.executable, path])
    if code != 0:
        print(f"[gate] FAIL: {path}", file=sys.stderr)
        if hard or STRICT: sys.exit(code)
        return False
    return True
def main():
    try:
        erp = importlib.import_module('erp')
        create_app = getattr(erp, 'create_app')
        socketio = getattr(erp, 'socketio')
        _ = create_app(testing=True) if 'testing' in create_app.__code__.co_varnames else create_app()
        print('[gate] import invariant OK')
    except Exception as e:
        print('[gate] import invariant FAILED:', e, file=sys.stderr)
        sys.exit(1)
    run_py('scripts/check_alembic_single_head.py', hard=True)
    run_py('scripts/validate_csp.py', hard=True)
    print('[gates] all mandatory checks passed.')
    sys.exit(0)
if __name__ == '__main__':
    main()

