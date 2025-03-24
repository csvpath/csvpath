from sqlalchemy import create_engine, Engine

# from sqlalchemy.orm import sessionmaker
from csvpath.util.config import Config
from csvpath.util.box import Box


class Db:
    @classmethod
    def get(self, config: Config) -> Engine:
        box = Box()
        engine = box.get(key=Box.SQL_ENGINE)
        if engine is None:
            dialect = config.get(section="sql", name="dialect")
            c_str = config.get(section="sql", name="connection_string")
            if dialect == "sqlite":
                # sqlite:///example.db
                engine = create_engine(c_str)
            elif dialect == "postgres":
                # postgresql+psycopg2://user:password@localhost/dbname
                engine = create_engine(c_str)
            elif dialect == "mysql":
                # mysql+pymysql://user:password@localhost/dbname
                engine = create_engine(c_str)
            elif dialect == "sql_server":
                # mssql+pyodbc://user:password@localhost/dbname
                engine = create_engine(c_str)
            else:
                raise ValueError("Unknown RDBMS dialect %s", dialect)
            box.add(Box.SQL_ENGINE, engine)
        return engine
