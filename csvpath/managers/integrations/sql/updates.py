from sqlalchemy import text
from .tables import Tables


class Updates:
    def __init__(self, engine):
        self.engine = engine

    def do_updates(self) -> None:
        stmts = [
            text("ALTER TABLE named_file ADD COLUMN template varchar(250)"),
            text("ALTER TABLE named_paths ADD COLUMN template varchar(250)"),
            text("ALTER TABLE named_file ADD COLUMN manifest_entry TEXT"),
            text("ALTER TABLE named_paths ADD COLUMN manifest_entry TEXT"),
            text("ALTER TABLE instance_run ADD COLUMN manifest_entry TEXT"),
            text("ALTER TABLE named_paths_group_run ADD COLUMN manifest_entry TEXT"),
            text("ALTER TABLE named_file ADD COLUMN manifest_index INTEGER"),
            text("ALTER TABLE named_paths ADD COLUMN manifest_index INTEGER"),
            text("ALTER TABLE named_file ADD COLUMN lifecycle varchar(20)"),
            text("ALTER TABLE named_paths ADD COLUMN lifecycle varchar(20)"),
            text(
                "ALTER TABLE named_paths_group_run ADD COLUMN archive_root varchar(250)"
            ),
            text("ALTER TABLE named_paths_group_run ADD COLUMN lifecycle varchar(20)"),
            text("ALTER TABLE instance_run ADD COLUMN lifecycle varchar(20)"),
        ]
        #
        # MySQL has no CREATE INDEX IF NOT EXISTS, so these fail like the
        # ALTERs once applied
        #
        for table, indexes in Tables.INDEXES.items():
            for name, columns in indexes.items():
                cols = ", ".join(Tables.index_columns(columns))
                stmts.append(text(f"CREATE INDEX {name} ON {table} ({cols})"))
        #
        # more updates if there are ever any go above the indexes
        #
        for s in stmts:
            try:
                print(f"doing an update to the database: {s}")
                with self.engine.connect() as connection:
                    connection.execute(s)
                    connection.commit()
            except Exception as e:
                ...
                print(f"error: {type(e)}: {e}")
                #
                # this is expected. we try all the updates every time we think
                # we need to update, so most of them can be expected to fail because
                # they will have already been applied at an earlier time.
                #
