"""
S3 client module for uploading files to S3-compatible storage services.
Supports AWS S3, MinIO, and other S3-compatible providers.
"""

import os
import logging
from typing import Optional, Any
import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)

MOODLE_URL: str = "https://moodle.ucl.ac.uk"


class S3Client:
    """Client for interacting with S3-compatible storage services."""

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region_name: str = "us-east-1",
    ) -> None:
        if boto3 is None:
            raise ImportError(
                "boto3 must be installed to use S3Client. Run: pip install boto3"
            )

        self.access_key: Optional[str] = access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key: Optional[str] = secret_key or os.getenv(
            "AWS_SECRET_ACCESS_KEY"
        )
        self.endpoint_url: Optional[str] = endpoint_url or os.getenv(
            "AWS_S3_ENDPOINT_URL"
        )
        self.bucket_name: Optional[str] = bucket_name or os.getenv("AWS_S3_BUCKET_NAME")
        self.region_name: str = region_name

        if not self.access_key or not self.secret_key:
            raise ValueError(
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be provided"
            )

        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET_NAME must be provided")

        # Initialize S3 client
        self.client: Any = boto3.client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
        )

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> dict[str, Any]:
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Use filename if object_name not provided
            if object_name is None:
                object_name = os.path.basename(file_path)

            # Determine content type if not provided
            if content_type is None:
                content_type = self._get_content_type(file_path)

            # Upload file
            self.client.upload_file(
                file_path,
                self.bucket_name,
                object_name,
                ExtraArgs={"ContentType": content_type} if content_type else {},
            )

            # Generate URL
            url = self._generate_url(object_name)

            return {
                "success": True,
                "s3_key": object_name,
                "url": url,
                "bucket": self.bucket_name,
            }

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Cannot upload file: {e}")
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            raise

    def upload_file_from_bytes(
        self,
        file_bytes: bytes,
        object_name: str,
        content_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Upload file from bytes to S3 bucket.

        Args:
            file_bytes: File content as bytes
            object_name: S3 object name
            content_type: MIME type of the file

        Returns:
            Dictionary with 'success' status, 's3_key', and 'url'

        Raises:
            ClientError: If S3 operation fails
        """
        try:
            extra_args: dict[str, Any] = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_bytes,
                **extra_args,
            )

            url = self._generate_url(object_name)

            return {
                "success": True,
                "s3_key": object_name,
                "url": url,
                "bucket": self.bucket_name,
            }

        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            raise

    def download_file(
        self,
        object_name: str,
        file_path: str,
    ) -> dict[str, Any]:
        """
        Download a file from S3 bucket.

        Args:
            object_name: S3 object name
            file_path: Local path to save the file

        Returns:
            Dictionary with 'success' status and file path

        Raises:
            ClientError: If S3 operation fails
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            self.client.download_file(self.bucket_name, object_name, file_path)

            return {
                "success": True,
                "file_path": file_path,
                "object_name": object_name,
            }

        except Exception as e:
            logger.error(f"S3 download error: {e}")
            raise

    def delete_file(self, object_name: str) -> dict[str, Any]:
        """
        Delete a file from S3 bucket.

        Args:
            object_name: S3 object name

        Returns:
            Dictionary with 'success' status

        Raises:
            ClientError: If S3 operation fails
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_name)

            return {
                "success": True,
                "object_name": object_name,
                "message": f"Successfully deleted {object_name}",
            }

        except Exception as e:
            logger.error(f"S3 delete error: {e}")
            raise

    def list_objects(self, prefix: str = "") -> dict[str, Any]:
        """
        List objects in S3 bucket with optional prefix.

        Args:
            prefix: Prefix to filter objects

        Returns:
            Dictionary with 'success' status and list of objects

        Raises:
            ClientError: If S3 operation fails
        """
        try:
            response: dict[str, Any] = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
            )

            objects: list[dict[str, Any]] = []
            if "Contents" in response:
                objects = [
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                    }
                    for obj in response["Contents"]
                ]

            return {
                "success": True,
                "objects": objects,
                "count": len(objects),
            }

        except Exception as e:
            logger.error(f"S3 list error: {e}")
            raise

    def _generate_url(self, object_name: str) -> str:
        """
        Generate URL for an S3 object.

        Args:
            object_name: S3 object name

        Returns:
            URL to the object
        """
        if self.endpoint_url:
            # For custom endpoints (MinIO, etc.)
            return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
        else:
            # For AWS S3
            return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{object_name}"

    @staticmethod
    def _get_content_type(file_path: str) -> str:
        """
        Determine MIME type based on file extension.

        Args:
            file_path: Path to the file

        Returns:
            MIME type string
        """
        import mimetypes

        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def get_presigned_url(
        self,
        object_name: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for an S3 object.

        Args:
            object_name: S3 object name
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL

        Raises:
            ClientError: If S3 operation fails
        """
        try:
            url: str = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
            return url
        except Exception as e:
            logger.error(f"S3 presigned URL error: {e}")
            raise

    def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            object_name: S3 object name

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except Exception as e:
            logger.debug(f"File existence check: {e}")
            return False


# Singleton instance for easy access
_s3_client: Optional[S3Client] = None


def get_s3_client(
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    bucket_name: Optional[str] = None,
    region_name: str = "us-east-1",
) -> S3Client:
    """
    Factory function to create and return an S3 client instance.

    Args:
        access_key: AWS Access Key ID
        secret_key: AWS Secret Access Key
        endpoint_url: S3 endpoint URL
        bucket_name: S3 bucket name
        region_name: AWS region

    Returns:
        Initialized S3Client instance
    """
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client(
            access_key=access_key,
            secret_key=secret_key,
            endpoint_url=endpoint_url,
            bucket_name=bucket_name,
            region_name=region_name,
        )
    return _s3_client


def upload_file_to_s3(
    file_path: str,
    s3_key: str,
    metadata: Optional[dict[str, Any]] = None,
    content_type: Optional[str] = None,
) -> bool:
    """
    Convenience function to upload a file to S3 using the singleton client.

    Args:
        file_path: Local path to the file to upload
        s3_key: S3 object key (path in bucket)
        metadata: Optional metadata dictionary
        content_type: Optional content type (MIME type)

    Returns:
        True if upload successful, False otherwise
    """
    try:
        client = get_s3_client()
        client.upload_file(file_path, s3_key, content_type)
        return True
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        return False


def upload_bytes_to_s3(
    file_bytes: bytes,
    s3_key: str,
    metadata: Optional[dict[str, Any]] = None,
    content_type: Optional[str] = None,
) -> bool:
    """
    Convenience function to upload bytes to S3 using the singleton client.

    Args:
        file_bytes: Bytes content to upload
        s3_key: S3 object key (path in bucket)
        metadata: Optional metadata dictionary
        content_type: Optional content type (MIME type)

    Returns:
        True if upload successful, False otherwise
    """
    try:
        client = get_s3_client()
        client.upload_file_from_bytes(file_bytes, s3_key, content_type)
        return True
    except Exception as e:
        logger.error(f"Failed to upload bytes: {e}")
        return False
