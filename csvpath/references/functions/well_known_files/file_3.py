from ...reference_3 import Reference3
from ...reference_exceptions_3 import ReferenceException3
from ..function_3 import Function3


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
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True

    def check_valid(self) -> None:
        super().check_valid()
        # bare filename only -- no path traversal outside the run
        # instance's own directory. Skips an InterpolatedString3 arg
        # (its actual text is not known until evaluation, which is
        # deferred -- see InterpolatedString3's own docstring).
        if isinstance(self._arg, str) and (
            "/" in self._arg or "\\" in self._arg or ".." in self._arg
        ):
            raise ReferenceException3(
                f":{self.NAME}() argument must be a bare filename, not a "
                f"path: {self._arg!r}"
            )
