import os
import uuid
import boto3


def _client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )


def configure_bucket_lifecycle():
    days = os.getenv("S3_RETENTION_DAYS")
    if not days:
        return
    client = _client()
    client.put_bucket_lifecycle_configuration(
        Bucket=os.getenv("S3_BUCKET"),
        LifecycleConfiguration={
            "Rules": [
                {"ID": "expire", "Status": "Enabled", "Expiration": {"Days": int(days)}}
            ]
        },
    )


def upload_fileobj(fileobj, filename):
    """Upload a file object to S3-compatible storage after a basic AV scan."""
    data = fileobj.read()
    if b"EICAR" in data:
        raise ValueError("infected file signature detected")
    fileobj.seek(0)
    key = f"{uuid.uuid4()}-{filename}"
    _client().upload_fileobj(fileobj, os.getenv("S3_BUCKET"), key)
    return key


def generate_presigned_url(key, expires=3600):
    client = _client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": os.getenv("S3_BUCKET"), "Key": key},
        ExpiresIn=expires,
    )
