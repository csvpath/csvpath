from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.count_3 import Count3
from ..filters.idchain_3 import Idchain3
from ..filters.message_3 import Message3


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
    # idchain. Added 2026-10-17: a nested :message(...) argument is the
    # direct sibling of :idchain(...) -- normative_reference_examples.txt
    # places them right next to each other, filtering by the entry's
    # own "message" field instead of "source" -- same mechanism, same
    # zero-matches-is-legitimate treatment, see Message3.
    #
    # POSITION DECIDES MEANING (David, 2026-08-21) -- this is the FILTER
    # half of a two-part rule, not the whole rule. A predicate NESTED as
    # this function's own argument (:idchain(...), matching a field
    # WITHIN errors.json's own array entries) narrows which entries of
    # errors.json's content come back -- the content itself is always
    # returned, just possibly narrowed. This is settled, shipped
    # behavior for :idchain()/:message() and must not change to an
    # all-or-nothing gate for THEM.
    #
    # The GATE half, shipped 2026-10-17, is a *separate* :idchain(...)
    # (currently only :idchain(), see _apply_errors_gate's own docstring)
    # CHAINED AFTER :errors() in the same func_chain, not nested inside
    # it -- e.g. ":errors():idchain(:not_none())". There, the gate's own
    # predicate decides whether :errors()'s WHOLE, unfiltered result is
    # returned at all -- not which entries survive. Chained position,
    # not nesting, is what signals "gate the function before me" instead
    # of "filter my own content."
    #
    # A third, EXPLICIT exception, also shipped 2026-10-17 -- a nested
    # :count(...) argument (e.g. ":errors(:count(:above(10)))",
    # normative examples 489-491). Despite being NESTED (normally the
    # FILTER position), :count() cannot filter entries at all -- it is
    # an aggregate over the WHOLE array, with no per-entry meaning -- so
    # it acts as a GATE instead, same all-or-nothing treatment as the
    # chained case above, just reached from the nested position. See
    # Count3's own docstring. Not a loophole in the FILTER/GATE rule --
    # an aggregate function nested here was never a case the rule's
    # original two positions anticipated either way.
    #
    NAME = "errors"
    SUMMARY = (
        "The parsed contents of a run instance's errors.json -- the list "
        "of errors that csvpath statement's execution recorded. Optionally "
        "filtered to entries matching a nested :idchain(...) or "
        ":message(...) argument, or gated all-or-nothing by a nested "
        ":count(...) argument."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- a whole-resource read, not a
    # single field, see Function3.RESOLVES_AS's own docstring for
    # why this class needs one (added 2026-08-28).
    RESOLVES_AS = Reference3.METADATA_FILE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (Idchain3, Message3, Count3)
    ARG_REQUIRED = False
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_THREE,)}
