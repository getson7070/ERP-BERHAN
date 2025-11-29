from pathlib import Path


def main() -> int:
    """
    Disaster-recovery drill stub.
    Writes a tiny CSV marker that can be asserted in tests or by ops.
    """
    Path("dr-drill.csv").write_text("drill,complete\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
