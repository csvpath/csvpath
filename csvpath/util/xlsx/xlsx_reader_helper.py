from csvpath.util.class_loader import ClassLoader
import pylightxl as xl


class XlsxReaderHelper:
    @classmethod
    def valid_worksheet(cls, path: str, mark: str):
        if path is None or mark is None:
            raise ValueError(f"Arguments cannot be None: [{path}, {mark}]")
        if not cls.is_xlsx(path):
            raise ValueError(f"Not an Excel path: {path}")
        db = xl.readxl(fn=path)
        return mark in db.ws_names

    @classmethod
    def is_xlsx(cls, path: str) -> bool:
        return cls._is_xlsx(path, None)

    @classmethod
    def _is_xlsx(cls, path, filetype) -> bool:
        if filetype == "xlsx":
            return True
        if path and path.endswith("xlsx"):
            return True
        return False

    @classmethod
    def _xlsx_if(
        cls, *, path: str, filetype: str, sheet: str, delimiter: str, quotechar: str
    ):
        if not cls._is_xlsx(path, filetype):
            return None
        if path.find("s3://") > -1:
            instance = ClassLoader.load(
                "from csvpath.util.s3.s3_xlsx_data_reader import S3XlsxDataReader",
                args=[path],
                kwargs={
                    "sheet": sheet if sheet != path else None,
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("sftp://") > -1:
            instance = ClassLoader.load(
                "from csvpath.util.sftp.sftp_xlsx_data_reader import SftpXlsxDataReader",
                args=[path],
                kwargs={
                    "sheet": sheet if sheet != path else None,
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("azure://") > -1:
            instance = ClassLoader.load(
                "from csvpath.util.azure.azure_xlsx_data_reader import AzureXlsxDataReader",
                args=[path],
                kwargs={
                    "sheet": sheet if sheet != path else None,
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance
        if path.find("gs://") > -1:
            instance = ClassLoader.load(
                "from csvpath.util.gcs.gcs_xlsx_data_reader import GcsXlsxDataReader",
                args=[path],
                kwargs={
                    "sheet": sheet if sheet != path else None,
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                },
            )
            return instance

        instance = ClassLoader.load(
            "from csvpath.util.xlsx.xlsx_data_reader import XlsxDataReader",
            args=[path],
            kwargs={
                "sheet": sheet if sheet != path else None,
                "delimiter": delimiter,
                "quotechar": quotechar,
            },
        )
        return instance
