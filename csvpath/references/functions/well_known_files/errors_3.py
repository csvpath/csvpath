from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.idchain_3 import Idchain3


class Errors3(Function3):
    #
    # the first of the results-only well-known instance-level file
    # functions -- resolves to the parsed JSON contents of errors.json,
    # the list of error dicts a csvpath statement's own run instance
    # wrote (ResultSerializer._save -- always written, even if empty).
    # Rides alongside the identity/:all() selector already occupying
    # name_three (e.g. "$acme.results.customers/2025:first().invoices
    # :errors()"), it does not select the instance itself -- see
    # ResultsReferenceFinder3._name_three_selector.
    #
    # optionally takes a nested :idchain(...) argument (e.g.
    # ":errors(:idchain('add[0]string[2]'))") that filters the parsed
    # list down to entries whose own "source" field matches -- see
    # Idchain3 and ResultsReferenceFinder3._read_accessor. Zero matches
    # is a legitimate, non-error result (an empty list), not None --
    # the file itself was found and read, it just has no entry for that
    # idchain.
    #
    NAME = "errors"
    SUMMARY = (
        "The parsed contents of a run instance's errors.json -- the list "
        "of errors that csvpath statement's execution recorded. Optionally "
        "filtered to entries matching a nested :idchain(...) argument."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (Idchain3,)
    ARG_REQUIRED = False
