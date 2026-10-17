from ...reference_3 import Reference3
from ...reference_exceptions_3 import ReferenceException3
from ..filters.predicate_function_3 import PredicateFunction3
from ..function_3 import Function3


class Definition3(Function3):
    #
    # the second metadata-file function, mirroring Manifest3 exactly --
    # points at the enclosing named-file/named-paths group's own
    # definition.json (its stored configuration: sources, on_arrival
    # behavior, scripts, webhooks, etc -- see NamedFileDescriber/
    # NamedPathsDescriber, both JSON_FILE = "definition.json", stored at
    # the same home directory as manifest.json). Unlike manifest.json,
    # definition.json is genuinely optional -- a named-file/group that
    # was never explicitly configured has no definition.json on disk at
    # all, and it is not currently versioned (always the single current
    # definition, regardless of which version of the file/group you are
    # looking at -- versioning description files is a real future need,
    # just not yet prioritized). Named-results has no definition.json
    # equivalent, so this is FILES/CSVPATHS only, unlike Manifest3.
    #
    # ROLE is VALUE, not POINTER, for the same reason Manifest3's own
    # ROLE was corrected: :definition() never narrows or selects
    # anything, even bare -- it only ever accesses what root_major
    # already fully identifies. This one was missed in that earlier fix
    # (only Manifest3 got corrected) -- caught while re-checking every
    # existing "accessor" function's role for consistency ahead of
    # adding the well-known-file functions below, which share the
    # exact same trait.
    #
    # ARG_TYPES widened to accept a nested Function3 -- added 2026-10-17,
    # the generic predicate-argument filtering mechanism (deferred-work
    # bucket list's own "Predicate-argument field accessors" entry),
    # closing its own motivating worked example:
    # "$*.files.:home():definition(:on_arrival(:not_none()))" -- "which
    # named-files have on_arrival set." check_valid() below cross-
    # validates the nested function rather than listing every possible
    # definition-sourced field accessor (:on_arrival()/:sources()/etc)
    # by name here -- any current or future one works for free. This is
    # the FILTER half of "position decides meaning" (David, 2026-08-21),
    # one level up from :errors(:idchain(...))'s own filter: there, the
    # predicate narrows WHICH ARRAY ENTRIES of one already-selected
    # resource come back; here, it narrows WHICH NAMED-FILES survive
    # '*' traversal in the first place (FilesReferenceFinder3's own
    # _query_star_traversal() does the actual filtering, using this
    # class's own validated nested call -- see
    # _matches_definition_field_predicate()).
    #
    NAME = "definition"
    SUMMARY = (
        "Points at the whole definition.json for the enclosing named-file "
        "or named-paths group -- its stored configuration (sources, "
        "on_arrival behavior, scripts, webhooks, etc). Not currently "
        "versioned; resolves to None if the group/file was never "
        "explicitly configured (no definition.json written yet). May take "
        "a nested, predicate-argued definition field accessor (e.g. "
        ":on_arrival(:not_none())) during '*' traversal, which filters "
        "which named-files survive rather than reading a value."
    )
    ROLE = Function3.VALUE
    # metadata_kind() override -- a whole-resource read, not a
    # single field, see Function3.RESOLVES_AS's own docstring for
    # why this class needs one (added 2026-08-28).
    RESOLVES_AS = Reference3.METADATA_FILE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = (Function3,)
    ARG_REQUIRED = False
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_ONE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
    }

    def check_valid(self) -> None:
        super().check_valid()
        if self._arg is None:
            return
        if self._arg.SOURCE != "definition":
            raise ReferenceException3(
                ":definition() only accepts a definition-sourced field "
                "accessor as its own nested argument (SOURCE == "
                f"'definition'), not :{self._arg.NAME}()."
            )
        if not isinstance(self._arg.arg, PredicateFunction3):
            raise ReferenceException3(
                ":definition()'s own nested field accessor must itself "
                "carry a predicate argument (e.g. :not_none()) -- this is "
                "the only nested-argument shape :definition() currently "
                "supports."
            )
