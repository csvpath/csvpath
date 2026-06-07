from typing import Any
import re
from sqlalchemy import Engine
import sqlalchemy as sa
import traceback

from csvpath.managers.integrations.sql.engine import Db
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.functions.function_focus import ValueProducer
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.args import Args
from csvpath.matching.util.exceptions import MatchException


class Select(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Selects from a table column into a stack variable.

                   A where clause can be provided as an argument. The where clause cannot be complex, for example, involving other tables or views.

                   The where clause uses CsvPath Language Variable syntax. Use @var to reference the csvpath's var variable. For example, to select values in the ID column according to a group name you might do:

                   select.my_ids("ID", "mytable", "where group='@group'", yes())

                   Here "ID" is the column name to select from, "mytable" is the table, and the where clause limits the returned values by checking the "group" column against the @group variable.

                   select() functions may take an arbitrary name qualifier to create a variable without an explicit assignment. If a name is provided, the select will only run if the variable does not exist. Put another way, to cache a select(), simply give it a name, like: select.my_cached_select(). The my_cached_select variable will be populated once. If you need to refresh it, use clear().

                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(5)
        a.arg(
            name="column name",
            types=[Variable, Header, Function, Term],
            actuals=[Any, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="table name",
            types=[Term, Variable, Header, Function],
            actuals=[str],
        )
        a.arg(
            name="where clause",
            types=[Term, Variable, Header, Function],
            actuals=[None, str, self.args.EMPTY_STRING],
        )
        a.arg(
            name="connect string",
            types=[Term, Variable],
            actuals=[str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        name = self.first_non_term_qualifier()
        if name is not None and name in self.matcher.csvpath.variables:
            v = self.matcher.get_variable(name)
            self.value = v
            return
        column = self._value_one(skip=skip)
        table = self._value_two(skip=skip)
        where = self._value_three(skip=skip)
        conn = self._value_four(skip=skip)
        v = self._query(table=table, column=column, where=where, conn=conn)
        name = self.first_non_term_qualifier()
        if name is not None:
            self.matcher.set_variable(name, value=v)
        self.value = v

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)

    ##################

    def _query(self, *, table: str, column: str, where: str, conn: str) -> bool:
        try:
            engine = Db.get_engine(conn=conn)
            return self._do_query(
                table=table, column=column, where=where, engine=engine
            )
        except Exception:
            print(traceback.format_exc())

    def _do_query(self, *, table: str, column: str, where: str, engine: Engine) -> list:
        table = sa.table(table, sa.column(column))
        query = sa.select(sa.column(column)).select_from(table)

        if str(where).strip() not in ["", "None"]:
            where_str, params = self._create_where(where)
            query = query.where(sa.text(where_str).bindparams(**params))

        ret = []
        with engine.connect() as conn:
            result = conn.execute(query).fetchall()
            for _ in result:
                ret.append(_[0])
            return ret

    def _create_where(self, w: str) -> tuple[str, dict]:
        w = re.sub(r"(?i)^where[\t ]", "", w.strip())
        if any(_ in w.lower() for _ in ["drop", "create", "select"]):
            msg = "Where clause cannot include substatements"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)

        params = {}
        for k, v in self.matcher.csvpath.variables.items():
            token = f"@{k}"
            if token not in w:
                continue

            if isinstance(v, (list, tuple, set)):
                # Expand list into numbered placeholders: @var -> :var_0, :var_1, ...
                if not v:
                    # Empty list — produce a always-false clause to avoid SQL errors
                    placeholders = "NULL"
                else:
                    keys = [f"var_{i}" for i in range(len(v))]
                    for key, item in zip(keys, v):
                        params[key] = item
                    placeholders = ", ".join(f":{k}" for k in keys)
                w = w.replace(token, f"({placeholders})")
            else:
                # Scalar: @apple -> :apple
                placeholder = f"var_{k}"
                params[placeholder] = v
                w = w.replace(token, f":{placeholder}")

        return w, params
