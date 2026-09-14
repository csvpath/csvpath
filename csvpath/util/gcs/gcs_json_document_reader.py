import json
from .gcs_data_reader import GcsDataReader


class GcsJsonDocumentReader(GcsDataReader):
    def next(self) -> list[str]:
        with self as file:
            yield json.load(file.source)
