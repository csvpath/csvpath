import json
from sqlalchemy import Table, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from csvpath.managers.metadata import Metadata
from .sql_listener import SqlListener
from .updates import Updates


class SqlFileListener(SqlListener):
    def __init__(self, config=None):
        SqlListener.__init__(self, config=config)
        self._named_file = None
        self._named_file_ledger = None

    @property
    def named_file(self) -> Table:
        if self._named_file is None:
            self._named_file = self.tables.named_file
        return self._named_file

    @property
    def named_file_ledger(self) -> Table:
        if self._named_file_ledger is None:
            self._named_file_ledger = self.tables.named_file_ledger
        return self._named_file_ledger

    def metadata_update(self, mdata: Metadata) -> None:
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        #
        # mirror only what was actually written: the version by the
        # primary registrar, the ledger entry by FilesListener. None means
        # the write was skipped or failed.
        #
        if mdata.manifest_entry is None:
            self.csvpaths.logger.info(
                "No manifest entry for named-file %s; not writing a version to SQL",
                mdata.named_file_name,
            )
        else:
            self._write_named_file(mdata)
        self._write_ledger(mdata)

    def metadata_failure(self, mdata: Metadata) -> None:
        """a failed registration has a ledger entry but no version"""
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        self._write_ledger(mdata)

    def _write_ledger(self, mdata: Metadata) -> None:
        if mdata.ledger_entry is None:
            self.csvpaths.logger.info(
                "No ledger entry for named-file %s; not writing a ledger row to SQL",
                mdata.named_file_name,
            )
            return
        row = self._ledger_row(
            mdata=mdata,
            root_column="files_root",
            root=mdata.named_files_root,
            name_column="named_file_name",
            name=mdata.named_file_name,
        )
        self._upsert_ledger_row(table=self.named_file_ledger, row=row)

    def _write_named_file(self, mdata: Metadata) -> None:
        named_file_data = {
            "uuid": mdata.uuid_string,
            "at": mdata.time,
            "named_file_name": mdata.named_file_name,
            "origin_path": mdata.origin_path,
            "name_home": mdata.name_home,
            "file_home": mdata.file_home,
            "file_path": mdata.file_path,
            "file_name": mdata.file_name,
            "mark": mdata.mark,
            "type": mdata.type,
            "file_size": mdata.file_size,
            "ip_address": mdata.ip_address,
            "hostname": mdata.hostname,
            "username": mdata.username,
            "files_root": mdata.named_files_root,
            #
            # capturing cwd to db does not help. base_path is deprecated.
            #
            # "base_path": mdata.base_path,
            "base_path": "",
            "manifest_path": mdata.manifest_path,
            "template": mdata.template,
            "manifest_entry": json.dumps(mdata.manifest_entry),
            "manifest_index": mdata.manifest_index,
        }
        self._upsert_named_file(named_file_data)

    def metadata_patch(self, mdata: Metadata) -> None:
        """updates the rows of the patched manifest entry and its ledger
        entry. updates, not upserts: a patch has too little to insert a
        row, and a missing row (e.g. registered before SQL was on) is not
        backfilled. an update also keeps the ledger row's at and
        ledger_index, which are the arrival's."""
        if not self.csvpaths:
            raise RuntimeError("CsvPaths cannot be None")
        entry = mdata.manifest_entry
        if entry is None:
            self.csvpaths.logger.info(
                "No patched manifest entry for named-file %s; not writing to SQL",
                mdata.named_file_name,
            )
            return
        values = {
            "type": entry.get("type"),
            "file_path": entry.get("file"),
            "file_home": entry.get("file_home"),
            "file_name": entry.get("file_name"),
            "manifest_entry": json.dumps(entry),
        }
        count = self._update_by_uuid(
            table=self.named_file, uuid=entry["uuid"], values=values
        )
        if count == 0:
            self.csvpaths.logger.warning(
                "No SQL row for named-file %s entry %s; patch not written to SQL",
                mdata.named_file_name,
                entry["uuid"],
            )
        self._patch_ledger_row(mdata)

    def _patch_ledger_row(self, mdata: Metadata) -> None:
        ledger_entry = mdata.ledger_entry
        if ledger_entry is None:
            self.csvpaths.logger.info(
                "No patched ledger entry for named-file %s; not writing a ledger row to SQL",
                mdata.named_file_name,
            )
            return
        values = {
            "ledger_entry": json.dumps(ledger_entry),
            "status": ledger_entry.get("status"),
            "lifecycle": ledger_entry.get("lifecycle"),
        }
        count = self._update_by_uuid(
            table=self.named_file_ledger, uuid=ledger_entry["uuid"], values=values
        )
        if count == 0:
            self.csvpaths.logger.warning(
                "No SQL ledger row for named-file %s entry %s; patch not written to SQL",
                mdata.named_file_name,
                ledger_entry["uuid"],
            )

    def _update_by_uuid(self, *, table: Table, uuid: str, values: dict) -> int:
        try:
            return self._update_by_uuid_unreliably(
                table=table, uuid=uuid, values=values
            )
        except Exception:
            Updates(self.engine).do_updates()
            return self._update_by_uuid_unreliably(
                table=table, uuid=uuid, values=values
            )

    def _update_by_uuid_unreliably(
        self, *, table: Table, uuid: str, values: dict
    ) -> int:
        if table is None:
            raise ValueError("Table cannot be None")
        if uuid is None or not isinstance(uuid, str) or uuid.strip() == "":
            raise ValueError("Uuid must be a non-empty str")
        if not isinstance(values, dict) or len(values) == 0:
            raise ValueError("Values must be a non-empty dict")
        with self.engine.connect() as conn:
            self.csvpaths.logger.info(
                "Updating patched named-file metadata in %s", conn.dialect.name
            )
            stmt = update(table).where(table.c.uuid == uuid).values(values)
            result = conn.execute(stmt)
            conn.commit()
            return result.rowcount

    def _upsert_named_file(self, named_file_data: dict):
        try:
            self._upsert_named_file_unreliably(named_file_data)
        except Exception:
            Updates(self.engine).do_updates()
            self._upsert_named_file_unreliably(named_file_data)

    def _upsert_named_file_unreliably(self, named_file_data: dict):
        with self.engine.connect() as conn:
            dialect = conn.dialect.name
            self.csvpaths.logger.info("Inserting named-file metadata into %s", dialect)
            stmt = None
            if dialect in ["postgresql", "sqlite"]:
                ist = pg_insert if dialect == "postgresql" else sqlite_insert
                stmt = (
                    ist(self.named_file)
                    .values(named_file_data)
                    .on_conflict_do_update(
                        index_elements=["uuid"], set_=self._set(named_file_data)
                    )
                )
            elif dialect == "mysql":
                stmt = (
                    mysql_insert(self.named_file)
                    .values(named_file_data)
                    .on_duplicate_key_update(self._set(named_file_data))
                )
            elif dialect == "mssql":
                raise NotImplementedError("SQL Server support is not yet implemented.")
            else:
                raise ValueError(f"Unsupported database dialect: {dialect}")
            conn.execute(stmt)
            conn.commit()

    def _set(self, named_file_data) -> dict:
        return {
            "files_root": named_file_data["files_root"],
            "file_home": named_file_data["file_home"],
            "file_path": named_file_data["file_path"],
            "file_name": named_file_data["file_name"],
            "mark": named_file_data["mark"],
            "type": named_file_data["type"],
            "file_size": named_file_data["file_size"],
            "ip_address": named_file_data["ip_address"],
            "hostname": named_file_data["hostname"],
            "username": named_file_data["username"],
            "template": named_file_data["template"]
            if "template" in named_file_data
            else None,
            "manifest_entry": named_file_data.get("manifest_entry"),
            "manifest_index": named_file_data.get("manifest_index"),
        }
