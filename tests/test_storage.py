import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from erp.storage import generate_presigned_url


def test_presigned(monkeypatch):
    monkeypatch.setenv("S3_ENDPOINT", "https://s3.example.com")
    monkeypatch.setenv("S3_BUCKET", "bucket")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "a")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "b")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    url = generate_presigned_url("sample.txt")
    assert "sample.txt" in url


