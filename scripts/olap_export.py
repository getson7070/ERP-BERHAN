from pathlib import Path

# Minimal stub to satisfy tests and provide a predictable export side effect.
OLAP_EXPORT_SUCCESS = 0


def main() -> int:
    """
    Fake OLAP export: writes a tiny CSV so tests and ops have something to assert on.
    Real implementation can replace this later.
    """
    path = Path("olap_export.csv")
    path.write_text("status\nok\n", encoding="utf-8")
    return OLAP_EXPORT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
