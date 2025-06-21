import csv
from smart_open import open
from csvpath.util.hasher import Hasher
from ..file_readers import CsvDataReader
from .azure_utils import AzureUtility
from .azure_fingerprinter import AzureFingerprinter


class AzureDataReader(CsvDataReader):
    def load_if(self) -> None:
        if self.source is None:
            client = AzureUtility.make_client()
            try:
                self.source = open(
                    self.path, self.mode, transport_params={"client": client}
                )
            except DeprecationWarning:
                ...

    def next(self) -> list[str]:
        if self.is_binary:
            raise ValueError("CSV files must be opened in text mode, not binary.")
        with open(
            uri=self.path,
            mode=self.mode,
            encoding=self.encoding,
            transport_params={"client": AzureUtility.make_client()},
        ) as file:
            reader = csv.reader(
                file, delimiter=self._delimiter, quotechar=self._quotechar
            )
            for line in reader:
                yield line

    def fingerprint(self) -> str:
        self.load_if()
        h = AzureFingerprinter().fingerprint(self.path)
        h = Hasher.percent_encode(h)
        self.close()
        return h

    def exists(self, path: str) -> bool:
        return AzureUtility.exists(path)

    def remove(self, path: str) -> None:
        container, blob = self.path_to_parts(path)
        AzureUtility.remove(container, blob)

    def rename(self, path: str, new_path: str) -> None:
        source_container, source_blob = self.path_to_parts(path)
        dest_container, dest_blob = self.path_to_parts(new_path)
        AzureUtility.rename(source_container, source_blob, dest_container, dest_blob)
