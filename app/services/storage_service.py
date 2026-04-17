import os
import uuid
import hashlib
import time
import hmac
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
    def __init__(self, cloud_name: str = None, api_key: str = None):
        self.cloud_name = cloud_name or os.getenv("CLOUDINARY_CLOUD_NAME", "")
        self.api_key = api_key or os.getenv("CLOUDINARY_API_KEY", "")
        self.api_secret = os.getenv("CLOUDINARY_API_SECRET", "")

    def _generate_signature(self, timestamp: int) -> str:
        """Generate Cloudinary API signature"""
        signature = f"timestamp={timestamp}{self.api_secret}"
        return hashlib.sha256(signature.encode()).hexdigest()

    def save(self, content: bytes, filename: str) -> str:
        import requests

        if not self.cloud_name or not self.api_key:
            raise ValueError("Cloudinary credentials not configured")

        timestamp = int(time.time())
        signature = self._generate_signature(timestamp)

        url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/upload"

        files = {"file": (filename, content, "image/jpeg")}

        data = {
            "api_key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "folder": "marketplace",
            "public_id": filename.split(".")[0],
        }

        response = requests.post(url, files=files, data=data, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Cloudinary upload failed: {response.text}")

        result = response.json()
        return result.get("public_id", filename)

    def delete(self, filename: str) -> None:
        import requests

        if not self.cloud_name or not self.api_key:
            return

        timestamp = int(time.time())
        signature = self._generate_signature(timestamp)

        url = f"https://api.cloudinary.com/v1_1/{self.cloud_name}/image/destroy"

        data = {
            "api_key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "public_id": filename,
        }

        try:
            requests.post(url, data=data, timeout=10)
        except Exception:
            pass

    def get_url(self, filename: str) -> str:
        if not self.cloud_name:
            return filename

        return f"https://res.cloudinary.com/{self.cloud_name}/image/upload/{filename}"


def get_storage_service() -> StorageService:
    storage_type = os.getenv("STORAGE_TYPE", "local")

    if storage_type == "s3":
        return S3StorageService()
    elif storage_type == "cloudinary":
        return CloudinaryStorageService()
    else:
        return LocalStorageService()


storage_service = get_storage_service()
