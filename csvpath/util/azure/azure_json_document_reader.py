import json
from .azure_data_reader import AzureDataReader


class AzureJsonDocumentReader(AzureDataReader):
    def next(self) -> list[str]:
        with self as file:
            yield json.load(file.source)
