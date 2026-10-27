import json

from sqlalchemy import Engine, Table, select

from csvpath.managers.integrations.sql.engine import Db
from csvpath.managers.integrations.sql.tables import Tables
from csvpath.managers.registrar import Registrar

from .filesystem_reference_source import FilesystemReferenceSource


class SqlReferenceSource(FilesystemReferenceSource):
    """reads FILES and CSVPATHS reference metadata from the SQL listeners'
    tables, used when [references] sql = on. RESULTS reads are inherited
    from the filesystem until the archive ledger is mirrored (step 4c).

    every value is an entry exactly as a registrar or ledger writer wrote
    it; nothing is derived. reads are scoped to the configured roots.
    per-name reads and names skip deleted versions, as the filesystem does
    by removing the folder; ledger reads keep deleted entries, as the
    JSON ledgers do.

    on assumes SQL has mirrored the manifests from the start. rows from
    before lifecycles (a NULL lifecycle) and JSON ledger entries from
    before the ledger mirror are not seen. nothing is backfilled.
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
