from datetime import datetime
from typing import Union, Optional, List, Any
from dataclasses import dataclass

from lark import Lark, Transformer, v_args, Tree, Token

#
# open questions:
#  - should we support # in names one and three?
#  - if we support # how do tokens work?
#  - non_local_reference type "reference" is set to "variable" in the transformer. is this long-term?
#  - should we limit tokens by type? e.g. csvpaths type takes :from and :to but not :today and :yesterday
#

REFERENCE_GRAMMAR = r"""
    ?start: reference

    reference: non_local_reference | local_reference

    non_local_reference: file_reference
                       | results_reference
                       | csvpaths_reference
                       | reference_reference

    local_reference: csvpath_reference
                   | headers_reference
                   | variables_reference
                   | metadata_reference

    file_reference:      "$" root_name non_local_type name_one ("." name_two)?
    csvpaths_reference:  "$" root_name non_local_type name_one ("." name_two)?
    results_reference:   "$" root_name non_local_type name_one ("." name_two)?
    reference_reference: "$" root_name non_local_type name_one ("." name_two)?
    csvpath_reference:   "$."    local_type           local_name_one ("." local_name_two)?
    variables_reference: "$."    local_type           local_name_one ("." local_name_two)?
    metadata_reference:  "$."    local_type           local_name_one ("." local_name_two)?
    headers_reference:   "$."    local_type           header_name

    non_local_type: files_type
                  | csvpaths_type
                  | results_type
                  | reference_type

    local_type: csvpath_type
              | headers_type
              | variables_type
              | metadata_type

    files_type: ".files."
    csvpaths_type: ".csvpaths."
    results_type: ".results."
    reference_type: ".variables."
    csvpath_type: "csvpath."
    headers_type: "headers."
    variables_type: "variables."
    metadata_type: "metadata."

    name_one: fingerprint
            | path? tokens?
            | DATETIME? tokens?

    name_two: path? tokens?
            | DATETIME? tokens?

    local_name_one: path? tokens?
                  | DATETIME? tokens?

    local_name_two: path? tokens?
                  | DATETIME? tokens?

    fingerprint: HASH

    header_name: "'"? IDENTIFIER "'"? | INTEGER

    tokens: token (token)?
    token: yesterday
          | today
          | last
          | first
          | before
          | after
          | ffrom
          | to
          | all
          | index
          | point
          | data
          | unmatched
          | preceding

    yesterday: ":yesterday"
    today: ":today"
    last: ":last"
    first: ":first"
    before: ":before"
    after: ":after"
    ffrom: ":from"
    to: ":to"
    all: ":all"
    data: ":data"
    unmatched: ":unmatched"
    preceding: ":preceding"
    index: ":" INTEGER
    point: ":" DATETIME

    // Basic components
    root_name: IDENTIFIER
    path: PATH_SEGMENT ("/" PATH_SEGMENT?)*

    // Terminals - PATH_SEGMENT now excludes dots to enforce two-dot limit
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_# \-]*/
    PATH_SEGMENT: /[a-zA-Z0-9_\- #]+/

    HASH: /[abcdef0-9]{64}/

    INTEGER: /\d+/
    DATETIME: /\d{4}-/
            | /\d{4}-\d{2}/
            | /\d{4}-\d{2}-\d{2}/
            | /\d{4}-\d{2}-\d{2}_\d{2}-/
            | /\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-/
            | /\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}/

    %import common.WS
    %ignore WS
"""


# =====================================


