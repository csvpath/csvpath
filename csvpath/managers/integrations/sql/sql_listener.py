from sqlalchemy import Engine
from csvpath.managers.listener import Listener
from csvpath.util.config import ReferencesSql
from .engine import Db
from .tables import Tables


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
