import logging

from lark.exceptions import VisitError

from .reference_3 import Reference3
from .reference_grammar_3 import QueryParser3
from .reference_transformer_3 import Reference3Transformer


#
# ReferenceParser3 wraps a references-v3 query string: parses it (via
# QueryParser3 + Reference3Transformer) into a Reference3 object graph
# (reference_3.py) and holds the CsvPaths context a ReferenceFinder3
# (not yet built) will need to actually run the query.
#
# workflow (see "creating references v3.txt"):
#   ref = ReferenceParser3(string="$acme.files.*.:last()", csvpaths=paths)
#   finder = FilesReferenceFinder3(ref)
#   results = finder.query()
#   data = finder.resolve()
#
class ReferenceParser3:
    FILES = Reference3.FILES
    CSVPATHS = Reference3.CSVPATHS
    RESULTS = Reference3.RESULTS

    _query_parser: QueryParser3 | None = None

    @classmethod
    def _get_query_parser(cls) -> QueryParser3:
        # built once and shared -- QueryParser3() compiles the LALR
        # grammar, no need to redo that on every ReferenceParser3 built.
        if cls._query_parser is None:
            cls._query_parser = QueryParser3()
        return cls._query_parser

    def __init__(self, *, string: str, csvpaths) -> None:
        if not string:
            raise ValueError("ReferenceParser3 string cannot be None or empty")
        if csvpaths is None:
            raise ValueError("ReferenceParser3 csvpaths cannot be None")
        self._csvpaths = csvpaths
        self._reference: str = string
        self._parsed: Reference3 | None = None
        self.parse(string)

    def __str__(self) -> str:
        return f"ReferenceParser3(reference={self._reference!r})"

    @property
    def csvpaths(self):
        return self._csvpaths

    @csvpaths.setter
    def csvpaths(self, csvpaths) -> None:
        self._csvpaths = csvpaths

    @property
    def reference(self) -> str:
        return self._reference

    @property
    def parsed(self) -> Reference3:
        return self._parsed

    @property
    def ref_string(self) -> str:
        return str(self._parsed)

    @property
    def root_major(self):
        return self._parsed.root_major

    @property
    def datatype(self) -> str:
        return self._parsed.datatype

    @property
    def name_one(self):
        return self._parsed.name_one

    @property
    def name_two(self) -> str | None:
        return self._parsed.name_one.name_two

    @property
    def name_three(self):
        return self._parsed.name_three

    def parse(self, string: str) -> None:
        if not string:
            raise ValueError("ReferenceParser3 string cannot be None or empty")
        logger = logging.getLogger(self.__class__.__name__)
        try:
            tree = self._get_query_parser().parse(string)
            self._parsed = Reference3Transformer().transform(tree)
            self._parsed.check_valid()
        except VisitError as e:
            # any exception raised from inside a Transformer rule
            # method (e.g. STRING's interpolation parsing rejecting an
            # unescaped brace) arrives here wrapped in lark's own
            # VisitError -- unwrap it so callers see the real
            # exception (typically ReferenceException3) rather than a
            # lark-internal type. Same reasoning as why
            # Reference3.check_valid() is called outside transform()'s
            # own call stack in the first place.
            logger.error("Failed to parse reference '%s': %s", string, e.orig_exc)
            raise e.orig_exc from e
        except Exception as e:
            logger.error("Failed to parse reference '%s': %s", string, e)
            raise
        self._reference = string
