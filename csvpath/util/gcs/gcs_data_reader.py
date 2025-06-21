# pylint: disable=C0114
import csv
from smart_open import open
from csvpath.util.hasher import Hasher
from ..file_readers import CsvDataReader
from .gcs_utils import GcsUtility
from .gcs_fingerprinter import GcsFingerprinter


class GcsDataReader(CsvDataReader):
    def load_if(self) -> None:
        if self.source is None:
            client = GcsUtility.make_client()
            try:
                self.source = open(
                    self.path, self.mode, transport_params={"client": client}
                )
            except DeprecationWarning:
                ...

    def next(self) -> list[str]:
        with open(
            uri=self.path,
            mode=self.mode,
            transport_params={"client": GcsUtility.make_client()},
        ) as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def fingerprint(self) -> str:
        self.load_if()
        h = GcsFingerprinter().fingerprint(self.path)
        h = Hasher.percent_encode(h)
        self.close()
        return h

    def exists(self, path: str) -> bool:
        return GcsUtility.exists(path)

    def remove(self, path: str) -> None:
        bucket, blob = self.path_to_parts(path)
        GcsUtility.remove(bucket, blob)

    def rename(self, path: str, new_path: str) -> None:
        source_bucket, source_blob = self.path_to_parts(path)
        dest_bucket, dest_blob = self.path_to_parts(new_path)
        GcsUtility.rename(source_bucket, source_blob, dest_bucket, dest_blob)

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here for cloud services? Can leave for now.
        return {}
