import os
import io
from typing import Protocol, Optional
from abc import ABC, abstractmethod
from app.core.config import get_settings

settings = get_settings()


class StorageService(Protocol):
    def save(self, content: bytes, filename: str) -> str: ...
    def delete(self, filename: str) -> None: ...
    def get_url(self, filename: str) -> str: ...


class LocalStorageService:
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or settings.UPLOAD_DIR

    def save(self, content: bytes, filename: str) -> str:
        filepath = os.path.join(self.base_dir, filename)
        with open(filepath, "wb") as f:
            f.write(content)
        return filename

    def delete(self, filename: str) -> None:
        filepath = os.path.join(self.base_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)

    def get_url(self, filename: str) -> str:
        return f"/uploads/{filename}"


class S3StorageService:
    def __init__(self, bucket: str = None, region: str = "us-east-1"):
        self.bucket = bucket or os.getenv("S3_BUCKET", "")
        self.region = region
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client("s3", region_name=self.region)
        return self._client

    def save(self, content: bytes, filename: str) -> str:
        key = f"uploads/{filename}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return filename

    def delete(self, filename: str) -> None:
        key = f"uploads/{filename}"
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except Exception:
            pass

    def get_url(self, filename: str) -> str:
        return (
            f"https://{self.bucket}.s3.{self.region}.amazonaws.com/uploads/{filename}"
        )


class CloudinaryStorageService:
    def __init__(self):
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
        api_key = os.getenv("CLOUDINARY_API_KEY", "")
        api_secret = os.getenv("CLOUDINARY_API_SECRET", "")

        if not cloud_name:
            raise ValueError("CLOUDINARY_CLOUD_NAME not configured")

        import cloudinary

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )

        self._cloudinary = cloudinary

    def save(self, content: bytes, filename: str) -> str:
        import cloudinary
        import cloudinary.uploader

        result = cloudinary.uploader.upload(
            io.BytesIO(content),
            folder="marketplace",
            public_id=filename.split(".")[0],
            resource_type="image",
        )
        return result.get("public_id", filename)

    def delete(self, filename: str) -> None:
        import cloudinary.uploader

        try:
            cloudinary.uploader.destroy(filename)
        except Exception:
            pass

    def get_url(self, filename: str) -> str:
        from cloudinary import CloudinaryImage

        img = CloudinaryImage(filename)
        return img.build_url(resource_type="image")


def get_storage_service() -> StorageService:
    storage_type = os.getenv("STORAGE_TYPE", "local")

    if storage_type == "s3":
        return S3StorageService()
    elif storage_type == "cloudinary":
        return CloudinaryStorageService()
    else:
        return LocalStorageService()


storage_service = get_storage_service()
