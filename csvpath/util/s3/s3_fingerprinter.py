import boto3
import uuid
from .s3_utils import S3Utils
from csvpath.util.box import Box


class S3Fingerprinter:
    def __init__(self) -> None:
        self._client = None

    @property
    def client(self):
        if self._client is None:
            box = Box()
            self._client = box.get(Box.BOTO_S3_CLIENT)
            if self._client is None:
                self._client = S3Utils.make_client()
                box.add(Box.BOTO_S3_CLIENT, self._client)
        return self._client

    def fingerprint(self, path: str) -> str:
        bucket, key = S3Utils.path_to_parts(path)
        return self.fingerprint_object(bucket, key)

    def fingerprint_object(self, bucket, key) -> str:
        h = self.get_sha(bucket, key)
        if h is None:
            h = self.generate_fingerprint(bucket, key)
        return h

    def get_sha(self, bucket: str, key: str) -> str:
        client = self.client
        response = client.get_object_attributes(
            Bucket=bucket, Key=key, ObjectAttributes=["Checksum"]
        )
        if "Checksum" in response:
            if "ChecksumSHA256" in response["Checksum"]:
                return response["Checksum"]["ChecksumSHA256"]
        return None

    def generate_fingerprint(self, bucket: str, key: str) -> str:
        client = self.client
        temp_key = f"temp/{str(uuid.uuid4())}/{key}"
        try:
            # Copy the file to temp location, requesting checksum calculation
            response = client.copy_object(
                Bucket=bucket,
                CopySource={"Bucket": bucket, "Key": key},
                Key=temp_key,
                ChecksumAlgorithm="SHA256",
            )
            # Get the checksum from the response
            sha256 = response["CopyObjectResult"]["ChecksumSHA256"]
            # Copy back to original location
            client.copy_object(
                Bucket=bucket, CopySource={"Bucket": bucket, "Key": temp_key}, Key=key
            )
            c = self.client
            S3Utils.remove(bucket, temp_key, client=c)
            return sha256
        except Exception as e:
            try:
                # Clean up temp file if dangling
                client.delete_object(Bucket=bucket, Key=temp_key)
            except Exception:
                pass
            raise e
