from sqlalchemy import create_engine, Engine

from csvpath.util.config import Config
from csvpath.util.box import Box


class Db:
    @classmethod
    def get(cls, config: Config) -> Engine:
        dialect = config.get(section="sql", name="dialect")
        conn = config.get(section="sql", name="connection_string")
        return cls.get_engine(conn=conn, dialect=dialect)

    @classmethod
    def get_engine(cls, *, conn:str, dialect:str="sqlite") -> Engine:
        box = Box()
        engine = box.get(key=Box.SQL_ENGINE)
        if engine is None:
            #
            # atm there's nothing different about the dialects, but we'll
            # leave the ifs just for docs purposes.
            #
            if dialect == "sqlite":
                # sqlite:///example.db
                engine = create_engine(conn)
            elif dialect == "postgres":
                # postgresql+psycopg2://user:password@localhost/dbname
                engine = create_engine(conn)
            elif dialect == "mysql":
                # mysql+pymysql://user:password@localhost/dbname
                engine = create_engine(conn)
            elif dialect == "sql_server":
                # mssql+pyodbc://user:password@localhost/dbname
                engine = create_engine(conn)
            else:
                raise ValueError("Unknown RDBMS dialect %s", dialect)
            box.add(Box.SQL_ENGINE, engine)
        return engine
