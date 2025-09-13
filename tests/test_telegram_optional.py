import pytest

pytest.importorskip("telegram")

def test_bot_main_importable():
    from bot import main  # noqa: F401

