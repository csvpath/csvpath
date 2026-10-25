from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


class SqlUpsertUtility:
    """builds an insert-or-update by primary key for the SQL dialects the
    SQL integration supports"""

    @classmethod
    def upsert(cls, *, dialect: str, table: Table, data: dict, set_: dict):
        """returns a statement that inserts data, or updates the columns in
        set_ when a row with data's uuid already exists"""
        if dialect is None or not isinstance(dialect, str) or dialect.strip() == "":
            raise ValueError("Dialect must be a non-empty str")
        if table is None:
            raise ValueError("Table cannot be None")
        if not isinstance(data, dict) or len(data) == 0:
            raise ValueError("Data must be a non-empty dict")
        if not isinstance(set_, dict) or len(set_) == 0:
            raise ValueError("Set must be a non-empty dict")
        if dialect in ["postgresql", "sqlite"]:
            ist = pg_insert if dialect == "postgresql" else sqlite_insert
            return (
                ist(table)
                .values(data)
                .on_conflict_do_update(index_elements=["uuid"], set_=set_)
            )
        if dialect == "mysql":
            return mysql_insert(table).values(data).on_duplicate_key_update(set_)
        if dialect == "mssql":
            raise NotImplementedError("SQL Server support is not yet implemented.")
        raise ValueError(f"Unsupported database dialect: {dialect}")
