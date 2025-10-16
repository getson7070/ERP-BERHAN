import os, subprocess, sys, shlex

    ALEMBIC = ["alembic", "-c", "alembic.ini"]

    def run(*args):
        proc = subprocess.run(list(args), text=True, capture_output=True)
        return proc.returncode, (proc.stdout or "") + (("
"+proc.stderr) if proc.stderr else "")

    def a(*sub):
        rc, out = run(*ALEMBIC, *sub)
        print(f"$ alembic -c alembic.ini {' '.join(sub)}\n{out}", flush=True)
        return rc, out

    def main():
        # 1) sanity: show heads
        rc, heads_out = a("heads", "--verbose")
        if rc != 0:
            sys.exit(1)

        # 2) detect multiple heads
        rc, out = a("heads")
        head_lines = [ln.strip() for ln in out.splitlines() if ln.strip().startswith("Rev:")]
        head_ids = []
        for ln in head_lines:
            # "Rev: X (head)"
            parts = ln.split()
            if len(parts) >= 2:
                head_ids.append(parts[1])
        head_ids = list(dict.fromkeys(head_ids))  # dedupe preserving order

        auto_merge = os.getenv("AUTO_MERGE_MIGRATIONS") == "1"
        if len(head_ids) > 1:
            if not auto_merge:
                print(f"[predeploy] Multiple heads detected: {head_ids}. Set AUTO_MERGE_MIGRATIONS=1 to merge in staging.", flush=True)
                sys.exit(1)
            # merge
            msg = "Auto-merge heads " + ", ".join(head_ids)
            rc, out = a("merge", "-m", msg, *head_ids)
            if rc != 0:
                sys.exit(1)

        # 3) upgrade
        rc, out = a("upgrade", "head")
        if rc != 0:
            # If failure says "Can't locate revision", do not attempt auto-fix here
            sys.exit(1)

        print("[predeploy] Migrations upgraded to head.", flush=True)

    if __name__ == "__main__":
        sys.exit(main())
