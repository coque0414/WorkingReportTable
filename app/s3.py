# app/s3.py
import os
import uuid
from datetime import date
import boto3

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

_s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def build_file_key(work_date: date, filename: str) -> str:
    # 확장자 보존(없으면 jpg로)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    uid = uuid.uuid4().hex
    return f"work-logs/{work_date.isoformat()}/{uid}.{ext}"

def create_presigned_put_url(file_key: str, content_type: str, expires_in: int = 60) -> str:
    # 업로드(PUT)용 presigned url 생성
    return _s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": AWS_S3_BUCKET,
            "Key": file_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )

def create_presigned_get_url(
    file_key: str,
    expires_in: int = 300,
    response_content_type: str | None = None,
    as_attachment: bool = False,
    download_filename: str | None = None,
) -> str:
    params: dict = {
        "Bucket": AWS_S3_BUCKET,
        "Key": file_key,
    }

    # 브라우저에서 열 때 content-type 힌트
    if response_content_type:
        params["ResponseContentType"] = response_content_type

    # 다운로드로 강제하고 싶으면 content-disposition 사용
    if as_attachment:
        filename = download_filename or os.path.basename(file_key)
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

    return _s3.generate_presigned_url(
        ClientMethod="get_object",
        Params=params,
        ExpiresIn=expires_in,
    )