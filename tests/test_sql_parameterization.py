from pathlib import Path

TARGET_FILES = [
    "erp/audit.py",
    "erp/data_retention.py",
    "BOT.PY",
    "erp/routes/analytics.py",
]


def test_no_question_mark_placeholders() -> None:
    for file in TARGET_FILES:
        lines = Path(file).read_text().splitlines()
        for line in lines:
            if ("execute(" in line or " text(" in line) and "safe_execute" not in line:
                assert "?" not in line, f"Found '?' placeholder in {file}: {line}"
