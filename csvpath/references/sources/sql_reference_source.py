import json

from sqlalchemy import Engine, Table, select

from csvpath.managers.integrations.sql.engine import Db
from csvpath.managers.integrations.sql.tables import Tables
from csvpath.managers.registrar import Registrar
from csvpath.util.nos import Nos

from .filesystem_reference_source import FilesystemReferenceSource


class SqlReferenceSource(FilesystemReferenceSource):
    """reads reference metadata from the SQL listeners' tables, used when
    [references] sql = on: FILES and CSVPATHS manifests, ledgers and
    names, and RESULTS' archive ledger, run and instance manifests and
    instance directories.

    every value is an entry exactly as a registrar or ledger writer wrote
    it; nothing is derived. reads are scoped to the configured roots.
    per-name reads and names skip deleted versions, as the filesystem does
    by removing the folder; ledger reads keep deleted entries, as the
    JSON ledgers do.

    a run's existence is still checked on the filesystem, as the
    filesystem source does: SQL rows outlive a deleted run.

    on assumes SQL has mirrored the manifests from the start. rows from
    before lifecycles (a NULL lifecycle), JSON ledger entries from before
    the ledger mirrors, and runs from before manifest_entry are not seen.
    nothing is backfilled.
    """

    def __init__(self, *, csvpaths) -> None:
        super().__init__(csvpaths=csvpaths)
        self._tables = None

    @property
    def engine(self) -> Engine:
        return Db.get(self.csvpaths.config)

    @property
    def tables(self) -> Tables:
        if self._tables is None:
            #
            # as the SQL listeners do: a new database has no tables until
            # the first write, and nothing written reads as empty
            #
            self._tables = Tables(self.csvpaths.config, engine=self.engine)
            self._tables.assure_tables()
        return self._tables

    def _column(self, stmt) -> list:
        with self.engine.connect() as conn:
            return [r[0] for r in conn.execute(stmt)]

    def _entries(self, stmt) -> list[dict]:
        return [json.loads(e) for e in self._column(stmt)]

    def _versions(
        self,
        *,
        table: Table,
        root_column: str,
        root: str,
        name_column: str,
        name: str,
    ) -> list[dict]:
        stmt = (
            select(table.c.manifest_entry)
            .where(table.c[root_column] == root)
            .where(table.c[name_column] == name)
            .where(table.c.lifecycle == Registrar.ACTIVE)
            .order_by(table.c.manifest_index)
        )
        return self._entries(stmt)

    def _ledger(self, *, table: Table, root_column: str, root: str) -> list[dict]:
        stmt = (
            select(table.c.ledger_entry)
            .where(table.c[root_column] == root)
            .order_by(table.c.ledger_index)
        )
        return self._entries(stmt)

    def _names(
        self, *, table: Table, root_column: str, root: str, name_column: str
    ) -> list[str]:
        stmt = (
            select(table.c[name_column])
            .distinct()
            .where(table.c[root_column] == root)
            .where(table.c.lifecycle == Registrar.ACTIVE)
        )
        #
        # sorted here, not by the database: collations differ by dialect
        # (MySQL's default ignores case), and the filesystem source sorts
        # the same way
        #
        return sorted(self._column(stmt))

    #
    # FILES
    #
    def file_manifest(self, name: str) -> list:
        self._check_name(name, "Named-file name")
        manifest = self._versions(
            table=self.tables.named_file,
            root_column="files_root",
            root=self.csvpaths.config.inputs_files_path,
            name_column="named_file_name",
            name=name,
        )
        #
        # as FileManager.get_manifest does for a name with no manifest
        #
        if len(manifest) == 0:
            raise ValueError(f"No manifest for file named {name}")
        return manifest

    def files_ledger(self) -> list:
        return self._ledger(
            table=self.tables.named_file_ledger,
            root_column="files_root",
            root=self.csvpaths.config.inputs_files_path,
        )

    def file_names(self) -> list[str]:
        return self._names(
            table=self.tables.named_file,
            root_column="files_root",
            root=self.csvpaths.config.inputs_files_path,
            name_column="named_file_name",
        )

    #
    # CSVPATHS
    #
    def paths_manifest(self, name: str) -> list:
        self._check_name(name, "Named-paths name")
        return self._versions(
            table=self.tables.named_paths,
            root_column="paths_root",
            root=self.csvpaths.config.inputs_csvpaths_path,
            name_column="paths_name",
            name=name,
        )

    def paths_ledger(self) -> list:
        return self._ledger(
            table=self.tables.named_paths_ledger,
            root_column="paths_root",
            root=self.csvpaths.config.inputs_csvpaths_path,
        )

    def paths_names(self) -> list[str]:
        return self._names(
            table=self.tables.named_paths,
            root_column="paths_root",
            root=self.csvpaths.config.inputs_csvpaths_path,
            name_column="paths_name",
        )

    #
    # RESULTS
    #
    def _one(self, stmt, *, what: str, key: str) -> dict | None:
        """the one entry stmt selects, or None. more than one means the
        database is wrong, not that either is the answer."""
        entries = self._entries(stmt)
        if len(entries) > 1:
            raise ValueError(
                f"{len(entries)} SQL rows for {what} {key}; expected one"
            )
        return entries[0] if len(entries) == 1 else None

    def results_ledger(self) -> list:
        return self._ledger(
            table=self.tables.archive_ledger,
            root_column="archive_root",
            root=self.csvpaths.config.archive_path,
        )

    def run_homes(
        self, *, root_major: str | None, name_filter: str | None
    ) -> list[tuple[str, str]]:
        return self._run_homes_from(
            entries=self.results_ledger(),
            root_major=root_major,
            name_filter=name_filter,
        )

    def run_manifest(self, run_dir: str) -> dict | None:
        self._check_name(run_dir, "Run dir")
        t = self.tables.group_run
        stmt = (
            select(t.c.manifest_entry)
            .where(t.c.archive_root == self.csvpaths.config.archive_path)
            .where(t.c.run_home == run_dir)
        )
        return self._one(stmt, what="run", key=run_dir)

    def instance_manifest(self, instance_dir: str) -> dict | None:
        self._check_name(instance_dir, "Instance dir")
        g = self.tables.group_run
        i = self.tables.instance_run
        #
        # instance_run is scoped through its run (D5)
        #
        stmt = (
            select(i.c.manifest_entry)
            .join(g, g.c.uuid == i.c.group_run_uuid)
            .where(g.c.archive_root == self.csvpaths.config.archive_path)
            .where(i.c.instance_home == instance_dir)
        )
        return self._one(stmt, what="instance", key=instance_dir)

    def instance_dirs(self, run_dir: str) -> list[str]:
        self._check_name(run_dir, "Run dir")
        g = self.tables.group_run
        i = self.tables.instance_run
        stmt = (
            select(i.c.instance_home)
            .join(g, g.c.uuid == i.c.group_run_uuid)
            .where(g.c.archive_root == self.csvpaths.config.archive_path)
            .where(g.c.run_home == run_dir)
        )
        #
        # an instance's directory is the last segment of its home
        #
        sep = Nos(run_dir).sep
        return [home[home.rfind(sep) + 1 :] for home in self._column(stmt)]
