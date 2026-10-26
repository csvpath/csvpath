from csvpath.managers.metadata import Metadata


class FileMetadata(Metadata):
    """@private"""

    def __init__(self, config):
        super().__init__(config)
        # like aname
        self.named_file_name: str = None
        # any reachable path
        self.origin_path: str = None
        # like inputs/named_files/aname
        self.name_home: str = None
        # like inputs/named_files/aname/afile.csv
        self.file_home: str = None
        # like inputs/named_files/aname/afile.csv/ab12cd546.csv
        self.file_path: str = None
        # like ab12cd546.csv
        self.file_name: str = None
        # a name after a '#' char
        self.mark: str = None
        # like csv
        self.type: str = None
        self.file_size: int = 0
        self.template: str = None
        self.fingerprint: str = None
        #
        # set only on a failed registration: the uuid of the attempt, which
        # the failure's own uuid is not. links the failure to the
        # attempt, and to its arrival entry if one was written.
        #
        self.registration_uuid: str | None = None
        #
        # a requested change to an existing manifest entry. see
        # FileRegistrar.patch_named_file. None for a registration.
        #
        self.patch: dict | None = None
        # the manifest position to patch. -1 is the latest entry.
        self.patch_index: int = -1
        #
        # named_file_ref is the most specific reference possible it is
        # in the form $name.files.fingerprint
        #
        # this field predates the Metadata.reference
        # TODO: remove
        #
