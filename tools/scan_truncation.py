
import sys, pathlib

MARKERS = ["<<<", ">>>", "--- a/", "+++ b/", "\n...\n", "\u2026"]

def main(path):
    root = pathlib.Path(path)
    issues = []
    for p in root.rglob("*.py"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(m in txt for m in MARKERS):
            issues.append(str(p))
    if issues:
        print("Truncated/garbled files:")
        print("\n".join(issues))
        sys.exit(1)
    print("No truncation markers found.")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv)>1 else ".")
