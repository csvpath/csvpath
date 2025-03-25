import os
from typing import Type, Any
from sqlite3 import connect, Connection, Row
from .code import Code
from .config import Config


class Sqliter:
    def __init__(self, *, config: Config, client_class: Type[Any] = None) -> None:
        self._db_file = None
        self._conn = None
        self._config = config
        self._client_class = client_class if client_class is not None else type(self)

    @property
    def db_file(self):
        if self._db_file is None:
            self._db_file = self._config.get(
                section="sqlite", name="db", default=f"archive{os.sep}csvpath.db"
            )
            if not os.path.exists(self._db_file):
                if self._db_file.find(os.sep) > -1:
                    d = os.path.dirname(self._db_file)
                    os.makedirs(d, exist_ok=True)
                open(self._db_file, "w").close()
                self._setup_db()
        return self._db_file

    def _setup_db(self) -> None:
        path = Code.get_source_path(self._client_class)
        path = os.path.dirname(path)
        path = os.path.join(path, "schema.sql")
        sql = ""
        with open(path, "r", encoding="utf-8") as file:
            sql = file.read()
        with Sqliter(config=self._config) as conn:
            cursor = conn.cursor()
            cursor.executescript(sql)
            conn.commit()

    @property
    def connection(self) -> Connection:
        self._conn = connect(self.db_file)
        return self._conn

    def __enter__(self):
        self._conn = self.connection
        self._conn.row_factory = Row
        return self._conn

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._conn.close()
        self._conn = None
        #
        # potential for config to have a different path? might be
        # worth something during testing?
        #
        self._db_file = None
