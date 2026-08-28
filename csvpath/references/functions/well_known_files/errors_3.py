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
    # POSITION DECIDES MEANING (David, 2026-08-21) -- this is the FILTER
    # half of a two-part rule, not the whole rule. A predicate NESTED as
    # this function's own argument (:idchain(...), matching a field
    # WITHIN errors.json's own array entries) narrows which entries of
    # errors.json's content come back -- the content itself is always
    # returned, just possibly narrowed. This is settled, shipped
    # behavior and must not change to an all-or-nothing gate.
    #
    # The GATE half (NOT YET BUILT -- see deferred_work_bucket_list.md)
    # is a *separate* function CHAINED AFTER :errors() in the same
    # func_chain, not nested inside it -- e.g. a hypothetical
    # ":errors():error_count(:above(5))". There, :error_count() reads a
    # field that has nothing to do with errors.json's own array (it is
    # a sibling field on the run instance's manifest.json), and its own
    # nested predicate (:above(5)) decides whether :errors()'s WHOLE
    # result is returned AT ALL -- not which entries survive. Chained
    # position, not nesting, is what signals "gate the function before
    # me" instead of "filter my own content."
    #
    NAME = "errors"
    SUMMARY = (
        "The parsed contents of a run instance's errors.json -- the list "
        "of errors that csvpath statement's execution recorded. Optionally "
        "filtered to entries matching a nested :idchain(...) argument."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- a whole-resource read, not a
    # single field, see Function3.RESOLVES_AS's own docstring for
    # why this class needs one (added 2026-08-28).
    RESOLVES_AS = Reference3.METADATA_FILE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (Idchain3,)
    ARG_REQUIRED = False
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
