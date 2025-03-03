# pylint: disable=C0114

import os
from smart_open import open
from csvpath.util.box import Box
from ..file_writers import DataFileWriter
from .sftp_config import SftpConfig


class SftpDataWriter(DataFileWriter):
    def load_if(self) -> None:
        if self.sink is None:
            config = Box.STUFF.get(Box.CSVPATHS_CONFIG)
            c = SftpConfig(config)
            self.sink = open(
                self.path,
                self._mode,
                newline="",
                transport_params={
                    "connect_kwargs": {"username": c.username, "password": c.password}
                },
            )

    def write(self, data) -> None:
        config = Box.STUFF.get(Box.CSVPATHS_CONFIG)
        c = SftpConfig(config)
        with open(
            self.path,
            self._mode,
            newline="",
            transport_params={
                "connect_kwargs": {"username": c.username, "password": c.password}
            },
        ) as sink:
            sink.write(data)

    def file_info(self) -> dict[str, str | int | float]:
        # TODO: what can/should we provide here?
        return {}
