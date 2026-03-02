import pyarrow as pa
from pyarrow import Schema, Field

from csvpath.matching.functions.types.string import String
from csvpath.matching.functions.types.decimal import Decimal
from csvpath.matching.functions.types.datef import Date
from csvpath.matching.functions.types.boolean import Boolean
from csvpath.matching.functions.types.nonef import Nonef
from csvpath.matching.functions.types.blank import Blank
from csvpath.matching.functions.types.url import Url
from csvpath.matching.functions.types.email import Email
from csvpath.matching.functions.types.wildcard import Wildcard
from csvpath.matching.productions import Term

from csvpath.matching.functions.function import Function
from csvpath.matching.util.exceptions import ChildrenException


class ParquetUtility:
    @classmethod
    def line_to_schema(cls, line: Function) -> Schema:
        if line.name not in ["line", "parquet"]:
            raise ChildrenException(f"Cannot create a schema from a {line.name}")
        return pa.schema(cls.columns(line))

    @classmethod
    def columns(cls, line: Function) -> Schema:
        if line.name not in ["line", "parquet"]:
            raise ChildrenException(f"Cannot create a schema from a {line.name}")
        columns = []
        for i, s in enumerate(line.siblings()):
            ttypes = cls.to_type(s)
            if len(ttypes) == 1:
                #
                # find name in name qualifer, or
                #   value_one, or
                #   c{i}
                #
                cname = s.first_non_term_qualifier(s._value_one(skip=None))
                if cname is None or str(cname).strip() == "":
                    cname = f"c{i}"
                _ = (cname, ttypes[0])
                columns.append(_)
            else:
                for j, _ in enumerate(ttypes):
                    n = i + j
                    t = (f"c{n}", ttypes[j])
                    columns.append(t)
        return columns

    @classmethod
    def to_type(cls, s: Function) -> list:
        if s is None:
            raise ValueError("Function cannot be None")
        if isinstance(s, String):
            return [pa.string()]
        elif isinstance(s, Decimal):
            if s.name == "decimal":
                return [pa.float64()]
            elif s.name == "integer":
                return [pa.int64()]
            else:
                raise ChildrenException(f"Unknown number type: {s.name}")
        elif isinstance(s, Date):
            if s.name == "date":
                [pa.date64()]
            elif s.name == "datetime":
                [pa.timestamp("us")]
            else:
                raise ChildrenException(f"Unknown type of Date object: {s.name}")
        elif isinstance(s, Blank):
            return [pa.string()]
        elif isinstance(s, Boolean):
            return [pa.bool_()]
        elif isinstance(s, Nonef):
            return [pa.null()]
        elif isinstance(s, Url):
            return [pa.string()]
        elif isinstance(s, Email):
            return [pa.string()]
        elif isinstance(s, Wildcard):
            c = s._child_one()
            if not isinstance(c, Term):
                raise ChildrenException(
                    "Wildcard child must be a Term with an int value"
                )
            i = s._value_one(skip=None)
            if isinstance(i, int):
                ts = []
                for _ in range(0, i):
                    ts.append(pa.string())
                return ts
            else:
                raise ChildrenException(f"Cannot have a wildcard with cardinality: {i}")
        else:
            raise ChildrenException(f"Unknown type function: {s}")
