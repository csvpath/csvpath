from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class RunHome3(Function3):
    #
    # split out of :home() (2026-08-26, see :home()'s own docstring and
    # the "split :home()'s field-read job" bucket-list entry) -- reads
    # the "run_home" key off whatever run a pointer already selected.
    # Run scope only -- deliberately does NOT also serve instance scope
    # the way :home() used to (see :instance_home() for that half); a
    # name_one-riding field accessor here is dispatched via
    # ResultsReferenceFinder3._extract_data()'s own run_field_call
    # branch, which always reads Function3.KEY[Reference3.RESULTS] and
    # explicitly rejects a name_three alongside it, so this only needs
    # (and only declares) that one key.
    #
    NAME = "run_home"
    SUMMARY = "The path to the resolved run's own home directory."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    # and :has_value()/:does_not_have_value(): "Every field matches exactly
    # one of the two" (NRE); other predicates on a string are not ruled
    ARG_TYPES = (str, HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.RESULTS: "run_home",
    }
    POSITIONS = {Reference3.RESULTS: (Reference3.NAME_ONE,)}
