from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    inspect,
)
from .engine import Db


class Tables:
    def __init__(self, config, *, engine=None):
        self.config = config
        self.engine = engine
        self._metadata = None
        self._instance_run = None
        self._named_paths_group_run = None
        self._named_file = None
        self._named_paths = None

    @property
    def metadata(self) -> MetaData:
        if self._metadata is None:
            self._metadata = MetaData()
        return self._metadata

    def assure_tables(self) -> None:
        self._assure_table(self.group_run)
        self._assure_table(self.instance_run)
        self._assure_table(self.named_file)
        self._assure_table(self.named_paths)

    def _assure_table(self, table) -> None:
        if self.engine is None:
            self.engine = Db.get(self.config)
        if not inspect(self.engine).has_table(table.name):
            metadata = table.metadata
            metadata.create_all(self.engine)

    # =============
    # tables
    # =============

    @property
    def named_paths(self) -> Table:
        if self._named_paths is not None:
            return self._named_paths
        mdata = self.metadata
        if "named_paths" in mdata.tables:
            return mdata.tables["named_paths"]
        named_paths = Table(
            "named_paths",
            mdata,
            Column("uuid", String(40), primary_key=True, nullable=False),
            Column("at", DateTime, nullable=False),
            Column("paths_root", String(250), nullable=False),
            Column("paths_name", String(40), nullable=False),
            Column("paths_home", String(250), nullable=False),
            Column("group_file_path", String(250)),
            Column("paths_count", Integer, default=0),
            Column("source_path", String(250)),
            Column("ip_address", String(30)),
            Column("hostname", String(100)),
            Column("username", String(50)),
            Column("base_path", String(250)),
            Column("manifest_path", String(250), nullable=False),
            Column("template", String(250), nullable=True),
        )
        self._named_paths = named_paths
        return self._named_paths

    @property
    def named_file(self) -> Table:
        if self._named_file is not None:
            return self._named_file
        mdata = self.metadata
        if "named_file" in mdata.tables:
            return mdata.tables["named_file"]
        named_file = Table(
            "named_file",
            mdata,
            Column("uuid", String(40), primary_key=True, nullable=False),
            Column("at", DateTime, nullable=False),
            Column("named_file_name", String(40), nullable=False),
            Column("origin_path", String(500), nullable=False),
            Column("name_home", String(250), nullable=False),
            Column("file_home", String(250)),
            Column("file_path", String(250)),
            Column("file_name", String(100)),
            Column("mark", String(5)),
            Column(
                "type", String(250)
            ),  # type is expected to be like csv, xlsx, etc. but w/http download we don't know
            Column("file_size", Integer, default=0),
            Column("ip_address", String(30)),
            Column("hostname", String(100)),
            Column("username", String(50)),
            Column("files_root", String(250), nullable=False),
            Column("base_path", String(250)),
            Column("manifest_path", String(250), nullable=False),
            Column("template", String(250), nullable=True),
        )
        self._named_file = named_file
        return self._named_file

    @property
    def instance_run(self) -> Table:
        if self._instance_run is not None:
            return self._instance_run
        mdata = self.metadata
        if "instance_run" in mdata.tables:
            return mdata.tables["instance_run"]
        instance_run = Table(
            "instance_run",
            mdata,
            Column("uuid", String(40), primary_key=True, nullable=False),
            Column("at", DateTime, nullable=False),
            Column(
                "group_run_uuid",
                String(40),
                ForeignKey("named_paths_group_run.uuid"),
                nullable=False,
            ),
            Column("instance_identity", String(100)),
            Column("instance_home", String(250), nullable=False),
            Column("preceding_instance_identity", String(100)),
            Column("actual_data_file", String(500)),
            Column("instance_index", Integer, default=-1),
            Column("number_of_files_expected", Integer, default=-1),
            Column("number_of_files_generated", Integer, default=-1),
            Column("source_mode_preceding", String(1), default="N"),
            Column("files_expected", String(1), default="Y"),
            Column("valid", String(1), default="N"),
            Column("completed", String(1), default="N"),
            Column("lines_scanned", Integer, default=0),
            Column("lines_total", Integer, default=0),
            Column("lines_matched", Integer, default=0),
            Column("error_count", Integer, default=-1),
            Column("manifest_path", String(250), nullable=False),
        )
        self._instance_run = instance_run
        return self._instance_run

    @property
    def group_run(self) -> Table:
        if self._named_paths_group_run is not None:
            return self._named_paths_group_run
        mdata = self.metadata
        if "named_paths_group_run" in mdata.tables:
            return mdata.tables["named_paths_group_run"]
        group_run = Table(
            "named_paths_group_run",
            self._metadata,
            Column("uuid", String(40), primary_key=True, nullable=False),
            Column("at", DateTime, nullable=False),
            Column("time_completed", DateTime),
            Column("status", String(20)),
            Column("by_line_run", String(1), default="Y"),
            Column("all_completed", String(1), default="N"),
            Column("all_valid", String(1), default="N"),
            Column("error_count", Integer),
            Column("all_expected_files", String(1), default="N"),
            Column("archive_name", String(100)),
            Column("run_home", String(250)),
            Column("named_results_name", String(45)),
            Column("named_paths_uuid", String(40), nullable=False),
            Column("named_paths_name", String(45), nullable=False),
            Column("named_paths_home", String(250), nullable=False),
            Column("named_file_uuid", String(40), nullable=False),
            Column("named_file_name", String(45), nullable=False),
            Column("named_file_home", String(500), nullable=False),
            Column("named_file_path", String(500), nullable=False),
            Column("named_file_size", Integer, default=-1),
            Column(
                "named_file_last_change", String(40)
            ),  # this represents a date but is not a date obj because of its source
            Column("named_file_fingerprint", String(70)),
            Column("hostname", String(45)),
            Column("username", String(45)),
            Column("ip_address", String(40)),
            Column("manifest_path", String(250)),
        )
        self._named_paths_group_run = group_run
        return self._named_paths_group_run