class ReferenceTransformer(Transformer):
    """Transformer to convert parse tree into structured data"""

    # ref: "ReferenceParser" disallowed by flake
    def __init__(self, ref) -> None:
        self.ref = ref

    def root_name(self, items):
        name = None
        if items and len(items) > 0 and items[0]:
            name = items[0].value
            name = str(name)
            self.ref.root_name = name
        return name

    def name_one(self, items):
        name, tokens = self._name_and_tokens(items)
        self.ref.name_one = name
        self.ref.name_one_tokens = tokens

    #
    # name two becomes name three after we're done parsing because
    # names one and two (in the query parser) are both potentially
    # split in two around a '#' to make names one through four. the
    # rest of CsvPath uses ReferenceParser as the reference class
    # and so knows name_one, name_two, name_three, and name_four,
    # with focus being on names one and three.
    #
    def name_two(self, items):
        name, tokens = self._name_and_tokens(items)
        self.ref.name_three = name
        self.ref.name_three_tokens = tokens

    def local_name_one(self, items):
        name, tokens = self._name_and_tokens(items)
        self.ref.name_one = name
        self.ref.name_one_tokens = tokens

    def local_name_two(self, items):
        name, tokens = self._name_and_tokens(items)
        self.ref.name_three = name
        self.ref.name_three_tokens = tokens

    def _name_and_tokens(self, items) -> tuple[str, list]:
        if not items or len(items) == 0:
            return
        data = None
        tokens = []
        if isinstance(items[0], str):
            data = items[0]
            if data and data.startswith(":"):
                tokens.append(data[1:])
            if len(items) > 1:
                tokens = tokens + items[1]
        elif isinstance(items[0], list):
            tokens = items[0]
        return (data, tokens)

    def path(self, items):
        p = "/".join(str(item.value) for item in items)
        return p

    def fingerprint(self, items):
        #
        # need to set ref flag to say name_two not allowed because
        # fingerprint. otherwise we won't have that info later on
        # because name and fingerprint are both just strings.
        #
        f = None
        if items is not None and len(items) > 0:
            f = items[0].value
            self.ref.name_one = f
            self.ref.name_one_is_fingerprint = True
        return str(f)

    def local_type(self, items):
        return self._type(items)

    def non_local_type(self, items):
        return self._type(items)

    def _type(self, items):
        t = None
        if items and len(items) > 0:
            # change from e.g. files_type to files
            t = items[0].data
            t = t.value
            t = t[0 : t.find("_")]
            if t == "reference":
                t = "variables"
            self.ref.datatype = t
        return str(t)

    def INTEGER(self, item) -> int:
        return int(item)

    def DATETIME(self, item) -> str:
        return f":{item}"

    # ============================
    # tokens
    #

    def index(self, item) -> int:
        return f":{item[0]}"

    def point(self, item) -> int:
        return f"{item[0]}"

    def today(self, item) -> int:
        return ":today"

    def yesterday(self, item) -> int:
        return ":yesterday"

    def all(self, item) -> int:
        return ":all"

    def first(self, item) -> int:
        return ":first"

    def last(self, item) -> int:
        return ":last"

    def before(self, item) -> int:
        return ":before"

    def after(self, item) -> int:
        return ":after"

    def ffrom(self, item) -> int:
        return ":from"

    def to(self, item) -> int:
        return ":to"

    def data(self, item) -> int:
        return ":data"

    def unmatched(self, item) -> int:
        return ":unmatched"

    def preceding(self, item) -> int:
        return ":preceding"

    def token(self, item) -> list:
        return item[0] if item and isinstance(item, list) else item

    def tokens(self, items) -> list:
        if isinstance(items, list):
            return items
        return items.children


# =====================================


class QueryParser:
    # ref: "ReferenceParser" disallowed by flake
    def __init__(self, ref):
        self.parser = Lark(REFERENCE_GRAMMAR, parser="earley")
        self.ref = ref

    def parse(self, query: str):
        """Parse a CsvPath query string and return structured representation"""
        if self.ref is None:
            raise RuntimeError("A reference object must be available for parsing")
        try:
            result = self.parser.parse(query)
            ReferenceTransformer(self.ref).transform(result)
            return self.ref
        except Exception as e:
            # from csvpath.util.log_utility import LogUtility
            # LogUtility.log_brief_trace()
            raise ValueError(f"Failed to parse query '{query}': {e}")

    def validate_query(self, query: str) -> bool:
        try:
            self.parse(query)
            return True
        except Exception:
            return False
