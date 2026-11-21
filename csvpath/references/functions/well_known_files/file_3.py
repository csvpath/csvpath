from ...reference_3 import Reference3
from ..function_3 import Function3
from .bare_name_utility import BareNameUtility as baut


class File3(Function3):
    #
    # the arbitrary-named counterpart to the other well-known-file
    # functions -- resolves to the raw bytes of a user-named output file
    # (e.g. a custom parquet/jinja/text output) sitting in the same run
    # instance directory as errors.json/vars.json/etc, per "creating
    # references v3.txt"'s resolve table ("...or a user-named parquet,
    # jinja, or text output file... using a function like
    # :file('orders.parquet')"). Genuinely optional, same as Data3/
    # Unmatched3 -- resolves to None rather than raising when absent.
    #
    NAME = "file"
    SUMMARY = (
        "The raw bytes of a user-named output file (e.g. a custom "
        "parquet/jinja/text output) in a run instance's own directory. "
        "None if no such file was written."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- a whole-resource read, not a
    # single field, see Function3.RESOLVES_AS's own docstring for
    # why this class needs one (added 2026-08-28).
    RESOLVES_AS = Reference3.METADATA_FILE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}

    def check_valid(self) -> None:
        super().check_valid()
        # bare filename only -- no path traversal outside the run
        # instance's own directory (BareNameUtility). An @variable or
        # "{...}" arg is checked once it resolves, in check_resolved().
        if isinstance(self._arg, str):
            baut.check(function_name=self.NAME, name=self._arg)

    def check_resolved(self) -> None:
        # ':file(@f)' with '../../x.txt' passed until 2026-11-21: only a
        # literal was checked (reviewer on #790)
        baut.check(function_name=self.NAME, name=self.arg)
