from typing import Any
from sqlalchemy import create_engine, Engine
import sqlalchemy as sa
import traceback

from csvpath.managers.integrations.sql.engine import Db
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.functions.function_focus import ValueProducer, MatchDecider
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.args import Args


class SqlIn(ValueProducer, MatchDecider):

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name, child=child)
        self._cache = {}

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Checks if a header value is present in a set of values found in a database. The
                   functionality is similar to in().

                   The function looks at all values of just one column.

                   If the cache argument is True, all values are retrieved from the
                   database the first time the function is used. Thereafter, the
                   values are cached in CsvPath Framework for fast in-memory constant time lookups. If cache
                   is not True a query is performed for each line the function sees.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(5)
        a.arg(
            name="value to checks for",
            types=[Variable, Header, Function, Term],
            actuals=[Any, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="table name",
            types=[Term, Variable, Header, Function],
            actuals=[str],
        )
        a.arg(
            name="table column",
            types=[Term, Variable, Header, Function],
            actuals=[str],
        )
        a.arg(
            name="connect string",
            types=[Term, Variable],
            actuals=[str],
        )
        a.arg(
            name="cache",
            types=[None, Term, Variable],
            actuals=[bool],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self._value_one(skip=skip)
        table = self._value_two(skip=skip)
        column = self._value_three(skip=skip)
        conn = self._value_four(skip=skip)
        cache = self._value_five(skip=skip)
        cache = False if cache is None else cache
        print(f"sqlin table: {table}")
        print(f"sqlin col: {column}")
        print(f"sqlin conn: {conn}")
        print(f"sqlin cache: {cache}")
        self.value = self._query(table=table, column=column, value=v, conn=conn, cache=cache)
        print(f"sqlin done")


    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)

##################

    def _query(self, *, table:str, column:str, value:Any, cache:bool, conn:str) -> bool:
        try:
            print(f"sqlin: doing _query")
            engine = Db.get_engine(conn=conn)
            print(f"sqlin: engine: {engine}")
            return self._do_query(table=table, column=column, value=value, cache=cache, engine=engine)
        except Exception as ex:
            print(traceback.format_exc())

    def _do_query(self, *, table:str, column:str, value:Any, cache:bool, engine:Engine) -> bool:
        print(f"sqlin cache: {cache}")
        if cache is True:
            if self._cached is None:
                self._do_cache(value=value, table=table, column=column, engine=engine)
            print(f"sqlin alue: {value} in _cached: {self._cached}")
            return value in self._cached
        else:
            print(f"sqlin looking up: {value} ")
            return self._do_lookup(value=value, table=table, column=column, engine=engine)

    def _do_cache(self, *, value:Any, table:str, column:str, engine:Engine) -> bool:
        print(f"sqlin doing cached")
        sql = f"select {column} from {table}"
        with engine.connect() as conn:
            rows = conn.execute(sql).fetchall()
            self._cache = {row[0]: None for row in rows}

    def _do_lookup(self, *, value:Any, table:str, column:str, engine:Engine) -> bool:
        print(f"sqlin doing lookup")
        table = sa.table(table, sa.column(column))
        query = (
            sa.select(sa.column(column))
            .select_from(table)
            .where(sa.column(column) == value)
            .limit(1)
        )
        with engine.connect() as conn:
            result = conn.execute(query).fetchone()
            return result is not None


