from ..reference_3 import Reference3
from .function_3 import Function3


class Idchain3(Function3):
    #
    # the first metadata-FIELD function -- addresses one specific error
    # entry (or entries) within errors.json by the match component that
    # produced it, e.g. ":errors(:idchain('add[0]string[2]'))". Despite
    # sounding like it walks a live Matcher parse tree, it does not --
    # Error.to_json()'s own "source" field already holds exactly this
    # chain string (Matchable.my_chain, generated once, at the moment
    # the error was recorded), so this is a plain field-match filter,
    # the same idea as :type() filtering manifest entries by their own
    # "type" field, confirmed directly against the real Error class
    # rather than assumed. Only meaningful nested inside :errors() (see
    # Errors3.ARG_TYPES) -- not usable on its own or in any other slot.
    # ROLE is VALUE, matching every other accessor/field function built
    # so far: it does not narrow/select anything itself, it is a value
    # fed to :errors()'s own filtering logic.
    #
    NAME = "idchain"
    SUMMARY = (
        "Addresses one specific match component within a well-known "
        "file's own entries (e.g. errors.json) by its idchain string -- "
        "only meaningful nested inside :errors()."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.RESULTS,)
    ARG_TYPES = (str,)
    ARG_REQUIRED = True
