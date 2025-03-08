from sqlalchemy import Engine
from csvpath.managers.listener import Listener
from .engine import Db
from .tables import Tables


class SqlListener(Listener):
    def __init__(self, config=None):
        Listener.__init__(self, config=config)
        self.csvpaths = None
        self._tables = None
        self._engine = None

    @property
    def tables(self) -> Tables:
        if self._tables is None:
            self._tables = Tables(self.config, engine=self.engine)
            self._tables.assure_tables()
        return self._tables

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = Db.get(self.config)
        return self._engine

    @engine.setter
    def engine(self, engine: Engine):
        self._engine = engine
