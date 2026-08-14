from ...reference_3 import Reference3
from ..function_3 import Function3


class Path3(Function3):
    #
    # settled 2026-08-07 alongside the $*.files.:manifest() question --
    # see references_notes/notes/manifest_field_functions_proposal.md's
    # "Entity resolution and pooling" section, Rule 2. Wraps any whole-
    # resource content function (:manifest(), :definition(), and
    # eventually :errors()/:vars()/etc. for results) and returns the
    # filesystem path to that resource instead of its content -- one
    # wrapping function instead of a _path()-suffixed sibling per well-
    # known file, so any future well-known file gets a path accessor for
    # free. Exempt from the single-entity content-pooling rule that
    # governs its own arg: a path is a cheap scalar, not a raw structure,
    # so :path(...) calls are always poolable across "*"/unresolved
    # versions.
    #
    # ARG_TYPES is (Function3,) rather than empty -- by the time
    # ReferenceFunctionFactory.build() constructs this, a nested
    # FunctionCall3 arg has already been compiled into a real Function3
    # instance (build() recurses first), so self.arg here is always
    # already the resolved inner function, e.g. a Manifest3() instance,
    # not the raw parsed shape.
    #
    # batch 1 (FILES/CSVPATHS) only wraps :manifest()/:definition() --
    # both are the only whole-resource functions available at either
    # datatype today. Wrapping a results-only well-known-file function
    # (:errors(), etc.) or a field accessor (:uuid(), etc. -- which has
    # no separate "path" of its own to give) is not yet supported; see
    # each finder's own _resolve_path_call().
    #
    NAME = "path"
    SUMMARY = (
        "The filesystem path to the resource a wrapped whole-resource "
        "function (e.g. :manifest(), :definition()) points at, instead "
        "of that resource's content. Always poolable across '*' and "
        "unresolved versions/runs, unlike the function it wraps."
    )
    ROLE = Function3.VALUE
    DATATYPES = (Reference3.FILES, Reference3.CSVPATHS)
    ARG_TYPES = (Function3,)
    ARG_REQUIRED = True
    POSITIONS = {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE,),
    }
