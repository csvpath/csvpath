# pylint: disable=C0114

import os
from smart_open import open
from ..file_writers import DataFileWriter
from csvpath.util.azure.azure_utils import AzureUtility


class AzureDataWriter(DataFileWriter):
    _write_file_count = 0

    def load_if(self) -> None:
        if self.sink is None:
            client = AzureUtility.make_client()
            self.sink = open(
                self.path,
                self._mode,
                transport_params={"client": client},
            )
            AzureDataWriter._write_file_count += 1

    def write(self, data) -> None:
        """this is a one-and-done write in mode 'w'. you don't use the data writer
        as a context manager for this method. for multiple write calls to the same
        file handle use append().
        """
        client = AzureUtility.make_client()
        with open(self.path, "wb", transport_params={"client": client}) as file:
            file.write(data.encode("utf-8"))

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
