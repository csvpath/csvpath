from csvpath.managers.metadata import Metadata
from csvpath.managers.results.result import Result


class Datafile:

    FILETYPES = ["data", "unmatched", "meta", "errors", "vars", "printouts", "manifest"]

    def __init__(
        self,
        *,
        listener,
        result: Result,
        manifest: dict,
        metadata: Metadata,
        path: str,
        filetype=str,
        dataset_id=None,
    ) -> None:
        self.listener = listener
        self.manifest = manifest
        self.metadata = metadata
        self.result = result
        self._path = path
        self._name = None
        self._mime_type = None
        self._dataset_id = None
        self._filetype = filetype
        if filetype not in Datafile.FILETYPES:
            raise Exception(
                f"File type must be in {Datafile.FILETYPES}, not {filetype}"
            )

    @property
    def name(self) -> str:
        if self._name is None:
            return self._filetype
        return self._name

    @name.setter
    def name(self, n: str) -> None:
        self._name = n

    @property
    def mime_type(self) -> str:
        return self._mime_type

    @mime_type.setter
    def mime_type(self, t: str) -> None:
        self._mime_type = t

    @property
    def filetype(self) -> str:
        return self._filetype

    @property
    def dataset_id(self) -> str:
        return self._dataset_id

    @dataset_id.setter
    def dataset_id(self, did: str) -> None:
        self._dataset_id = did

    @property
    def url(self) -> str:
        return self.result.instance_dir

    @property
    def path(self) -> str:
        return self._path
