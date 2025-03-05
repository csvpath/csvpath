import hashlib
from azure.storage.blob import BlobServiceClient, BlobClient
from .azure_utils import AzureUtility
from ..hasher import Hasher


class AzureFingerprinter:
    def fingerprint(self, path: str) -> str:
        container, blob = AzureUtility.path_to_parts(path)
        return self.fingerprint_object(container, blob)

    def fingerprint_object(self, container: str, blob: str) -> str:
        h = self.get_sha(container, blob)
        if h is None:
            h = self.generate_fingerprint(container, blob)
            #
            # set the properties for future use
            #
            bc = AzureUtility.make_client().get_blob_client(
                container=container, blob=blob
            )
            bc.set_blob_metadata({"sha256": h})
        return h

    def get_sha(self, container: str, blob: str) -> str:
        blob_client = AzureUtility.make_client().get_blob_client(
            container=container, blob=blob
        )
        properties = blob_client.get_blob_properties()
        if "metadata" in properties and "sha256" in properties["metadata"]:
            return properties["metadata"]["sha256"]
        return None

    def generate_fingerprint(self, container: str, blob: str) -> str:
        """Downloads the blob and calculates its SHA256 hash."""
        #
        # don't love this being outside Hasher. not today's problem.
        #
        client = AzureUtility.make_client()
        blob_client = client.get_blob_client(container=container, blob=blob)
        sha256 = hashlib.sha256()
        try:
            download_stream = blob_client.download_blob()
            for chunk in download_stream.chunks():
                sha256.update(chunk)
            h = sha256.hexdigest()
            h = Hasher.percent_encode(h)
            return h
        except Exception as e:
            raise e
