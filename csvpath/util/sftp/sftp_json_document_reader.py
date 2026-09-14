import json
from .sftp_data_reader import SftpDataReader


class SftpJsonDocumentReader(SftpDataReader):
    def next(self) -> list[str]:
        with self as file:
            yield json.load(file.source)
