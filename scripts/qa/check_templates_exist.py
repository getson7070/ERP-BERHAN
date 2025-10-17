from pathlib import Path
import sys

TEMPLATES = [
    "templates/base.html",
    "templates/index.html",
]

def main():
    repo = Path(__file__).resolve().parents[2]
    missing = [p for p in TEMPLATES if not (repo / p).exists()]
    if missing:
        print("Missing templates:", ", ".join(missing))
        sys.exit(1)
    print("All required templates exist.")

if __name__ == "__main__":
    main()
