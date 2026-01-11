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
        # named_file_ref is the most specific reference possible it is
        # in the form $name.files.fingerprint
        #
        self.named_file_ref: str = None
