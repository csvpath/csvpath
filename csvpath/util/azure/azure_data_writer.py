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
                self.mode,
                transport_params={"client": client},
                newline=''
            )
            AzureDataWriter._write_file_count += 1

    def write(self, data) -> None:
        if self.is_binary and not isinstance(data, bytes):
            data = data.encode(self.encoding)
        self.sink.write(data)

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
