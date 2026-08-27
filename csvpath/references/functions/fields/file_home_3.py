from ...reference_3 import Reference3
from ..function_3 import Function3


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
    ARG_TYPES = ()
    ARG_REQUIRED = False
    SOURCE = "manifest"
    KEY = {
        Reference3.FILES: "file_home",
    }
    POSITIONS = {Reference3.FILES: (Reference3.NAME_THREE,)}
