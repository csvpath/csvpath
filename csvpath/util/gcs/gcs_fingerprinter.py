import hashlib
from google.cloud import storage
from .gcs_utils import GcsUtility
from ..hasher import Hasher


class GcsFingerprinter:
    def fingerprint(self, path: str) -> str:
        bucket, blob = GcsUtility.path_to_parts(path)
        return self.fingerprint_object(bucket, blob)

    def fingerprint_object(self, bucket: str, blob: str) -> str:
        h = self.get_sha(bucket, blob)
        if h is None:
            h = self.generate_fingerprint(bucket, blob)
            #
            # Set the properties for future use
            #
            blob_obj = GcsUtility.make_client().bucket(bucket).blob(blob)
            blob_obj.metadata = {"sha256": h}
            blob_obj.patch()  # Update metadata in GCS
        return h

    def get_sha(self, bucket: str, blob: str) -> str:
        blob_obj = GcsUtility.make_client().bucket(bucket).blob(blob)
        blob_obj.reload()  # Ensure metadata is up-to-date
        if blob_obj.metadata and "sha256" in blob_obj.metadata:
            return blob_obj.metadata["sha256"]
        return None

    def generate_fingerprint(self, bucket: str, blob: str) -> str:
        """Downloads the blob and calculates its SHA256 hash."""
        client = GcsUtility.make_client()
        blob_obj = client.bucket(bucket).blob(blob)
        sha256 = hashlib.sha256()
        try:
            with blob_obj.open("rb") as download_stream:
                for chunk in download_stream:
                    sha256.update(chunk)
            h = sha256.hexdigest()
            h = Hasher.percent_encode(h)
            return h
        except Exception as e:
            raise e
