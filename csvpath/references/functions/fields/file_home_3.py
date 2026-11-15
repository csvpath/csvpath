from ...reference_3 import Reference3
from ..function_3 import Function3
from ..filters.does_not_have_value_3 import DoesNotHaveValue3
from ..filters.has_value_3 import HasValue3


class FileHome3(Function3):
    #
    # split out of :home() (2026-08-26, see :home()'s own docstring and
    # the "split :home()'s field-read job" bucket-list entry) -- reads
    # the "file_home" key off whatever named-file version a pointer
    # already selected. FILES' own half of what used to be :home()'s
    # single, cross-datatype field-read job, now under an obviously-
    # named, single-datatype function instead of one name polymorphic
    # across four different manifest keys.
    #
    NAME = "file_home"
    SUMMARY = "The path to the resolved named-file version's own home directory."
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES,)
    # an argument filters (compendium 6.40: "An argument to a field accessor
    # filters too"); it refused one until 2026-11-15 (RC triage A6/H)
    # and :has_value()/:does_not_have_value(): "Every field matches exactly
    # one of the two" (NRE); other predicates on a string are not ruled
    ARG_TYPES = (str, HasValue3, DoesNotHaveValue3)
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "file_home",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
