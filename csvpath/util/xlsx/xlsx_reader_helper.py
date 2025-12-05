from csvpath.util.class_loader import ClassLoader


class XlsxReaderHelper:
    @classmethod
    def _is_xslt(cls, path, filetype) -> bool:
        if filetype == "xlsx":
            return True
        if path and path.endswith("xlsx"):
            return True
        return False

    @classmethod
    def _xlsx_if(
        cls, *, path: str, filetype: str, sheet: str, delimiter: str, quotechar: str
    ):
        if not cls._is_xslt(path, filetype):
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
