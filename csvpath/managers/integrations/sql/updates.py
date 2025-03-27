from sqlalchemy import text


class Updates:
    def __init__(self, engine):
        self.engine = engine

    def do_updates(self) -> None:
        stmts = [
            text("ALTER TABLE named_file ADD COLUMN template varchar(250)"),
            text("ALTER TABLE named_paths ADD COLUMN template varchar(250)")
            #
            # more updates if there are ever any go here
            #
        ]
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
