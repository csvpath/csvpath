import json
from sqlalchemy import Engine, Table, update
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.managers.registrar import Registrar
from csvpath.util.config import ReferencesSql
from .engine import Db
from .tables import Tables
from .updates import Updates
from .sql_upsert_utility import SqlUpsertUtility as squt


class SqlListener(Listener):
    def __init__(self, config=None):
        Listener.__init__(self, config=config)
        self.csvpaths = None
        self._tables = None

    def update_is_required(self) -> bool:
        #
        # when references rely on SQL ([references] sql = on) a failed SQL
        # write is a correctness problem, so it always raises.
        #
        return self.config.references_sql == ReferencesSql.ON.value

    def raise_on_update_error(self) -> bool:
        #
        # otherwise SQL is data exhaust and failures follow the CsvPaths
        # error policy.
        #
        if self.update_is_required():
            return True
        if self.csvpaths is None:
            return False
        return self.csvpaths.ecoms.do_i_raise()

    @property
    def tables(self) -> Tables:
        if self._tables is None:
            self._tables = Tables(self.config, engine=self.engine)
            self._tables.assure_tables()
        return self._tables

    @property
    def engine(self) -> Engine:
        return Db.get(self.config)

    # =============
    # root ledgers
    # =============

    def _ledger_row(
        self,
        *,
        mdata: Metadata,
        root_column: str,
        root: str,
        name_column: str,
        name: str,
    ) -> dict:
        """the ledger-table row for mdata's ledger entry. every value comes
        from mdata, as written by this update; nothing is read back."""
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if mdata.ledger_entry is None or mdata.ledger_index is None:
            raise ValueError("Metadata has no ledger entry")
        for label, v in [
            ("Root column", root_column),
            ("Root", root),
            ("Name column", name_column),
            ("Name", name),
        ]:
            if v is None or not isinstance(v, str) or v.strip() == "":
                raise ValueError(f"{label} must be a non-empty str")
        entry = mdata.ledger_entry
        version = mdata.manifest_entry
        #
        # the version written by this update, else the version the entry
        # itself names (an unchanged named-paths reload), else NULL
        #
        if version is None:
            version_uuid = entry.get("version_uuid")
        else:
            version_uuid = version["uuid"]
        return {
            "uuid": entry["uuid"],
            "at": mdata.time,
            root_column: root,
            name_column: name,
            "ledger_entry": json.dumps(entry),
            "ledger_index": mdata.ledger_index,
            "status": entry.get("status"),
            "lifecycle": entry.get("lifecycle"),
            "version_uuid": version_uuid,
        }

    def _mark_deleted(
        self, *, mdata: Metadata, version_table: Table, ledger_table: Table, name: str
    ) -> None:
        """marks the rows of a delete: each deleted version's row, and each
        ledger row with its entry as the ledger writer marked it. updates,
        not upserts, as for a patch: a missing row (e.g. written before SQL
        was on) is not backfilled, and ledger rows keep at and
        ledger_index."""
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if version_table is None or ledger_table is None:
            raise ValueError("Tables cannot be None")
        for e in mdata.manifest_entries or []:
            count = self._update_by_uuid(
                table=version_table,
                uuid=e["uuid"],
                values={"lifecycle": Registrar.DELETED},
            )
            if count == 0:
                self.csvpaths.logger.warning(
                    "No SQL row for %s entry %s; delete not written to SQL",
                    name,
                    e["uuid"],
                )
        for e in mdata.ledger_entries or []:
            values = {
                "ledger_entry": json.dumps(e),
                "status": e.get("status"),
                "lifecycle": e.get("lifecycle"),
            }
            count = self._update_by_uuid(
                table=ledger_table, uuid=e["uuid"], values=values
            )
            if count == 0:
                self.csvpaths.logger.warning(
                    "No SQL ledger row for %s entry %s; delete not written to SQL",
                    name,
                    e["uuid"],
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
                "Updating %s entry %s in %s", table.name, uuid, conn.dialect.name
            )
            stmt = update(table).where(table.c.uuid == uuid).values(values)
            result = conn.execute(stmt)
            conn.commit()
            return result.rowcount

    def _upsert_ledger_row(self, *, table: Table, row: dict) -> None:
        try:
            self._upsert_ledger_row_unreliably(table=table, row=row)
        except Exception:
            Updates(self.engine).do_updates()
            self._upsert_ledger_row_unreliably(table=table, row=row)

    def _upsert_ledger_row_unreliably(self, *, table: Table, row: dict) -> None:
        with self.engine.connect() as conn:
            dialect = conn.dialect.name
            self.csvpaths.logger.info(
                "Inserting %s entry %s into %s", table.name, row["uuid"], dialect
            )
            set_ = {k: v for k, v in row.items() if k != "uuid"}
            stmt = squt.upsert(dialect=dialect, table=table, data=row, set_=set_)
            conn.execute(stmt)
            conn.commit()
