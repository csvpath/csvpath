from ...reference_3 import Reference3
from ..function_3 import Function3


class OnArrival3(Function3):
    #
    # first of the definition.json-backed field accessors -- SOURCE is
    # "definition", not "manifest", so a finder resolves this against
    # the enclosing named-file's definition.json config instead of a
    # manifest entry, and does not need result.uuid to do it:
    # definition.json is not versioned (see Definition3), so there is
    # only ever one on_arrival value regardless of which version a
    # reference otherwise narrowed to.
    #
    NAME = "on_arrival"
    SUMMARY = (
        "The on_arrival configuration for the resolved named-file -- "
        "which named-paths group and run method to trigger automatically "
        "when a new version arrives, read from definition.json. None if "
        "the named-file was never configured for this."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "definition"
    KEY = {
        Reference3.FILES: "on_arrival",
    }
    #
    # BOTH positions -- bare, name_one (settled 2026-08-12, David: an
    # arrival activation lives in the named-file's own definition.json,
    # it "doesn't go to the version level" -- matches :definition()
    # itself, see FilesReferenceFinder3._bare_definition_field_call()),
    # AND the ordinary name_three field-accessor position beside a
    # matched pointer (e.g. ":name('orders.csv').:first():on_arrival()")
    # -- confirmed via existing passing tests, both give the identical
    # answer regardless of which version is selected, since SOURCE ==
    # "definition" means _extract_data() never reads result.uuid for
    # this function either way.
    #
    POSITIONS = {Reference3.FILES: (Reference3.NAME_ONE, Reference3.NAME_THREE)}
