class ReferenceException3(Exception):
    """raised for semantic problems with a parsed references-v3
    reference that the grammar deliberately doesn't enforce -- e.g. a
    missing name_three where the reference's datatype requires one. see
    reference_grammar_3.py's module docstring for why that check is
    deferred out of the grammar."""


class ReferenceRuntimeException3(ReferenceException3):
    """raised for reference problems that can only be detected once a
    reference is actually being resolved -- never by Function3.
    check_valid()'s own parse-time structural check, which runs before
    any @variable is necessarily even registered. Mirrors the matching
    language's own static-vs-runtime split (csvpath/matching/functions/
    args.py: Args.validate() raises ChildrenException for a syntax
    problem, Args.matches() raises MatchException for a data problem
    found while actually matching a line) -- added 2026-08-27, David:
    "we just use a different exception that indicates a 'runtime'
    error, as opposed to a static analysis error." Deliberately does
    NOT bring over that split's other half, the error_manager/
    do_i_raise() collect-vs-raise machinery -- references v3 has never
    had that, every ReferenceException3 (this one included) has always
    raised immediately, and nothing about the exception-class split
    requires copying that too.

    A subclass of ReferenceException3, not a sibling -- every existing
    broad `except ReferenceException3`/`pytest.raises(ReferenceException3)`
    keeps working completely unchanged; catch this narrower type
    specifically when the static-vs-runtime distinction itself matters.

    Two cases today, both in ReferenceFinder3: an `@variable` used in a
    reference but never registered via set_variable()/set_variables()
    (_resolve_value()), and a variable that WAS registered but resolved
    to a value of the wrong type for the argument slot it was given in
    (_resolve_arg() -- Function3.check_valid() cannot catch this itself,
    since ARG_TYPES was widened to accept Variable3 unconditionally
    precisely because its eventual resolved value could be anything)."""
