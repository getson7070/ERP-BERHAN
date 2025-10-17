from pathlib import Path
import sys

# Directories/files to confirm (tweak as needed)
REQUIRED = [
    "templates/base.html",
    "templates/auth/login.html",
    "templates/auth/register.html",
]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    missing = []
    for rel in REQUIRED:
        p = (repo_root / rel).resolve()
        if not p.exists():
            missing.append(rel)
    if missing:
        sys.stderr.write(
            "Missing required templates:\n - " + "\n - ".join(missing) + "\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
